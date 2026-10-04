#!/usr/bin/env python3
"""Render review previews from exported maps: albedo, lit and hillshade views, tiled sheets, 1:1 crops at picked sites.

Usage:
    python previews.py checks/classic.json [checks/weathered.json ...] --out DIR [--sites N] [--no-shadows]

Scale, maps and regions come from each checks.json through matcheck.py (same folder). Writes <out>/<variant>_*.png,
compare_front.png and compare_crop_raking.png when given two or more configs, and <out>/views_index.md, which says
what every file shows and at what scale. Documented in references/checks.md, "Previews".
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matcheck as mc  # noqa: E402

# light directions: x right, y up the image, z toward the viewer (normalised before use)
LIGHTS = {
    "front": (-0.3, 0.35, 0.89),
    "raking_a": (-0.75, 0.55, 0.36),  # upper-left, az 143.7 deg, el 21.2 deg
    "raking_b": (0.75, -0.55, 0.36),  # lower-right: opposite azimuth, same elevation
}
CROP_PX = 512
ZOOM_PX = 256
HILL_GREY_SRGB = 0.5
PALETTE = [(0.27, 0.55, 1.0), (1.0, 0.4, 0.1), (0.25, 0.9, 0.35), (0.95, 0.25, 0.8), (1.0, 0.85, 0.1), (0.1, 0.9, 0.9)]
PALETTE_NAMES = ["blue", "orange", "green", "magenta", "yellow", "cyan"]

# ----------------------------------------------------------------------------- image helpers


def lin_to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    lo = c <= 0.0031308
    out = np.power(c, 1 / 2.4)  # same values as np.where(lo, 12.92 c, 1.055 c^(1/2.4) - 0.055), fewer temporaries
    out *= 1.055
    out -= 0.055
    out[lo] = c[lo] * 12.92
    return out


def to8(a):
    return (np.clip(a, 0.0, 1.0) * 255 + 0.5).astype(np.uint8)


def resize_wrap(a, width, height=None):
    """Lanczos resize of a tileable float image (HxW or HxWxC) to width x height px (default: keep the px aspect),
    reading across the tile border."""
    H, W = a.shape[:2]
    height = height or max(1, int(round(H * width / float(W))))
    pad = int(math.ceil(3.0 * max(W / float(width), H / float(height)))) + 2  # Lanczos-3 support, in source px
    planes = [a] if a.ndim == 2 else [a[..., i] for i in range(a.shape[2])]
    out = []
    for p in planes:
        big = np.pad(np.asarray(p, np.float32), pad, mode="wrap")
        im = Image.fromarray(big).resize((width, height), Image.LANCZOS, box=(pad, pad, pad + W, pad + H))
        out.append(np.asarray(im))
    return out[0] if a.ndim == 2 else np.stack(out, -1)


def crop(a, y0, x0, h, w):
    """h x w window with its top-left at (y0, x0), wrapping around the tile."""
    H, W = a.shape[:2]
    return a[(y0 + np.arange(h)) % H][:, (x0 + np.arange(w)) % W]


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def labelled_row(panels, labels, gap=8, strip=34):
    """uint8 panels side by side, each under a one-line label."""
    f = font(20)
    h = max(p.shape[0] for p in panels)
    w = sum(p.shape[1] for p in panels) + gap * (len(panels) - 1)
    sheet = Image.new("RGB", (w, h + strip), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    x = 0
    for p, text in zip(panels, labels):
        sheet.paste(Image.fromarray(p), (x, strip))
        draw.text((x + 8, 6), text, fill=(235, 235, 235), font=f)
        x += p.shape[1] + gap
    return sheet


# ----------------------------------------------------------------------------- shading


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def light_angles(light):
    L = unit(light)
    return math.degrees(math.atan2(L[1], L[0])) % 360.0, math.degrees(math.asin(L[2]))


def map_normals(rgb, fmt):
    """Normal map RGB -> unit vectors in a y-up frame (DirectX green flipped)."""
    n = rgb.astype(np.float32) * 2.0 - 1.0
    if fmt == "directx":
        n[..., 1] *= -1.0
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
    return n


def height_normals(ctx, hmm):
    """Unit normals of the height field in mm (wrap central differences), y-up frame."""
    gx, gy = mc.grad_mm(ctx, hmm)  # gy runs down the rows
    n = np.stack([-gx, gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def shade(alb, n, rough, ao, light, vis=None, specular=True):
    """views.py shader, linear in and out: Lambert + GGX D-term, 0.08 x AO ambient, a flat face renders at its albedo."""
    L = unit(light).astype(np.float32)
    ndl = np.clip(n @ L, 0.0, 1.0)
    direct = ndl * 0.92 if vis is None else ndl * 0.92 * vis
    col = alb * (direct + 0.08 * ao)[..., None]
    del direct
    if specular:
        half = unit(L + np.array([0.0, 0.0, 1.0])).astype(np.float32)
        ndh = np.clip(n @ half, 0.0, 1.0)
        a2 = np.maximum(rough * rough, 0.02) ** 2
        spec = a2 / (np.pi * (ndh * ndh * (a2 - 1.0) + 1.0) ** 2) * 0.04 * ndl * 0.25
        del ndh
        col += (spec if vis is None else spec * vis)[..., None]
    col /= max(float(L[2]), 0.2)
    return np.clip(col, 0.0, 1.0, out=col)


def normal_agreement(n, hn):
    """Correlation of the normal map's x and y tilt with the height map's (both y-up), on the steepest quarter of the
    height map; nan when the height map is flat. A negative y says normal_format is wrong."""
    s = np.hypot(hn[..., 0], hn[..., 1])
    sel = s > max(float(np.percentile(s, 75)), 1e-4)
    if sel.sum() < 100:
        return float("nan"), float("nan")
    r = [np.corrcoef(n[..., i][sel], hn[..., i][sel])[0, 1] for i in (0, 1)]
    return float(r[0]), float(r[1])


def shadow_vis(hmm, light, mmx, mmy):
    """Light visibility 0-1 from height-field cast shadows: march toward the light (wrap), soft over 1 px of ray rise."""
    L = unit(light)
    horiz = math.hypot(L[0], L[1])
    span = float(hmm.max() - hmm.min())
    if horiz < 1e-6 or span <= 0:
        return None
    dx, dy = L[0] / mmx, -L[1] / mmy  # toward the light in px; rows run down
    k = max(abs(dx), abs(dy))
    sx, sy = dx / k, dy / k  # one px per step along the major axis
    rise = math.hypot(sx * mmx, sy * mmy) * L[2] / horiz  # mm the ray climbs per step
    steps = int(math.ceil(span / rise))  # height range / tan(elevation) / mm per px
    H, W = hmm.shape
    p = steps + 2
    P = np.pad(hmm.astype(np.float32), p, mode="wrap")
    top = np.full((H, W), -np.inf, np.float32)  # highest (terrain - ray) along the ray
    for t in range(1, steps + 1):
        ox, oy = t * sx, t * sy
        ix, iy = math.floor(ox), math.floor(oy)
        fx, fy = ox - ix, oy - iy
        s = None
        for a, b, w in ((0, 0, (1 - fy) * (1 - fx)), (0, 1, (1 - fy) * fx), (1, 0, fy * (1 - fx)), (1, 1, fy * fx)):
            if w > 1e-6:  # bilinear sample; one axis is always whole px
                v = P[p + iy + a:p + iy + a + H, p + ix + b:p + ix + b + W] * np.float32(w)
                s = v if s is None else s + v
        np.maximum(top, s - np.float32(t * rise), out=top)
    return np.clip(1.0 - (top - hmm) / np.float32(rise), 0.0, 1.0)


# ----------------------------------------------------------------------------- masks and crop sites


def optional_gray(ctx, names, default):
    for name in names:
        try:
            return ctx.main.gray(name).astype(np.float32)
        except mc.ConfigError:
            pass
    return np.float32(default)


def layout_masks(ctx, cfg, masks):
    """Masks set by the layout: previews.layout_masks, else masks in mask_invariance checks, else masks matching id == 0."""
    pv = cfg.get("previews", {})
    if "layout_masks" in pv:
        return [m for m in mc.listify(pv["layout_masks"]) if m in masks], "previews.layout_masks"
    found = []
    for c in cfg.get("checks", []):
        if c.get("type") == "mask_invariance":
            m = c.get("mask") or cfg.get("regions", {}).get(c.get("region"), {}).get("mask")
            if m in masks and m not in found:
                found.append(m)
    if found:
        return found, "named in mask_invariance checks"
    if "id" in cfg.get("maps", {}):
        gap = ctx.main.gray("id") < 1e-6
        for m in masks:
            on = masks[m] >= 0.5
            if (on & gap).sum() >= 0.5 * max(1, (on | gap).sum()):
                found.append(m)
        if found:
            return found, "mask matches id == 0 (IoU >= 0.5)"
    return [], "none found (set previews.layout_masks)"


def element_spec(cfg):
    """Spec for per-element luma: previews.elements, else the first per_element luma_mean check, else the id map."""
    pv = cfg.get("previews", {})
    if pv.get("elements"):
        return dict(pv["elements"], metric="luma_mean")
    for c in cfg.get("checks", []):
        if c.get("type") == "per_element" and c.get("metric") == "luma_mean":
            return c
    if "id" in cfg.get("maps", {}):
        return {"metric": "luma_mean"}
    return None


def block_grid(a, b):
    """Mean of each b x b block."""
    H, W = a.shape
    return a.reshape(H // b, b, W // b, b).mean(axis=(1, 3), dtype=np.float64)


def window_mean(grid, wb):
    """Mean of every wb x wb window of a block grid, indexed by the window's top-left block (wrap)."""
    n0, n1 = grid.shape
    g = np.pad(grid, ((0, wb), (0, wb)), mode="wrap")
    c = np.pad(g.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return (c[wb:wb + n0, wb:wb + n1] - c[:n0, wb:wb + n1] - c[wb:wb + n0, :n1] + c[:n0, :n1]) / float(wb * wb)


def free_windows(shape, b, chosen, H, W, size, max_overlap=0.25):
    """Block-grid windows that overlap no chosen window by more than max_overlap (wrap)."""
    return free_at(np.arange(shape[0])[:, None] * b, np.arange(shape[1])[None, :] * b, chosen, H, W, size, max_overlap)


def free_at(yy, xx, chosen, H, W, size, max_overlap=0.25):
    """True where the window with top-left (yy, xx) (broadcast) overlaps no chosen window by more than max_overlap."""
    ok = np.ones(np.broadcast(yy, xx).shape, bool)
    for y0, x0 in chosen:
        dy = np.abs((yy - y0 + H / 2.0) % H - H / 2.0)
        dx = np.abs((xx - x0 + W / 2.0) % W - W / 2.0)
        ok &= np.clip(size - dy, 0, None) * np.clip(size - dx, 0, None) <= max_overlap * size * size
    return ok


def wrap_centre(mask):
    """Centroid (row, col) of a mask on the torus, from circular means."""
    H, W = mask.shape
    ys, xs = np.nonzero(mask)
    cy = math.atan2(np.sin(2 * np.pi * ys / H).mean(), np.cos(2 * np.pi * ys / H).mean()) * H / (2 * np.pi)
    cx = math.atan2(np.sin(2 * np.pi * xs / W).mean(), np.cos(2 * np.pi * xs / W).mean()) * W / (2 * np.pi)
    return int(round(cy)) % H, int(round(cx)) % W


def pick_sites(ctx, cfg, d, n_sites, size):
    """One typical window, then n_sites-1 worst ones: most of each process mask, extreme element luma, low-pass extreme."""
    H, W = d["hmm"].shape
    b = math.gcd(math.gcd(H, W), max(1, size // 32))
    wb = max(1, size // b)
    feats = {"luma": d["luma"], "height": d["hmm"]}
    if np.ndim(d["rough"]):
        feats["roughness"] = d["rough"]
    feats.update(("'%s' coverage" % m, a) for m, a in d["masks"].items())
    z = np.zeros((H // b, W // b))
    for f in feats.values():
        if np.ndim(f) == 2:
            g = window_mean(block_grid(f, b), wb)
            if g.std() > 0:
                z += ((g - g.mean()) / g.std()) ** 2
    i, j = np.unravel_index(int(np.argmin(z)), z.shape)
    sites = [{"name": "typical", "y0": int(i * b), "x0": int(j * b),
              "why": "window closest to the tile means of %s" % ", ".join(feats)}]

    def best(score):
        ok = free_windows(score.shape, b, [(s["y0"], s["x0"]) for s in sites], H, W, size) & np.isfinite(score)
        if not ok.any():
            return None
        s = np.where(ok, score, -np.inf)
        i, j = np.unravel_index(int(np.argmax(s)), s.shape)
        return int(i * b), int(j * b), float(s[i, j])

    def mask_gen(m):
        reg = ctx.region(m)
        cov = window_mean(block_grid(reg.astype(np.float32), b), wb)
        tile = float(reg.mean())

        def gen():
            r = best(cov)
            if r is None or r[2] <= 0:
                return None
            return {"name": "most_" + m, "y0": r[0], "x0": r[1],
                    "why": "most '%s' region in any window: %.1f %% of the window (tile %.2f %%)"
                           % (m, 100 * r[2], 100 * tile)}
        return gen

    def element_gen():
        state = {}

        def gen():
            if "order" not in state:
                spec = element_spec(cfg)
                state["order"] = []
                if spec is None:
                    return None
                lab, n = ctx.elements(spec)
                val, ok = mc.per_element_metric(ctx, spec, lab, n, "luma_mean")
                if ok.sum() < 3:
                    return None
                rel = val / val[ok].mean()
                ids = np.flatnonzero(ok)
                state.update(lab=lab, rel=rel, order=list(ids[np.argsort(-np.abs(rel[ids] - 1.0))]))
            while state["order"]:
                k = state["order"].pop(0)
                m = state["lab"] == k
                ys, xs = np.nonzero(m)
                if any((((ys - s["y0"]) % H < size) & ((xs - s["x0"]) % W < size)).mean() >= 0.9 for s in sites):
                    continue  # already in a crop
                cy, cx = wrap_centre(m)
                y0, x0 = element_window(ys, xs, cy, cx, H, W, size, b, [(s["y0"], s["x0"]) for s in sites])
                if y0 is None:
                    continue
                rel = float(state["rel"][k])
                return {"name": "brightest_element" if rel > 1 else "darkest_element", "y0": y0, "x0": x0,
                        "why": "element centred at (x %d, y %d): luma %.3fx the element mean, the most extreme "
                               "element not already in a crop" % (cx, cy, rel)}
            return None
        return gen

    def lowfreq_gen():
        lum = block_grid(d["luma"], b)
        lp = mc.gaussian_wrap(lum, ctx.px(35.0) / b)
        dev = lp / lp.mean() - 1.0
        score = np.roll(np.abs(dev), (-(wb // 2), -(wb // 2)), axis=(0, 1))  # index = window top-left

        def gen():
            r = best(score)
            if r is None:
                return None
            c = dev[(r[0] // b + wb // 2) % dev.shape[0], (r[1] // b + wb // 2) % dev.shape[1]]
            return {"name": "lowfreq_peak" if c > 0 else "lowfreq_trough", "y0": r[0], "x0": r[1],
                    "why": "low-pass (sigma 35 mm) luma %+.1f %% of the tile mean at the window centre" % (100 * c)}
        return gen

    gens = [mask_gen(m) for m in d["masks"] if m not in d["layout"]] + [element_gen(), lowfreq_gen()]
    while len(sites) < n_sites and gens:
        for g in list(gens):
            if len(sites) >= n_sites:
                break
            s = g()
            if s is None:
                gens.remove(g)
            else:
                sites.append(s)
    for s in cfg.get("previews", {}).get("sites", []):
        cx, cy = s["center_px"]
        sites.append({"name": s.get("name", "site"), "y0": int(cy - size // 2) % H, "x0": int(cx - size // 2) % W,
                      "why": s.get("why", "listed in previews.sites")})
    seen = {}
    for s in sites:  # unique, file-safe names
        base = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in s["name"])
        seen[base] = seen.get(base, 0) + 1
        s["name"] = base if seen[base] == 1 else "%s_%d" % (base, seen[base])
    return sites


def element_window(ys, xs, cy, cx, H, W, size, b, chosen):
    """Top-left of a free window (<= 25 % overlap) that holds the element's wrapped bounding box, as near centred as
    possible (on the b-px grid); the centred window when the element is bigger than a crop. (None, None) if none."""
    dy = (ys - cy + H // 2) % H - H // 2
    dx = (xs - cx + W // 2) % W - W // 2
    span = []
    for c, lo, hi, n in ((cy, int(dy.min()), int(dy.max()), H), (cx, int(dx.min()), int(dx.max()), W)):
        centred = c - size // 2
        if hi - lo + 1 > size:
            span.append(np.array([centred]))
        else:
            first, last = c + hi + 1 - size, c + lo  # window [o, o + size) holds [c + lo, c + hi]
            grid = np.arange(first + (-first) % b, last + 1, b)
            span.append(np.unique(np.concatenate([[min(max(centred, first), last)], grid])))
    yy, xx = span[0][:, None], span[1][None, :]
    ok = free_at(yy % H, xx % W, chosen, H, W, size)
    if not ok.any():
        return None, None
    dist = np.where(ok, np.abs(yy - (cy - size // 2)) + np.abs(xx - (cx - size // 2)), np.inf)
    i, j = np.unravel_index(int(np.argmin(dist)), dist.shape)
    return int(yy[i, 0]) % H, int(xx[0, j]) % W


def zoom_origin(layout, site, size, zoom):
    """Top-left of a zoom window centred on a layout corner (boundary in x and in y) near the middle of a site."""
    H, W = layout.shape
    c = crop(layout, site["y0"], site["x0"], size, size)
    ex = ndi.gaussian_filter(np.abs(np.diff(c, axis=1, append=c[:, -1:])), 6)
    ey = ndi.gaussian_filter(np.abs(np.diff(c, axis=0, append=c[-1:])), 6)
    q = size // 4
    score = (ex * ey)[q:size - q, q:size - q]
    if score.max() <= 0:
        score = (ex + ey)[q:size - q, q:size - q]
    i, j = np.unravel_index(int(np.argmax(score)), score.shape)
    if score[i, j] <= 0:
        i, j = score.shape[0] // 2, score.shape[1] // 2
    return (site["y0"] + q + i - zoom // 2) % H, (site["x0"] + q + j - zoom // 2) % W


def mask_edges(m):
    """Pixels of mask >= 0.5 with a 4-neighbour below 0.5 (wrap)."""
    on = m >= 0.5
    inner = on & np.roll(on, 1, 0) & np.roll(on, -1, 0) & np.roll(on, 1, 1) & np.roll(on, -1, 1)
    return on & ~inner


def mask_overlay(bc, masks, edges, colours):
    """Dimmed grey albedo, each mask tinted in its colour (alpha = 0.5 x mask value), its 0.5 contour drawn solid."""
    lum = bc @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    out = np.repeat((0.15 + 0.6 * lum)[..., None], 3, -1)
    for m, e, col in zip(masks, edges, colours):
        a = (np.clip(m, 0.0, 1.0) * 0.5)[..., None]
        out = out * (1 - a) + np.array(col, np.float32) * a
        out[e] = col
    return out


# ----------------------------------------------------------------------------- one variant


def bits_of(a):
    """8 when every sampled value is a multiple of 1/255 (8-bit file, or the Pillow fallback), else 16."""
    sample = a.ravel()[::97]
    return 8 if np.abs(sample * 255 - np.round(sample * 255)).max() < 1e-4 else 16


def dims(w_mm, h_mm, unit="m"):
    """'1.80 m wide', or '2.00 m wide x 1.00 m tall' when the extents differ."""
    f = (lambda x: "%.2f m" % (x / 1000.0)) if unit == "m" else (lambda x: "%.0f mm" % x)
    return "%s wide" % f(w_mm) if f(w_mm) == f(h_mm) else "%s wide x %s tall" % (f(w_mm), f(h_mm))


def mm_per_px(mmx, mmy):
    return "%.3f mm/px" % mmx if abs(mmx - mmy) < 5e-4 else "%.3f mm/px across, %.3f down" % (mmx, mmy)


def safe_name(name):
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name)


def render_variant(path, out, n_sites, shadows, ref=None, taken=None):
    """Write <out>/<variant>_*.png; return index info plus the images the compare sheets need.
    Big arrays are freed as soon as their views are written (about 1 GB peak RSS for a 2048 variant)."""
    t0 = time.time()
    with open(path) as fh:
        cfg = json.load(fh)
    ctx = mc.Ctx(cfg, os.path.dirname(os.path.abspath(path)))
    if ctx.normal_format not in ("directx", "opengl"):
        raise mc.ConfigError("scale.normal_format is '%s': use directx or opengl" % ctx.normal_format)
    v = safe_name(cfg.get("variant") or os.path.splitext(os.path.basename(path))[0])
    if taken is not None:  # two configs with one variant name must not overwrite each other's files
        base, k = v, 1
        while v in taken:
            k += 1
            v = "%s_%d" % (base, k)
        taken.add(v)
    hmm = ctx.height_mm()
    H, W = hmm.shape
    bc = ctx.main.map("basecolor")
    bc = np.repeat(bc[..., None], 3, axis=2) if bc.ndim == 2 else bc[..., :3]
    d = {"hmm": hmm, "luma": ctx.map_values("basecolor", "linear", "luma"),  # shared with per_element luma
         "rough": optional_gray(ctx, ("roughness",), 0.5),
         "masks": {m: np.asarray(ctx.main.gray(m), np.float32) for m in cfg["maps"].get("masks", {})}}
    d["layout"], layout_how = layout_masks(ctx, cfg, d["masks"])
    ao = optional_gray(ctx, ("ao", "ambientocclusion", "ambient_occlusion"), 1.0)
    tile_mm, tile_mm_y = W * ctx.mmx, H * ctx.mmy
    rows = []

    def emit(name, img, shows, scale, caveat):
        fn = "%s_%s.png" % (v, name)
        Image.fromarray(img if img.dtype == np.uint8 else to8(img)).save(os.path.join(out, fn), compress_level=3)
        rows.append((fn, shows, scale, caveat))

    def extent(n_tiles, width=None):
        """'<w> m wide[ x <h> m tall][, <mm>/px]' for n_tiles x n_tiles tiles drawn `width` px wide."""
        e = dims(n_tiles * tile_mm, n_tiles * tile_mm_y)
        return e if width is None else "%s, %.2f mm/px" % (e, n_tiles * tile_mm / width)

    def small(a, width):  # physical aspect, also for non-square px
        return lin_to_srgb(resize_wrap(a, width, max(1, int(round(width * tile_mm_y / tile_mm)))))

    sh = "cast shadows" if shadows else "no cast shadows (--no-shadows)"
    ang = {k: "az %.1f deg, el %.1f deg" % light_angles(L) for k, L in LIGHTS.items()}
    s1024 = "whole tile, " + extent(1, 1024)
    lit = "toy shader (see Shader)"

    # sites first (fewest big arrays alive), then keep only crops of the exported basecolor and normal
    size = min(CROP_PX, H, W)
    sites = pick_sites(ctx, cfg, d, n_sites, size)
    c = lambda a, s: crop(a, s["y0"], s["x0"], size, size)
    color_bits = bits_of(bc)
    for s in sites:
        s["bc"] = c(bc, s)
    alb = mc.srgb_to_linear(bc)
    del bc
    ctx.main.drop("basecolor", "id")
    emit("albedo_1024", small(alb, 1024), "basecolor only, unlit", s1024, "unlit")
    nrm = ctx.main.map("normal")[..., :3]
    normal_bits = bits_of(nrm)
    for s in sites:
        s["nrm"] = c(nrm, s)
    n = map_normals(nrm, ctx.normal_format)
    del nrm
    ctx.main.drop("normal")
    front = shade(alb, n, d["rough"], ao, LIGHTS["front"])
    front_1024 = to8(small(front, 1024))
    emit("lit_front_1024", front_1024, "lit, front light (%s), no cast shadows" % ang["front"], s1024, lit)
    t3 = 1536 // 3
    front_t3, front_t4 = to8(small(front, t3)), to8(small(front, 256))
    del front
    vis_a = shadow_vis(hmm, LIGHTS["raking_a"], ctx.mmx, ctx.mmy) if shadows else None
    rake_a = shade(alb, n, d["rough"], ao, LIGHTS["raking_a"], vis_a)
    emit("lit_raking_a_1024", small(rake_a, 1024), "lit, raking light from the upper left (%s), %s"
         % (ang["raking_a"], sh), s1024, lit)
    vis_b = shadow_vis(hmm, LIGHTS["raking_b"], ctx.mmx, ctx.mmy) if shadows else None
    rake_b = shade(alb, n, d["rough"], ao, LIGHTS["raking_b"], vis_b)
    del vis_b
    emit("lit_raking_b_1024", small(rake_b, 1024), "lit, raking light from the lower right (%s), %s"
         % (ang["raking_b"], sh), s1024, lit)
    del rake_b
    hn = height_normals(ctx, hmm)
    agree = normal_agreement(n, hn)
    del n
    grey = mc.srgb_to_linear(np.full(3, HILL_GREY_SRGB, np.float32))
    hill = shade(grey, hn, 1.0, 1.0, LIGHTS["raking_a"], vis_a, specular=False)
    del hn, vis_a
    emit("hillshade_1024", small(hill, 1024), "relief only: normals from the height map, grey albedo, no AO, same "
         "light and shadows as raking_a. Compare with lit_raking_a to tell colour from relief", s1024,
         "toy shader, no specular; shows the height map, not the normal map")
    del hill
    px = mm_per_px(ctx.mmx, ctx.mmy)
    emit("lit_raking_full", lin_to_srgb(rake_a), "lit raking_a at full resolution",
         "whole tile, %s, %s (1:1)" % (extent(1), px), lit)
    emit("tiled3x3_albedo", np.tile(to8(small(alb, t3)), (3, 3, 1)), "3x3 tiles of the basecolor",
         "3x3 tiles = " + extent(3, 3 * t3), "unlit")
    del alb
    emit("tiled3x3_lit", np.tile(front_t3, (3, 3, 1)), "3x3 tiles, front light", "3x3 tiles = " + extent(3, 3 * t3),
         lit)
    emit("tiled4x4_lit_small", np.tile(front_t4, (4, 4, 1)), "4x4 tiles, front light: repetition at distance",
         "4x4 tiles = " + extent(4, 4 * 256), lit)

    order = d["layout"] + [m for m in d["masks"] if m not in d["layout"]]
    colours = {m: PALETTE[i % len(PALETTE)] for i, m in enumerate(order)}
    legend = ", ".join("%s = %s" % (m, PALETTE_NAMES[i % len(PALETTE)]) for i, m in enumerate(order))
    edges = {m: mask_edges(d["masks"][m]) for m in order}
    s_crop = "1:1 crop = %s (%d px, %s)" % (dims(size * ctx.mmx, size * ctx.mmy, "mm"), size, px)
    for k, s in enumerate(sites, 1):
        y0, x0 = s["y0"], s["x0"]
        tag = "crop%d_%s" % (k, s["name"])
        hc, bcc = c(hmm, s), s.pop("bc")
        s.update(file_tag=tag, h_lo=float(hc.min()), h_hi=float(hc.max()))
        where = "%s, origin x %d y %d" % (s["name"], x0, y0)
        emit(tag + "_lit_raking", lin_to_srgb(c(rake_a, s)), "%s: lit raking_a" % where, s_crop, lit)
        emit(tag + "_albedo", bcc, "%s: basecolor" % where, s_crop, "unlit")
        emit(tag + "_height", (hc - s["h_lo"]) / max(s["h_hi"] - s["h_lo"], 1e-6),
             "%s: height, black = %.2f mm, white = %.2f mm" % (where, s["h_lo"], s["h_hi"]), s_crop,
             "stretched per crop: grey levels are not comparable between crops")
        if np.ndim(d["rough"]):
            rc = c(d["rough"], s)
            emit(tag + "_roughness", rc, "%s: roughness, raw 0-1 (crop p1-p99 %.2f-%.2f)"
                 % (where, np.percentile(rc, 1), np.percentile(rc, 99)), s_crop, "unlit, not stretched")
        emit(tag + "_normal", s.pop("nrm"), "%s: normal map RGB as exported (%s)" % (where, ctx.normal_format), s_crop,
             "unlit; %d-bit read" % normal_bits)
        if order:
            emit(tag + "_masks", mask_overlay(bcc, [c(d["masks"][m], s) for m in order],
                                              [c(edges[m], s) for m in order],
                                              [colours[m] for m in order]),
                 "%s: masks over dimmed grey albedo (%s; tint = 0.5 x mask value, solid line = 0.5 contour)"
                 % (where, legend), s_crop, "unlit")
    zsite = sites[0]
    ref_mask = d["masks"][d["layout"][0]] if d["layout"] else (next(iter(d["masks"].values())) if d["masks"] else None)
    if ref_mask is not None:
        zy, zx = zoom_origin(ref_mask, zsite, size, ZOOM_PX)
        target = "a %s corner" % (d["layout"][0] if d["layout"] else "mask")
    else:
        zy, zx = (zsite["y0"] + (size - ZOOM_PX) // 2) % H, (zsite["x0"] + (size - ZOOM_PX) // 2) % W
        target = "the typical site's centre"
    z = to8(lin_to_srgb(crop(rake_a, zy, zx, ZOOM_PX, ZOOM_PX)))
    emit("zoom3x_raking", np.repeat(np.repeat(z, 3, 0), 3, 1),
         "lit raking_a, %d px window centred on %s, origin x %d y %d (inside crop1)" % (ZOOM_PX, target, zx, zy),
         "%.0f mm wide, nearest-neighbour x3 (1 map px = 3x3 screen px = %.3f mm)" % (ZOOM_PX * ctx.mmx, ctx.mmx), lit)

    ry, rx = (sites[0]["y0"], sites[0]["x0"]) if ref is None else (int(ref[0] * H) % H, int(ref[1] * W) % W)
    cmp_crop = to8(lin_to_srgb(crop(rake_a, ry, rx, size, size)))
    warn = []
    if agree[1] < -0.2 or agree[0] < -0.2:
        warn.append("the normal map disagrees with the height map (correlation of tilt x %.2f, y %.2f; both should "
                    "be positive): %s. Lit views follow the normal map as configured (%s), the hillshade follows "
                    "the height map" % (agree[0], agree[1], "the green channel is flipped, so scale.normal_format "
                                        "is probably wrong" if agree[0] > 0.2 else "the normal map may not come "
                                        "from this height map", ctx.normal_format))
    info = {"variant": v, "config": os.path.abspath(path), "maps_dir": ctx.main.dir, "prefix": ctx.main.prefix,
            "W": W, "H": H, "mm": ctx.mmx, "mmy": ctx.mmy, "tile_mm": tile_mm, "tile_mm_y": tile_mm_y,
            "depth": ctx.depth_mm, "fmt": ctx.normal_format,
            "layout": d["layout"], "layout_how": layout_how, "process": [m for m in d["masks"] if m not in d["layout"]],
            "legend": legend, "rows": rows, "sites": sites, "normal_bits": normal_bits, "color_bits": color_bits,
            "size": size, "agree": agree, "warn": warn, "seconds": time.time() - t0}
    return info, front_1024, cmp_crop, (ry / float(H), rx / float(W)), (rx, ry)


# ----------------------------------------------------------------------------- index


def shader_note(shadows):
    a = {k: "az %.1f deg, el %.1f deg" % light_angles(L) for k, L in LIGHTS.items()}
    return [
        "Lit views (`lit_*`, `hillshade`, `tiled*_lit`, `zoom3x_raking`, `*_lit_raking`, `compare_*`) use the brick "
        "project's views.py toy shader: one directional light, Lambert diffuse plus a GGX D-term specular "
        "(alpha = max(roughness^2, 0.02), spec = D x 0.04 x N.L x 0.25; no Fresnel, no geometry term), "
        "ambient = 0.08 x AO, exposure 1/max(L.z, 0.2). A flat face renders at about its albedo under the front light "
        "(x1.01 with AO 1) and brighter under the raking lights (x1.14 with AO 1), so compare colour only between views "
        "with the same light. Faces tilted toward a raking light clip to white. No IBL, no interreflection; metallic is ignored. Shading is linear; albedo is "
        "decoded from sRGB and the output re-encoded to sRGB. Downsizing is Lanczos in linear light, wrapped at the "
        "tile border; tiled sheets tile the downsized image.",
        "Lights (x right, y up the image): front %s; raking_a from the upper left, %s; raking_b from the lower right, "
        "%s." % (a["front"], a["raking_a"], a["raking_b"]),
        ("Raking views and the hillshade add height-field cast shadows: each pixel marches toward the light over the "
         "height map (wrapping at the border) for up to height range / tan(elevation); it is shadowed where the "
         "terrain rises above the ray, softened over 1 px of ray rise. The front light casts no shadows."
         if shadows else "Cast shadows are OFF (--no-shadows): deep recesses under raking light are over-lit, and "
         "steep walls facing the light read as bright rims."),
        "Judge colour from albedo, relief from hillshade and lit views together. Before calling a dark line, rim or "
        "crumpled look a defect, check it against the height crop and the hillshade (it may be the shader).",
    ]


def write_index(out, infos, compare, shadows):
    L = ["# Preview index", "",
         "Written by `previews.py` (sd-material-research). Configs: %s." % ", ".join(
             "`%s`" % i["config"] for i in infos), "", "## Shader", ""]
    L += ["- " + s for s in shader_note(shadows)] + [""]
    for i in infos:
        L += ["## %s" % i["variant"], "",
              "- Maps: `%s/%s*`, %d x %d px. Tile %s, %s. Height depth %g mm. Normals %s, read at %d bits; basecolor "
              "read at %d bits." % (i["maps_dir"], i["prefix"], i["W"], i["H"], dims(i["tile_mm"], i["tile_mm_y"]),
                                    mm_per_px(i["mm"], i["mmy"]), i["depth"], i["fmt"], i["normal_bits"],
                                    i["color_bits"]),
              "- Layout masks: %s (%s). Process masks: %s. Overlay colours: %s." % (
                  ", ".join(i["layout"]) or "none", i["layout_how"], ", ".join(i["process"]) or "none",
                  i["legend"] or "no masks")] + ["- **Warning:** " + w + "." for w in i["warn"]] + ["",
              "### Crop sites", "", "| crop | picked because | origin px (x, y) | height in crop (mm) |", "|---|---|---|---|"]
        for s in i["sites"]:
            L.append("| %s | %s | %d, %d | %.2f-%.2f |" % (s["file_tag"], s["why"], s["x0"], s["y0"], s["h_lo"], s["h_hi"]))
        L += ["", "Origins are top-left corners in map px; crops wrap around the tile border.", "",
              "### Files", "", "| file | shows | scale | caveat |", "|---|---|---|---|"]
        L += ["| %s | %s | %s | %s |" % r for r in i["rows"]]
        L.append("")
    if compare:
        L += ["## Comparison sheets", "", "| file | shows | scale | caveat |", "|---|---|---|---|"]
        L += ["| %s | %s | %s | %s |" % r for r in compare]
        L.append("")
    with open(os.path.join(out, "views_index.md"), "w") as fh:
        fh.write("\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("configs", nargs="+", help="checks.json files, one per variant")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--sites", type=int, default=3, help="crop sites per variant: 1 typical + N-1 worst (default 3)")
    ap.add_argument("--no-shadows", action="store_true", help="skip the cast shadows on the raking views")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    infos, fronts, crops, ref, ref_px, taken = [], [], [], None, None, set()
    for path in a.configs:
        if os.path.basename(path).startswith("scorecard_"):  # matcheck output that checks/*.json picks up
            print("skipped %s: a matcheck scorecard, not a config" % path, file=sys.stderr)
            continue
        try:
            info, front, cc, r, rpx = render_variant(path, a.out, max(1, a.sites), not a.no_shadows, ref, taken)
        except (mc.ConfigError, KeyError, ValueError, OSError) as e:
            print("config error in %s: %s" % (path, e), file=sys.stderr)
            return 2
        if ref is None:
            ref, ref_px = r, rpx
        infos.append(info)
        fronts.append(front)
        crops.append(cc)
        print("%s: %d files, %.1f s" % (info["variant"], len(info["rows"]), info["seconds"]))
        for w in info["warn"]:
            print("%s: warning: %s" % (info["variant"], w), file=sys.stderr)
    compare = []
    if len(infos) > 1:
        names = [i["variant"] for i in infos]
        labelled_row(fronts, ["%s: lit front, whole tile" % nm for nm in names]).save(
            os.path.join(a.out, "compare_front.png"), compress_level=3)
        labelled_row(crops, ["%s: lit raking_a" % nm for nm in names]).save(
            os.path.join(a.out, "compare_crop_raking.png"), compress_level=3)
        i0 = infos[0]
        compare = [("compare_front.png", "lit_front_1024 of %s, side by side" % ", ".join(names),
                    "each panel the whole tile, %s" % dims(i0["tile_mm"], i0["tile_mm_y"]), "toy shader (see Shader)"),
                   ("compare_crop_raking.png", "lit raking_a crop at the same place in every variant: %s's typical "
                    "site, origin x %d y %d" % (names[0], ref_px[0], ref_px[1]),
                    "each panel a 1:1 crop, %s" % dims(i0["size"] * i0["mm"], i0["size"] * i0["mmy"], "mm"),
                    "toy shader (see Shader)")]
    write_index(a.out, infos, compare, not a.no_shadows)
    print("wrote %s/views_index.md" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
