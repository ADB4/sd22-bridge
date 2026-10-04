#!/usr/bin/env python3
"""Run the physical checks in a checks.json against exported material maps and write a scorecard.

Usage:
    python matcheck.py checks/weathered.json [--out DIR] [--only id1,id2] [--quiet]

The check vocabulary is documented in references/checks.md. Exit code: 0 when every hard check
passes, 1 when a hard check fails, 2 on a configuration error.
Needs numpy, Pillow and scipy, plus opencv-python-headless to read 16-bit colour PNGs at full precision
(scripts/setup_env.sh creates an environment with them).
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

try:
    import cv2
except ImportError:  # Pillow then reads colour PNGs at 8 bits, and the scorecard says so
    cv2 = None

Image.MAX_IMAGE_PIXELS = None
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)  # Rec.709

# ----------------------------------------------------------------------------- image io


def load_image(path):
    """Float32 array in 0-1: HxW for single-channel files, HxWxC (RGB order) for colour.
    OpenCV keeps 16-bit colour; the Pillow fallback reads colour at 8 bits. 16-bit grey is exact either way."""
    if cv2 is not None:
        a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if a is not None:
            return cv_float(a)
    return pil_float(path)


def cv_float(a):
    """OpenCV array (BGR(A); uint8, uint16 or float) to float32 RGB(A) in 0-1."""
    if a.ndim == 3:
        c = a.shape[2]
        a = a[..., 0] if c <= 2 else a[..., [2, 1, 0, 3][:c]]  # grey(+alpha) -> grey; BGR(A) -> RGB(A)
    scale = {np.uint8: 255.0, np.uint16: 65535.0}.get(a.dtype.type)
    out = a.astype(np.float32)
    if scale:
        out /= np.float32(scale)
    return out


def pil_float(path):
    """Pillow reader: exact for 8/16-bit grey, 8 bits for colour (Pillow keeps the high byte of 16-bit RGB)."""
    im = Image.open(path)
    mode = im.mode
    if mode in ("I;16", "I;16B", "I;16L"):
        return np.asarray(im, dtype=np.float32) / np.float32(65535.0)
    if mode == "I":
        a = np.asarray(im, dtype=np.float32)
        return a / np.float32(65535.0 if a.max() > 255 else 255.0)
    if mode == "F":
        return np.asarray(im, dtype=np.float32)
    if mode in ("1", "L", "P"):
        return np.asarray(im.convert("L"), dtype=np.float32) / np.float32(255.0)
    if mode == "LA":
        return np.asarray(im, dtype=np.float32)[..., 0] / np.float32(255.0)
    return np.asarray(im.convert("RGBA") if mode == "RGBA" else im.convert("RGB"), dtype=np.float32) / np.float32(255.0)


def to_gray(a):
    """Single channel view: first channel when the colour channels are equal, else Rec.709 luma."""
    if a.ndim == 2:
        return a
    rgb = a[..., :3]
    if np.allclose(rgb[..., 0], rgb[..., 1], atol=1e-6) and np.allclose(rgb[..., 0], rgb[..., 2], atol=1e-6):
        return rgb[..., 0]
    return rgb @ LUMA


def srgb_to_linear(c):
    c = np.clip(c, 0.0, 1.0)
    if np.ndim(c) == 0:
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    lo = c <= 0.04045
    out = c + 0.055  # same values as the np.where form, without its full-size temporaries
    out /= 1.055
    np.power(out, 2.4, out=out)
    out[lo] = c[lo] / 12.92
    return out


LAB_CHANNELS = ("lab_l", "lab_a", "lab_b", "chroma", "hue")
CHANNELS = ("luma", "r", "g", "b") + LAB_CHANNELS
SRGB_TO_XYZ = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], np.float32)


def lab_channel(rgb, channel):
    """CIELAB (D65) channel of sRGB-encoded 0-1 colour: lab_l / lab_a / lab_b, chroma C*ab, or hue h_ab in degrees."""
    xyz = srgb_to_linear(rgb) @ SRGB_TO_XYZ.T / np.array([0.95047, 1.0, 1.08883], np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(np.maximum(xyz, 0.0)), 7.787 * xyz + 16.0 / 116.0)
    if channel == "lab_l":
        return 116.0 * f[..., 1] - 16.0
    la, lb = 500.0 * (f[..., 0] - f[..., 1]), 200.0 * (f[..., 1] - f[..., 2])
    if channel == "lab_a":
        return la
    if channel == "lab_b":
        return lb
    return np.hypot(la, lb) if channel == "chroma" else np.degrees(np.arctan2(lb, la)) % 360.0


# ----------------------------------------------------------------------------- helpers


def pct(a, q):
    return float(np.percentile(a, q)) if a.size else float("nan")


def stat_of(a, stat):
    a = np.asarray(a, dtype=np.float64).ravel()
    a = a[np.isfinite(a)]
    if a.size == 0:
        return float("nan")
    s = str(stat).lower()
    if s in ("median", "p50"):
        return float(np.median(a))
    if s == "mean":
        return float(a.mean())
    if s == "min":
        return float(a.min())
    if s == "max":
        return float(a.max())
    if s == "std":
        return float(a.std())
    if s == "count":
        return float(a.size)
    if s == "sum":
        return float(a.sum())
    if s == "cv":
        m = a.mean()
        return float(a.std() / m) if m else float("nan")
    if s.startswith("p"):
        return pct(a, float(s[1:]))
    raise ValueError("unknown stat '%s'" % stat)


def summary(a, unit=""):
    a = np.asarray(a, dtype=np.float64).ravel()
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"n": 0}
    r = lambda v: round(float(v), 4)
    return {"n": int(a.size), "min": r(a.min()), "p05": r(pct(a, 5)), "median": r(np.median(a)),
            "mean": r(a.mean()), "p95": r(pct(a, 95)), "max": r(a.max()), "unit": unit}


def listify(x):
    if x is None:
        return []
    return list(x) if isinstance(x, (list, tuple)) else [x]


def wrap_edt(mask, r_px):
    """Distance (px) from each False pixel to the nearest True pixel, tile-wrapped, valid up to r_px."""
    p = int(math.ceil(r_px)) + 2
    pad = np.pad(mask, p, mode="wrap")
    d = ndi.distance_transform_edt(~pad)
    return d[p:-p, p:-p]


def erode(mask, r_px):
    if r_px <= 0:
        return mask
    p = int(math.ceil(r_px)) + 2
    pad = np.pad(mask, p, mode="wrap")
    d = ndi.distance_transform_edt(pad)
    return d[p:-p, p:-p] > r_px


def dilate(mask, r_px):
    if r_px <= 0:
        return mask
    return wrap_edt(mask, r_px) <= r_px


def sweep_wrap(mask, length_px, axis, forward, include_ref=False):
    """Pixels 1..length_px past a source pixel along one axis (0 = rows, 1 = columns), wrapping: forward on axis 0 is
    toward the bottom of the image. The source pixels themselves are included only with include_ref."""
    m = np.moveaxis(np.asarray(mask, bool), axis, 0)
    if not forward:
        m = m[::-1]
    n = m.shape[0]
    idx = np.arange(2 * n)[:, None]
    last = np.maximum.accumulate(np.where(np.concatenate([m, m], 0), idx, -(4 * n)), axis=0)
    d = (idx - last)[n:]  # distance to the nearest source at or behind each pixel, across the wrapped border
    out = (d >= (0 if include_ref else 1)) & (d <= length_px)
    if not forward:
        out = out[::-1]
    return np.moveaxis(out, 0, axis)


def label_wrap(mask, connectivity=8, wrap=(True, True)):
    """Connected components on a tileable mask; parts split by the tile border are merged.
    wrap=(rows, cols) says which borders join (for a crop that spans only one axis of the tile)."""
    structure = np.ones((3, 3), bool) if connectivity == 8 else ndi.generate_binary_structure(2, 1)
    lab, n = ndi.label(mask, structure=structure)
    if n == 0:
        return lab, 0
    compact = wrap_merge(lab, n, wrap)
    return compact[lab], int(compact.max())


def wrap_merge(lab, n, wrap=(True, True)):
    """Map from ndi.label labels to compact labels after joining labels that meet across the tile border
    (straight across, row to row and column to column); label 0 stays 0."""
    parent = np.arange(n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    if wrap[1]:
        for a, b in zip(lab[:, 0], lab[:, -1]):
            if a and b:
                union(a, b)
    if wrap[0]:
        for a, b in zip(lab[0, :], lab[-1, :]):
            if a and b:
                union(a, b)
    roots = np.array([find(i) for i in range(n + 1)])
    return np.unique(roots, return_inverse=True)[1]  # label 0 maps to root 0, the smallest -> compact index 0


def split_values(lab, keep, connectivity=4):
    """Connected parts of each value of `lab` inside `keep`, tile-wrapped as label_wrap does, in one labelling pass:
    pixels sit on the even cells of a 2x grid whose in-between cells are set where two neighbours share a value.
    Same parts as label_wrap(lab == v) for every v; 8-connectivity adds the diagonal pairs (not across the border)."""
    H, W = lab.shape
    big = np.zeros((2 * H, 2 * W), bool)
    big[0::2, 0::2] = keep
    big[0::2, 1::2] = keep & np.roll(keep, -1, 1) & (lab == np.roll(lab, -1, 1))  # column 2W-1 joins W-1 to 0
    big[1::2, 0::2] = keep & np.roll(keep, -1, 0) & (lab == np.roll(lab, -1, 0))
    blab, n = ndi.label(big, structure=ndi.generate_binary_structure(2, 1))
    if n == 0:
        return np.zeros((H, W), np.int64), 0
    compact = wrap_merge(blab, n)
    out = compact[blab[0::2, 0::2]]
    del blab, big
    if connectivity == 8:
        a, b, la, lb = [], [], [], []
        for s0, s1 in (((slice(None, -1), slice(None, -1)), (slice(1, None), slice(1, None))),
                       ((slice(None, -1), slice(1, None)), (slice(1, None), slice(None, -1)))):
            m = (out[s0] > 0) & (out[s1] > 0) & (out[s0] != out[s1]) & (lab[s0] == lab[s1])
            a.append(out[s0][m])
            b.append(out[s1][m])
        a, b = np.concatenate(a), np.concatenate(b)
        if a.size:
            from scipy.sparse import coo_matrix
            from scipy.sparse.csgraph import connected_components
            k = int(out.max()) + 1
            cc = connected_components(coo_matrix((np.ones(a.size), (a, b)), shape=(k, k)), directed=False)[1]
            new = np.zeros(k, np.int64)
            new[1:] = np.unique(cc[1:], return_inverse=True)[1] + 1
            out = new[out]
    return out, int(out.max())


def gaussian_wrap(a, sigma_px):
    """Gaussian blur that wraps around the tile: exact periodic FFT for wide kernels, ndimage for narrow ones."""
    if sigma_px < 3:
        return ndi.gaussian_filter(a, sigma=sigma_px, mode="wrap")
    fy = np.fft.fftfreq(a.shape[0])[:, None]
    fx = np.fft.rfftfreq(a.shape[1])[None, :]
    g = np.exp(-2.0 * (np.pi * sigma_px) ** 2 * (fy ** 2 + fx ** 2))
    out = np.fft.irfft2(np.fft.rfft2(a) * g, s=a.shape)
    return out.astype(np.float32) if a.dtype == np.float32 else out


def box_mean(v, mask, size, min_px=1):
    """Mean of v over mask in a size x size box around each pixel (wrapped); NaN with fewer than min_px mask pixels."""
    num = ndi.uniform_filter(np.where(mask, v, 0).astype(np.float32), size=size, mode="wrap")
    den = ndi.uniform_filter(mask.astype(np.float32), size=size, mode="wrap")
    return np.where(den * (size * size) >= min_px - 0.5, num / np.maximum(den, 1e-12), np.nan).astype(np.float32)


def grouped_median(ids, vals, n):
    """Median of vals for each integer id in 0..n (NaN where an id has no values)."""
    order = np.lexsort((vals, ids))
    v = vals[order]
    cnt = np.bincount(ids, minlength=n + 1)
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    out = np.full(n + 1, np.nan)
    ok = cnt > 0
    out[ok] = 0.5 * (v[(start + (cnt - 1) // 2)[ok]] + v[(start + cnt // 2)[ok]])
    return out


def block_level(values, mask, block_px, stat, min_px):
    """Per-block statistic of values inside mask, NaN-filled from neighbours, bilinear-upsampled (wrapped)."""
    H, W = values.shape
    by, bx = max(1, int(round(H / block_px))), max(1, int(round(W / block_px)))
    ys = np.linspace(0, H, by + 1).astype(int)
    xs = np.linspace(0, W, bx + 1).astype(int)
    grid = np.full((by, bx), np.nan)
    for i in range(by):
        for j in range(bx):
            m = mask[ys[i]:ys[i + 1], xs[j]:xs[j + 1]]
            if m.sum() >= min_px:
                grid[i, j] = stat_of(values[ys[i]:ys[i + 1], xs[j]:xs[j + 1]][m], stat)
    for _ in range(max(by, bx)):
        nan = np.isnan(grid)
        if not nan.any() or nan.all():
            break
        acc = np.zeros_like(grid)
        cnt = np.zeros_like(grid)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = np.roll(grid, (dy, dx), axis=(0, 1))
            ok = ~np.isnan(nb)
            acc[ok] += nb[ok]
            cnt[ok] += 1
        fill = nan & (cnt > 0)
        grid[fill] = acc[fill] / cnt[fill]
    # bilinear upsample with wrap: block centres at (i+0.5)*size
    yy = (np.arange(H) + 0.5) / (H / by) - 0.5
    xx = (np.arange(W) + 0.5) / (W / bx) - 0.5
    y0 = np.floor(yy).astype(int)
    x0 = np.floor(xx).astype(int)
    fy = (yy - y0)[:, None]
    fx = (xx - x0)[None, :]
    g = lambda a, b: grid[np.mod(a, by)[:, None], np.mod(b, bx)[None, :]]
    return ((1 - fy) * (1 - fx) * g(y0, x0) + (1 - fy) * fx * g(y0, x0 + 1)
            + fy * (1 - fx) * g(y0 + 1, x0) + fy * fx * g(y0 + 1, x0 + 1))


# ----------------------------------------------------------------------------- renders and regions


class ConfigError(Exception):
    pass


class Render:
    """One set of exported maps (a variant, or a comparison render such as nowear)."""

    def __init__(self, cfg, maps_cfg, base_dir, notes=None):
        self.cfg = cfg
        self.maps_cfg = maps_cfg
        d = maps_cfg.get("dir", ".")
        self.dir = d if os.path.isabs(d) else os.path.normpath(os.path.join(base_dir, d))
        self.prefix = maps_cfg.get("prefix", "")
        self.ext = maps_cfg.get("ext", ".png")
        self.notes = notes if notes is not None else []
        self.files = {}
        self.size = None  # (H, W) of the main height map, set by Ctx: every map must match it
        self._maps = {}
        self._gray = {}
        self._views = {}
        self._regions = {}

    def names(self):
        """Logical map names declared in the config (maps and masks)."""
        names = dict(self.cfg["maps"])
        names.update({k: v for k, v in self.maps_cfg.items() if k not in ("dir", "prefix", "ext", "masks")})
        masks = dict(self.cfg["maps"].get("masks", {}))
        masks.update(self.maps_cfg.get("masks", {}))
        return {k: v for k, v in list(names.items()) + list(masks.items())
                if k not in ("dir", "prefix", "ext", "masks") and isinstance(v, str)}

    def path(self, name):
        names = dict(self.cfg["maps"])  # logical names declared on the main render
        names.update({k: v for k, v in self.maps_cfg.items() if k not in ("dir", "prefix", "ext", "masks")})
        masks = dict(self.cfg["maps"].get("masks", {}))
        masks.update(self.maps_cfg.get("masks", {}))
        stem = names.get(name, masks.get(name, name))
        if not isinstance(stem, str):
            raise ConfigError("map '%s' is not a file name" % name)
        p = stem if os.path.isabs(stem) else os.path.join(self.dir, self.prefix + stem)
        if not os.path.splitext(p)[1]:
            p += self.ext
        return p

    def map(self, name):
        if name not in self._maps:
            p = self.path(name)
            if not os.path.exists(p):
                raise ConfigError("missing map '%s': %s" % (name, p))
            a = load_image(p)
            if self.size and a.shape[:2] != self.size:
                raise ConfigError("map '%s' is %dx%d px but the main height map is %dx%d: export all maps at one size"
                                  % (name, a.shape[1], a.shape[0], self.size[1], self.size[0]))
            if a.ndim == 3 and cv2 is None and "color maps read at 8 bits" not in self.notes:
                self.notes.append("color maps read at 8 bits")
            self._maps[name] = a
            self.files[name] = p
        return self._maps[name]

    def drop(self, *names):
        """Forget cached maps and their views (to free memory); they reload on the next use."""
        for name in names:
            self._maps.pop(name, None)
            self._gray.pop(name, None)
            for k in [k for k in self._views if k[0] == name]:
                del self._views[k]

    def gray(self, name):
        if name not in self._gray:
            self._gray[name] = to_gray(self.map(name))
        return self._gray[name]

    @property
    def shape(self):
        return self.gray("height").shape


class Ctx:
    def __init__(self, cfg, base_dir):
        self.cfg = cfg
        sc = cfg.get("scale", {})
        self.tile_m = sc.get("tile_m")
        self.res = sc.get("resolution")
        self.depth_mm = float(sc.get("height_depth_mm", 1.0))
        self.normal_format = sc.get("normal_format", "directx").lower()
        if self.tile_m is None:
            raise ConfigError("scale.tile_m is required")
        self.notes = []
        self.main = Render(cfg, cfg["maps"], base_dir, self.notes)
        self.compare = {k: Render(cfg, v, base_dir, self.notes) for k, v in cfg.get("compare", {}).items()}
        self._elements = {}
        H, W = self.main.shape
        for R in [self.main] + list(self.compare.values()):
            R.size = (H, W)
        tm = self.tile_m if isinstance(self.tile_m, (list, tuple)) else [self.tile_m, self.tile_m]
        self.mmx = tm[0] * 1000.0 / W
        self.mmy = tm[1] * 1000.0 / H
        self.mm = (self.mmx + self.mmy) / 2.0
        self.area_m2 = tm[0] * tm[1]
        if self.res and self.res != W:
            self.note = "maps are %d px, scale.resolution says %d: using the map size" % (W, self.res)
            self.notes.append(self.note)
        else:
            self.note = None

    def render(self, name=None):
        if not name:
            return self.main
        if name not in self.compare:
            raise ConfigError("unknown comparison render '%s'" % name)
        return self.compare[name]

    def height_mm(self, render=None):
        return self.map_values("height", "mm", render=render)

    def px(self, mm):
        return float(mm) / self.mm

    def region(self, name, render=None):
        R = self.render(render)
        if name in R._regions:
            if R._regions[name] is None:
                raise ConfigError("region '%s' refers to itself" % name)
            return R._regions[name]
        regs = self.cfg.get("regions", {})
        if name not in regs:
            # a bare mask name works as a region with threshold 0.5
            m = R.gray(name) >= 0.5
            R._regions[name] = m
            return m
        R._regions[name] = None  # cycle guard
        try:
            R._regions[name] = self._build_region(name, regs[name], R, render)
        except Exception:
            R._regions.pop(name, None)  # a failed build must not read as a cycle on the next check
            raise
        return R._regions[name]

    def _build_region(self, name, spec, R, render):
        """Boolean mask for one region spec (see region())."""
        base = None
        if "mask" in spec:
            v = R.gray(spec["mask"])
            if "range" in spec:
                lo, hi = spec["range"]
                base = (v >= lo) & (v <= hi)
            else:
                base = v >= float(spec.get("threshold", 0.5))
        elif "below_local" in spec:
            bl = spec["below_local"]
            m = bl.get("map", spec.get("map", "height"))
            v = self.map_values(m, "mm" if m == "height" else bl.get("space", "raw"), bl.get("channel", "luma"), render)
            size = 2 * int(round(self.px(bl.get("radius_mm", 10.0)))) + 1
            lvl = box_mean(v, self.region(bl["ref"], render), size, int(bl.get("min_px", 10)))
            base = v < lvl - float(bl.get("offset_mm", bl.get("offset", 0.0)))  # NaN level -> False
        elif "rel_below" in spec:
            rb = spec["rel_below"]
            v = self.map_values(rb["map"], rb.get("space", "linear"), rb.get("channel", "luma"), render)
            ref = stat_of(v[self.region(rb["ref"], render)], rb.get("stat", "median"))
            base = v < float(rb.get("scale", 0.5)) * ref
        elif "sweep" in spec:
            sw = spec["sweep"]
            dirs = {"down": (0, True), "up": (0, False), "right": (1, True), "left": (1, False)}
            if sw.get("direction") not in dirs:
                raise ConfigError("region '%s': sweep direction must be down, up, left or right" % name)
            axis, fwd = dirs[sw["direction"]]
            length = int(round(float(sw["length_mm"]) / (self.mmy if axis == 0 else self.mmx)))
            base = sweep_wrap(self.region(sw["ref"], render), length, axis, fwd, bool(sw.get("include_ref", False)))
        elif "map" in spec:
            v = R.gray(spec["map"])
            if "channel" in spec or "space" in spec:
                v = self.map_values(spec["map"], spec.get("space", "raw"), spec.get("channel", "luma"), render)
            if spec["map"] == "height" and ("min_mm" in spec or "max_mm" in spec):
                v = v * self.depth_mm
                lo, hi = spec.get("min_mm"), spec.get("max_mm")
            else:
                lo, hi = spec.get("min"), spec.get("max")
            base = np.ones(v.shape, bool)
            if lo is not None:
                base &= v >= lo
            if hi is not None:
                base &= v <= hi
        elif "height_split" in spec:
            hs = spec["height_split"]
            h = self.height_mm(render)
            lo_r = self.region(hs["low"], render)
            hi_r = self.region(hs["high"], render)
            stat = hs.get("stat", "median")
            lvl_lo, lvl_hi = stat_of(h[lo_r], stat), stat_of(h[hi_r], stat)
            level = lvl_lo + float(hs.get("frac", 0.5)) * (lvl_hi - lvl_lo)
            base = h < level if hs.get("below", True) else h >= level
        elif "boundary" in spec:
            a, b = spec["boundary"]
            band = self.px(spec.get("band_mm", self.mm))
            ra, rb = self.region(a, render), self.region(b, render)
            base = (wrap_edt(ra, band + 1) <= band) & (wrap_edt(rb, band + 1) <= band)
        if spec.get("invert") and base is not None:
            base = ~base
        if "or" in spec:
            acc = base if base is not None else np.zeros(R.shape, bool)
            for r in listify(spec["or"]):
                acc = acc | self.region(r, render)
            base = acc
        if "and" in spec:
            acc = base if base is not None else np.ones(R.shape, bool)
            for r in listify(spec["and"]):
                acc = acc & self.region(r, render)
            base = acc
        if "not" in spec:
            acc = base if base is not None else np.ones(R.shape, bool)
            for r in listify(spec["not"]):
                acc = acc & ~self.region(r, render)
            base = acc
        if base is None:
            raise ConfigError("region '%s' has no mask/map/below_local/rel_below/height_split/boundary/sweep/and/or/not" % name)
        if spec.get("erode_mm"):
            base = erode(base, self.px(spec["erode_mm"]))
        if spec.get("dilate_mm"):
            base = dilate(base, self.px(spec["dilate_mm"]))
        return base

    def map_values(self, name, space="raw", channel="luma", render=None):
        """A 2-D float32 view of a map (cached): raw 0-1, srgb255 (0-255), linear, or mm for height; luma, one channel,
        or a CIELAB channel (lab_l / lab_a / lab_b / chroma / hue, computed from the sRGB values; space is ignored)."""
        if channel not in CHANNELS:
            raise ConfigError("unknown channel '%s' (use %s)" % (channel, ", ".join(CHANNELS)))
        R = self.render(render)
        key = (name, space, channel)
        if key not in R._views:
            a = R.map(name)
            if channel in LAB_CHANNELS:
                rgb = a[..., :3] if a.ndim == 3 else np.repeat(a[..., None], 3, axis=2)
                v = lab_channel(rgb, channel)
            elif a.ndim == 3:
                rgb = a[..., :3]
                if space == "linear":
                    rgb = srgb_to_linear(rgb)
                elif space == "srgb255":
                    rgb = rgb * np.float32(255.0)
                v = rgb[..., "rgb".index(channel)] if channel in ("r", "g", "b") else rgb @ LUMA
            elif name == "height" and space == "mm":
                v = a * np.float32(self.depth_mm)
            elif space == "srgb255":
                v = a * np.float32(255.0)
            elif space == "linear":
                v = srgb_to_linear(a)
            else:
                v = a
            R._views[key] = np.ascontiguousarray(v, dtype=np.float32)
        return R._views[key]

    def elements(self, spec):
        """Integer label image for per-element checks: from an ID map or from components of a region (cached)."""
        src = spec.get("elements", {"from": "id_map", "map": spec.get("id_map", "id")})
        min_px = int(spec.get("element_min_px", 50))
        key = json.dumps([src, min_px], sort_keys=True)
        if key not in self._elements:
            self._elements[key] = self._make_elements(src, min_px)
        return self._elements[key]

    def _make_elements(self, src, min_px):
        if src.get("from", "id_map") == "components":
            return label_wrap(self.region(src["region"]), src.get("connectivity", 4))
        a = self.main.map(src.get("map", "id"))
        if a.ndim == 3:
            q = np.round(a[..., :3] * 255).astype(np.int64)
            key = (q[..., 0] << 16) | (q[..., 1] << 8) | q[..., 2]
        else:
            key = np.round(a * 65535).astype(np.int64)
        uniq, inv = np.unique(key, return_inverse=True)
        lab = inv.reshape(key.shape) + 1
        if not src.get("split_components", True):
            return lab, len(uniq)
        # one ID value can cover several separate units (random IDs collide); split each into its own elements
        keep = np.bincount(lab.ravel(), minlength=len(uniq) + 1) >= min_px  # ID values with >= min_px pixels
        keep[0] = False
        if src.get("ignore_zero", True):
            keep[1:] &= uniq != 0
        return split_values(lab, keep[lab], src.get("connectivity", 4))


# ----------------------------------------------------------------------------- checks
# Each check returns (value, details). details["n_key"] counts the pixels (or the unit in "n_key_unit") of the set
# the value rests on; main() reports the check as vacuous when it is below the check's min_px (default 1).


def runs_1d(line):
    """Lengths of True runs in a cyclic 1-D boolean line (complete runs only)."""
    if line.all() or not line.any():
        return np.array([], dtype=int)
    k = int(np.argmin(line))  # a False pixel: rotate so no run crosses the ends
    l = np.roll(line, -k).astype(np.int8)
    d = np.diff(np.concatenate([[0], l, [0]]))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    return ends - starts


def ck_run_length(ctx, c):
    R = ctx.region(c["region"])
    axis = c.get("axis", "both")
    step = max(1, int(c.get("step_px", 1)))
    vals = []
    if axis in ("x", "both"):
        for y in range(0, R.shape[0], step):
            vals.extend(runs_1d(R[y, :]) * ctx.mmx)
    if axis in ("y", "both"):
        for x in range(0, R.shape[1], step):
            vals.extend(runs_1d(R[:, x]) * ctx.mmy)
    v = np.array(vals, dtype=float)
    if c.get("min_mm") is not None:
        v = v[v >= c["min_mm"]]
    if c.get("max_mm") is not None:
        v = v[v <= c["max_mm"]]
    return stat_of(v, c.get("stat", "median")), {"runs_mm": summary(v, "mm"), "n_key": int(R.sum())}


def component_shapes(lab, n):
    """Per component 1..n: PCA elongation sqrt(l1/l2) and fill (area / bounding-box area), unwrapped at the border."""
    H, W = lab.shape
    ys, xs = np.nonzero(lab)
    ids = lab[ys, xs]
    uid, first = np.unique(ids, return_index=True)
    ry, rx = np.zeros(n + 1, np.int64), np.zeros(n + 1, np.int64)
    ry[uid], rx[uid] = ys[first], xs[first]
    dy = ((ys - ry[ids] + H // 2) % H - H // 2).astype(np.float64)  # offsets from a pixel of the same component
    dx = ((xs - rx[ids] + W // 2) % W - W // 2).astype(np.float64)
    cnt = np.maximum(np.bincount(ids, minlength=n + 1), 1).astype(np.float64)
    my, mx = np.bincount(ids, dy, n + 1) / cnt, np.bincount(ids, dx, n + 1) / cnt
    syy = np.bincount(ids, dy * dy, n + 1) / cnt - my * my + 1 / 12.0  # + a pixel's own variance
    sxx = np.bincount(ids, dx * dx, n + 1) / cnt - mx * mx + 1 / 12.0
    sxy = np.bincount(ids, dx * dy, n + 1) / cnt - mx * my
    half_tr = (sxx + syy) / 2
    disc = np.sqrt(np.maximum(half_tr ** 2 - (sxx * syy - sxy ** 2), 0))
    aspect = np.sqrt((half_tr + disc) / np.maximum(half_tr - disc, 1e-12))
    idx = np.arange(1, n + 1)
    hy = np.asarray(ndi.maximum(dy, ids, idx)) - np.asarray(ndi.minimum(dy, ids, idx)) + 1
    hx = np.asarray(ndi.maximum(dx, ids, idx)) - np.asarray(ndi.minimum(dx, ids, idx)) + 1
    fill = cnt[1:] / (hy * hx)
    return aspect[1:], fill


def ck_components(ctx, c):
    R = ctx.region(c["region"])
    Wn = ctx.region(c["within"]) if c.get("within") else None
    if Wn is not None:
        R = R & Wn
    lab, n = label_wrap(R, c.get("connectivity", 8))
    if n == 0:
        sizes = np.array([], dtype=float)
    else:
        sizes = np.bincount(lab.ravel(), minlength=n + 1)[1:].astype(float)
    area_mm2 = sizes * ctx.mmx * ctx.mmy
    eq_d = 2.0 * np.sqrt(area_mm2 / math.pi)
    keep = eq_d >= float(c.get("min_mm", 0.0))
    if c.get("border_px") is not None and n:
        # opt-in: only the components that reach within border_px of the tile border (wrap artefacts of a warped
        # coordinate show up there as specks)
        b = max(1, int(c["border_px"]))
        band = np.zeros(R.shape, bool)
        band[:b, :] = band[-b:, :] = True
        band[:, :b] = band[:, -b:] = True
        touch = np.zeros(n + 1, bool)
        touch[np.unique(lab[band])] = True
        keep &= touch[1:]
    eq_k, area_k = eq_d[keep], area_mm2[keep]
    metric = c.get("metric", "count_per_m2")
    det = {"components": int(keep.sum()), "eq_diameter_mm": summary(eq_k, "mm"),
           "n_key": int(Wn.sum()) if Wn is not None else int(R.size)}
    if c.get("border_px") is not None:
        det["border_px"] = int(c["border_px"])
    if metric == "count":
        val = float(keep.sum())
    elif metric == "count_per_m2":
        val = float(keep.sum()) / ctx.area_m2
    elif metric == "eq_diameter_mm":
        val = stat_of(eq_k, c.get("stat", "median"))
    elif metric == "largest_mm":
        val = float(eq_k.max()) if eq_k.size else 0.0
    elif metric in ("small_island_count", "small_island_frac"):
        thr = float(c.get("below_mm", 10.0))
        small = eq_k < thr
        det["below_mm"] = thr
        if metric == "small_island_count":
            val = float(small.sum())
        else:
            val = float(area_k[small].sum() / area_k.sum()) if area_k.sum() else 0.0
    elif metric in ("aspect", "fill"):
        aspect, fill = component_shapes(lab, n) if n else (np.array([]), np.array([]))
        aspect, fill = aspect[keep], fill[keep]
        det.update(aspect=summary(aspect), fill=summary(fill))
        val = stat_of(aspect if metric == "aspect" else fill, c.get("stat", "median"))
    else:
        raise ConfigError("components metric '%s' unknown" % metric)
    return val, det


def ck_coverage(ctx, c):
    R = ctx.region(c["region"])
    W = ctx.region(c["within"]) if c.get("within") else np.ones_like(R)
    n = W.sum()
    return (float((R & W).sum() / n) if n else float("nan")), {"within_px": int(n), "n_key": int(n)}


def ck_concentration(ctx, c):
    R = ctx.region(c["region"])
    D = ctx.region(c["driver"])
    W = ctx.region(c["within"]) if c.get("within") else np.ones_like(R)
    ins, out = W & D, W & ~D
    ci = R[ins].mean() if ins.any() else float("nan")
    co = R[out].mean() if out.any() else float("nan")
    # nothing outside the driver: undefined (inf would pass any lower bound)
    ratio = float("nan") if not out.any() else float(ci / co) if co > 0 else float("inf") if ci > 0 else float("nan")
    return ratio, {"coverage_in_driver": round(float(ci), 5), "coverage_outside": round(float(co), 5),
                   "n_key": int(ins.sum())}


def ck_height_diff(ctx, c):
    h = ctx.height_mm()
    A, B = ctx.region(c["a"]), ctx.region(c["b"])
    n_key = int(min(A.sum(), B.sum()))
    sa, sb = c.get("stat_a", c.get("stat", "median")), c.get("stat_b", c.get("stat", "median"))
    if not c.get("local_mm"):
        va, vb = stat_of(h[A], sa), stat_of(h[B], sb)
        return va - vb, {"a_mm": round(va, 4), "b_mm": round(vb, 4), "n_key": n_key}
    blk = ctx.px(c["local_mm"])
    mn = int(c.get("block_min_px", 20))
    la = block_level(h, A, blk, sa, mn)
    lb = block_level(h, B, blk, sb, mn)
    d = (la - lb)[A | B]
    return stat_of(d, c.get("over_blocks", "median")), {"local_diff_mm": summary(d, "mm"), "n_key": n_key}


def local_level(ctx, h, mask, stat, r_px, min_px=10):
    s = str(stat).lower()
    size = int(2 * round(r_px) + 1)
    if s == "max":
        v = ndi.maximum_filter(np.where(mask, h, -np.inf), size=size, mode="wrap")
        return np.where(np.isfinite(v), v, np.nan)
    if s == "min":
        v = ndi.minimum_filter(np.where(mask, h, np.inf), size=size, mode="wrap")
        return np.where(np.isfinite(v), v, np.nan)
    if s == "mean":
        return box_mean(h, mask, size, min_px)
    # percentile or median: block statistic, neighbour-filled, bilinear
    lvl = block_level(h, mask, max(4.0, 2 * r_px), s, min_px)
    near = wrap_edt(mask, r_px + 1) <= r_px
    return np.where(near, lvl, np.nan)


def ck_order(ctx, c):
    """Fraction of upper pixels below the level of lower (+ margin_mm): local within neighborhood_mm, or global
    when neighborhood_mm is null. Margins are the upper pixels' heights over that level (mm). Vacuous when lower
    has fewer than lower_min_px pixels in all."""
    h = ctx.height_mm()
    U, L = ctx.region(c["upper"]), ctx.region(c["lower"])
    stat = c.get("lower_stat", "p95")
    nb = c.get("neighborhood_mm", 20)
    lmin = int(c.get("lower_min_px", 10))
    if nb is None:
        lvl = stat_of(h[L], stat)
        checked = U & bool(np.isfinite(lvl))
    else:
        lvl = local_level(ctx, h, L, stat, ctx.px(nb), lmin)
        checked = U & np.isfinite(lvl)
    clear = (h - lvl)[checked] if c.get("direction", "above") == "above" else (lvl - h)[checked]
    deficit = float(c.get("margin_mm", 0.0)) - clear
    viol = deficit > float(c.get("tolerance_mm", 1e-6))
    n = int(checked.sum())
    det = {"checked_px": n, "skipped_px_no_neighbour": int(U.sum()) - n, "violating_px": int(viol.sum()),
           "worst_mm": round(float(deficit[viol].max()), 4) if viol.any() else 0.0,
           "min_margin_mm": round(float(clear.min()), 4) if n else None,
           "p1_margin_mm": round(pct(clear, 1), 4) if n else None, "lower_px": int(L.sum()),
           "n_key": n if L.sum() >= lmin else 0}  # a lower set under lower_min_px makes the check vacuous
    if nb is None:
        det["global_level_mm"] = round(float(lvl), 4)
    return (float(viol.sum() / n) if n else 0.0), det


def ck_mask_invariance(ctx, c):
    ref = c["against"]
    if "region" in c:
        a, b = ctx.region(c["region"]), ctx.region(c["region"], ref)
    else:
        thr = float(c.get("threshold", 0.5))
        a, b = ctx.main.gray(c["mask"]) >= thr, ctx.render(ref).gray(c["mask"]) >= thr
    if a.shape != b.shape:
        raise ConfigError("mask_invariance: renders differ in size %s vs %s" % (a.shape, b.shape))
    changed = a ^ b
    area = max(1, int(b.sum()))
    return float(changed.sum() / area), {"changed_px": int(changed.sum()), "ref_area_px": area,
                                          "gained_px": int((a & ~b).sum()), "lost_px": int((~a & b).sum()),
                                          "n_key": int(b.sum())}


def ck_envelope(ctx, c):
    h = ctx.height_mm()
    h0 = ctx.height_mm(c["against"])
    keep = np.ones(h.shape, bool)
    for r in listify(c.get("except")):
        ex = ctx.region(r)
        if c.get("except_dilate_mm"):
            ex = dilate(ex, ctx.px(c["except_dilate_mm"]))
        keep &= ~ex
    if c.get("within"):
        keep &= ctx.region(c["within"])
    d = h - h0
    tol = float(c.get("tolerance_mm", 0.05))
    viol = keep & (d > tol)
    n = keep.sum()
    return (float(viol.sum() / n) if n else 0.0), {
        "violating_px": int(viol.sum()), "max_excess_mm": round(float(d[keep].max()), 4) if n else None,
        "lowered_frac": round(float((keep & (d < -tol)).sum() / max(1, n)), 4),
        "max_lowering_mm": round(float(-d[keep].min()), 4) if n else None, "n_key": int(n)}


def per_element_metric(ctx, c, lab, n, metric, region_key="region"):
    """Per-element values (indexed by label) and a validity mask, for metric coverage / luma_mean / luma_median /
    height_mean / value_mean. Valid: >= element_min_px pixels measured and >= min_area_mm2 of element area."""
    ids = lab.ravel()
    wv = ctx.region(c["within"]).ravel() if c.get("within") else np.ones(ids.shape, bool)
    if metric != "coverage" and c.get(region_key):
        wv = wv & ctx.region(c[region_key]).ravel()
    cnt = np.bincount(ids[wv], minlength=n + 1).astype(float)
    if metric == "coverage":
        R = ctx.region(c[region_key]).ravel()
        val = np.bincount(ids[wv & R], minlength=n + 1) / np.maximum(cnt, 1)
    else:
        if metric in ("luma_mean", "luma_median"):
            v = ctx.map_values(c.get("map", "basecolor"), c.get("space", "linear"), "luma")
        elif metric == "height_mean":
            v = ctx.height_mm()
        elif metric == "value_mean":
            v = ctx.map_values(c["map"], c.get("space", "raw"), c.get("channel", "luma"))
        else:
            raise ConfigError("per_element metric '%s' unknown" % metric)
        if metric == "luma_median":
            val = grouped_median(ids[wv], v.ravel()[wv], n)
        else:
            val = np.bincount(ids[wv], weights=v.ravel()[wv], minlength=n + 1) / np.maximum(cnt, 1)
    ok = cnt >= float(c.get("element_min_px", 50))
    if c.get("min_area_mm2"):
        ok &= np.bincount(ids, minlength=n + 1) * (ctx.mmx * ctx.mmy) >= float(c["min_area_mm2"])
    ok[0] = False
    return val, ok


def ck_per_element(ctx, c):
    lab, n = ctx.elements(c)
    metric = c.get("metric", "coverage")
    val, ok = per_element_metric(ctx, c, lab, n, metric)
    v = val[ok]
    stat = c.get("stat", "max")
    det = {"elements": int(ok.sum()), "per_element": summary(v), "n_key": int(ok.sum()), "n_key_unit": "elements"}
    if stat in ("corr", "abs_corr"):
        c2 = dict(c)
        c2["region"] = c.get("region2", c.get("region"))
        val2, ok2 = per_element_metric(ctx, c2, lab, n, c.get("metric2", metric))
        both = ok & ok2
        det["pairs"] = int(both.sum())
        if both.sum() < 3:
            return float("nan"), det
        r = float(np.corrcoef(val[both], val2[both])[0, 1])
        return (abs(r) if stat == "abs_corr" else r), det
    if stat in ("count_outside", "frac_outside", "range_max", "range_min"):
        norm = c.get("normalize", "mean")
        if norm not in ("mean", "median"):
            raise ConfigError("per_element normalize must be mean or median")
        m = (v.mean() if norm == "mean" else np.median(v)) if v.size else float("nan")
        rel = v / m if m else v * np.nan
        band = float(c.get("band", 0.12))
        out = (rel < 1 - band) | (rel > 1 + band)
        det.update({"band": band, "normalize": norm, "rel_min": round(float(rel.min()), 4) if v.size else None,
                    "rel_max": round(float(rel.max()), 4) if v.size else None})
        if stat == "count_outside":
            return float(out.sum()), det
        if stat == "frac_outside":
            return float(out.mean()) if v.size else float("nan"), det
        return (float(rel.max()) if stat == "range_max" else float(rel.min())), det
    return stat_of(v, stat), det


def grad_mm(ctx, h):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * ctx.mmx)
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / (2 * ctx.mmy)
    return gx, gy


def ck_slope(ctx, c):
    h = ctx.height_mm()
    gx, gy = grad_mm(ctx, h)
    ang = np.degrees(np.arctan(np.hypot(gx, gy)))
    if "between" in c:
        a, b = c["between"]
        band = ctx.px(c.get("band_mm", 2 * ctx.mm))
        ra, rb = ctx.region(a), ctx.region(b)
        sel = (wrap_edt(ra, band + 1) <= band) & (wrap_edt(rb, band + 1) <= band)
    else:
        sel = ctx.region(c["region"])
    v = ang[sel]
    if c.get("min_deg") is not None:  # ignore flat pixels that only sit inside the band
        v = v[v >= c["min_deg"]]
    return stat_of(v, c.get("stat", "median")), {"slope_deg": summary(v, "deg"), "n_key": int(v.size)}


LOWFREQ_STATS = ("std_over_mean", "frac_beyond", "peak_pct", "trough_pct")


def lowfreq_stat(lp, m, stat, beyond_pct):
    """One statistic of a low-passed map lp (pixels of interest only) relative to the map mean m."""
    dev = lp / m - 1.0
    if stat == "std_over_mean":
        return float(lp.std() / m)
    if stat == "frac_beyond":
        return float((np.abs(dev) > beyond_pct / 100.0).mean())
    if stat == "peak_pct":
        return float(dev.max() * 100)
    if stat == "trough_pct":
        return float(-dev.min() * 100)
    if stat.startswith("p"):
        return float(abs(np.percentile(lp, float(stat[1:])) / m - 1.0) * 100)
    raise ConfigError("lowfreq stat '%s' unknown" % stat)


def ck_lowfreq(ctx, c):
    """Worst over sigma_mm of a low-pass statistic; with a region, a masked (normalised) low-pass inside it."""
    v = ctx.map_values(c.get("map", "basecolor"), c.get("space", "linear"), c.get("channel", "luma"))
    R = ctx.region(c["region"]) if c.get("region") else None
    m = float(v[R].mean()) if R is not None and R.any() else float(v.mean())
    stat = str(c.get("stat", "std_over_mean")).lower()
    beyond = float(c.get("pct", 8.0))
    out = {"stat": stat, "mean": round(m, 5), "n_key": int(R.sum()) if R is not None else int(v.size)}
    worst = float("nan")
    for s in listify(c.get("sigma_mm", [40, 160])):
        if R is None:
            lp = gaussian_wrap(v, ctx.px(s))
        else:
            num = gaussian_wrap(np.where(R, v, 0).astype(np.float32), ctx.px(s))
            lp = num / np.maximum(gaussian_wrap(R.astype(np.float32), ctx.px(s)), 1e-6)
            lp = lp[R]
        if not m or lp.size == 0:
            continue
        row = {k: round(lowfreq_stat(lp, m, k, beyond), 5) for k in LOWFREQ_STATS + ("p0.5", "p99.5")}
        val = row[stat] if stat in row else lowfreq_stat(lp, m, stat, beyond)
        row[stat] = round(val, 5)
        out["sigma_%gmm" % s] = row
        worst = val if not worst >= val else worst
    return worst, out


def seam_rowmedian_z(a, axis, floor):
    """Row-median seam statistic of one map (HxWxC) along one axis: for every adjacent pair i, the median over the rows
    (columns) of the signed second difference e = d_i - (d_(i-1) + d_(i+1)) / 2, with d_i = x_(i+1) - x_i. A step at
    the border adds the same amount to e in every row, so the border pair's median moves with it; sparse features
    (a crack or a hole that reaches the border) touch few rows and barely move a median. z = (m_border - median(m_inner))
    / max(1.4826 MAD(m_inner), floor), worst channel, signed."""
    best = 0.0
    for ch in range(a.shape[2]):
        x = a[..., ch].astype(np.float64)
        if axis == 0:
            x = x.T                      # the top|bottom pairs become columns
        d = np.roll(x, -1, axis=1) - x   # d[:, i] = x[:, i+1] - x[:, i]; i = W-1 is the wrapped border pair
        e = d - 0.5 * (np.roll(d, 1, axis=1) + np.roll(d, -1, axis=1))
        m = np.median(e, axis=0)
        inner = m[:-1]
        med = float(np.median(inner))
        sc = max(1.4826 * float(np.median(np.abs(inner - med))), float(floor))
        z = (float(m[-1]) - med) / sc if sc > 0 else (0.0 if m[-1] == med else float("inf"))
        if abs(z) > abs(best):
            best = z
    return best


def ck_seam(ctx, c):
    """Max |z| of the wrapped border pair's mean absolute difference among all adjacent column (row) pairs.
    axis x tests the left|right border (the tile repeats along x), y the top|bottom border, both (default) both.
    method rowmedian (opt-in) scores the border pair's row-median signed second difference instead (seam_rowmedian_z):
    it keeps its power on busy maps, where a crack or a hole crossing the border inflates the mean statistic's spread.
    Its scale has an absolute floor in map units: `floor_mm` for the height (default 0.005 mm), `floor` for the other
    maps (default 0.5/255)."""
    two_sided = c.get("two_sided", True)
    axes = {"both": ((1, "x"), (0, "y")), "x": ((1, "x"),), "y": ((0, "y"),)}
    if c.get("axis", "both") not in axes:
        raise ConfigError("seam axis must be x, y or both")
    method = c.get("method", "mean_abs")
    if method not in ("mean_abs", "rowmedian"):
        raise ConfigError("seam method must be mean_abs or rowmedian")
    zs, det = [], {}
    for name in listify(c.get("maps", ["height", "basecolor"])):
        a = ctx.main.map(name)
        a = a[..., :3] if a.ndim == 3 else a[..., None]
        d = {}
        for axis, key in axes[c.get("axis", "both")]:
            if method == "rowmedian":
                floor = (float(c.get("floor_mm", 0.005)) / ctx.depth_mm if name == "height"
                         else float(c.get("floor", 0.5 / 255.0)))
                z = seam_rowmedian_z(a, axis, floor)
                d[key + "_z"] = round(float(z), 3)
            else:
                diff = np.abs(np.roll(a, -1, axis=axis) - a)  # pair (i, i+1); the last pair is the wrapped border
                prof = diff.mean(axis=(0, 2)) if axis == 1 else diff.mean(axis=(1, 2))
                seam, inner = float(prof[-1]), prof[:-1].astype(np.float64)
                sd = inner.std()
                z = (seam - inner.mean()) / sd if sd > 0 else (0.0 if seam == inner.mean() else float("inf"))
                d[key + "_z"], d[key + "_ratio"] = round(float(z), 3), round(seam / max(inner.mean(), 1e-12), 3)
            zs.append(abs(z) if two_sided else z)
        det[name] = d
    if method == "rowmedian":
        det["method"] = method
    return (float(max(zs)) if zs else float("nan")), det


def ck_value_range(ctx, c):
    v = ctx.map_values(c["map"], c.get("space", "raw"), c.get("channel", "luma"))
    sel = ctx.region(c["region"]) if c.get("region") else np.ones(v.shape, bool)
    return stat_of(v[sel], c.get("stat", "median")), {"values": summary(v[sel]), "n_key": int(sel.sum())}


def ck_value_order(ctx, c):
    v = ctx.map_values(c["map"], c.get("space", "raw"), c.get("channel", "luma"))
    regs = [ctx.region(r) for r in c["regions"]]
    stats = [stat_of(v[r], c.get("stat", "median")) for r in regs]
    gap = float(c.get("min_gap", 0.0))
    desc = c.get("order", "ascending") == "descending"
    ok = all(((b - a) if not desc else (a - b)) >= gap for a, b in zip(stats, stats[1:]))
    det = {"values": dict(zip(c["regions"], [round(s, 4) for s in stats])), "order": c.get("order", "ascending"),
           "n_key": int(min(r.sum() for r in regs))}
    return (1.0 if ok else 0.0), det


def ck_orientation(ctx, c):
    if c.get("map"):
        f = ctx.map_values(c["map"], c.get("space", "raw"), c.get("channel", "luma"))
    else:
        f = ctx.region(c["region"]).astype(np.float32)
    f = gaussian_wrap(f, max(0.7, ctx.px(c.get("pre_sigma_mm", 0.0)) or 0.7))
    gx = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / 2
    gy = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) / 2
    s = max(1.0, ctx.px(c.get("window_mm", 4 * ctx.mm)))
    jxx, jyy, jxy = (gaussian_wrap(gx * gx, s), gaussian_wrap(gy * gy, s), gaussian_wrap(gx * gy, s))
    theta_g = 0.5 * np.arctan2(2 * jxy, jxx - jyy)  # dominant gradient direction (image coords, y down)
    tr = jxx + jyy
    coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / np.maximum(tr, 1e-12)
    struct = np.degrees(theta_g) + 90.0  # structures run perpendicular to the gradient
    struct = -struct  # report with y up (counter-clockwise from +x), like a drawing
    w = coh * tr
    if c.get("region"):
        sel = ctx.region(c["region"])
        if not c.get("map"):  # gradients of a mask live on its edges
            sel = dilate(sel, 1.5)
    else:
        sel = np.ones(f.shape, bool)
    d = np.abs(((struct - float(c.get("axis_deg", 0.0)) + 90.0) % 180.0) - 90.0)
    ww = w[sel]
    tol = float(c.get("tolerance_deg", 15))
    frac = float(ww[d[sel] <= tol].sum() / ww.sum()) if ww.sum() > 0 else float("nan")
    hist, edges = np.histogram((struct[sel] % 180.0), bins=12, range=(0, 180), weights=ww)
    peak = float(edges[int(np.argmax(hist))] + 7.5) if ww.sum() > 0 else None
    return frac, {"dominant_deg": peak, "tolerance_deg": tol, "n_key": int(sel.sum())}


def ck_spacing(ctx, c):
    det = {}
    if c.get("map"):
        f = ctx.map_values(c["map"], c.get("space", "raw"), c.get("channel", "luma"))
    else:
        R = ctx.region(c["region"])
        f = R.astype(np.float32)
        det["n_key"] = int(R.sum())
    axis = c.get("axis", "x")
    prof = f.mean(axis=0) if axis == "x" else f.mean(axis=1)
    mm = ctx.mmx if axis == "x" else ctx.mmy
    prof = prof - prof.mean()
    ac = np.fft.irfft(np.abs(np.fft.rfft(prof)) ** 2, n=prof.size)
    ac = ac / ac[0] if ac[0] else ac
    lo = max(1, int(float(c.get("min_mm", 2 * mm)) / mm))
    hi = min(prof.size // 2, int(float(c.get("max_mm", prof.size * mm / 2)) / mm))
    if hi <= lo:
        return float("nan"), det
    seg = ac[lo:hi]
    k = int(np.argmax(seg)) + lo
    det.update(autocorr_peak=round(float(ac[k]), 4), search_mm=[round(lo * mm, 2), round(hi * mm, 2)])
    return float(k * mm), det


def ck_ridge(ctx, c):
    """Fins: band pixels higher than both sides by > threshold_mm. With `against` (opt-in, e.g. nowear) the test runs
    on the height minus that render's height, so relief both renders share (a rut flank, the as-built texture) cancels
    and only what the process added or removed can form a fin."""
    h = ctx.height_mm()
    if c.get("against"):
        h = h - ctx.height_mm(c["against"])
    a, b = c["between"]
    band = ctx.px(c.get("band_mm", 3 * ctx.mm))
    ra, rb = ctx.region(a), ctx.region(b)
    sel = (wrap_edt(ra, band + 1) <= band) & (wrap_edt(rb, band + 1) <= band)
    k = int(c.get("half_width_px", 2))
    thr = float(c.get("threshold_mm", 0.3))
    fin = np.zeros(h.shape, bool)
    for ax in (0, 1):
        lo = np.minimum(np.roll(h, k, ax), np.roll(h, -k, ax))
        hi_side = np.maximum(np.roll(h, k, ax), np.roll(h, -k, ax))
        fin |= (h - hi_side > thr) & (h - lo > thr)
    fin &= sel
    n = sel.sum()
    det = {"fin_px": int(fin.sum()), "band_px": int(n), "threshold_mm": thr, "n_key": int(n)}
    if c.get("against"):
        det["against"] = c["against"]
    return (float(fin.sum() / n) if n else 0.0), det


ORIENTATIONS = ("top", "bottom", "left", "right")


def oriented(a, o):
    """View of a 2-D array in which orientation o's profiles run down the rows. A profile runs from outer into
    inner: top = downward (the top edges of inner units), bottom = upward, left = rightward, right = leftward."""
    if o in ("left", "right"):
        a = a.T
    return a[::-1] if o in ("bottom", "right") else a


def any_along(mask, offsets):
    """True where mask holds at any of the row offsets k (wrapped): out[y] = OR mask[y + k]."""
    out = np.zeros(mask.shape, bool)
    for k in offsets:
        out |= np.roll(mask, -k, axis=0)
    return out


def edge_windows(ctx, c, o):
    """Height windows (n x window_px, mm) across rising steps of orientation o, centred on the 50 % crossing."""
    win = int(c.get("window_px", 11)) | 1
    k = win // 2
    h = oriented(ctx.height_mm(), o).astype(np.float64)
    lo = ndi.minimum_filter1d(h, win, axis=0, mode="wrap")
    hi = ndi.maximum_filter1d(h, win, axis=0, mode="wrap")
    mid = lo + 0.5 * (hi - lo)
    sel = (hi - lo >= float(c.get("min_step_mm", 3.6))) & (np.roll(h, 1, axis=0) < mid) & (mid <= h)
    del lo, hi, mid
    if c.get("outer"):
        sel &= any_along(oriented(ctx.region(c["outer"]), o), range(-k, 0))
    if c.get("inner"):
        sel &= any_along(oriented(ctx.region(c["inner"]), o), range(0, k + 1))
    if c.get("exclude"):
        sel &= ~any_along(oriented(ctx.region(c["exclude"]), o), range(0, int(c.get("exclude_px", 6))))
    step = int(c.get("step_px", 1))
    if step > 1:
        sel &= (np.arange(sel.shape[1]) % step == int(c.get("offset_px", 0)) % step)[None, :]
    ys, xs = np.nonzero(sel)
    return np.stack([h[(ys + j) % h.shape[0], xs] for j in range(-k, k + 1)], axis=1)


def rise_px(w, t10, t90):
    """Distance (px) between the 10 % and 90 % crossings nearest the 50 % crossing, linearly interpolated."""
    n, win = w.shape
    k = win // 2
    r = np.arange(n)
    i = np.full(n, k - 1)
    for _ in range(k - 1):
        i = np.where((i > 0) & (w[r, i] > t10), i - 1, i)
    a, b = w[r, i], w[r, i + 1]
    p10 = i + np.clip((t10 - a) / np.maximum(b - a, 1e-12), 0, 1)
    j = np.full(n, k)
    for _ in range(win - 1 - k):
        j = np.where((j < win - 1) & (w[r, j] < t90), j + 1, j)
    a, b = w[r, j - 1], w[r, j]
    p90 = j - 1 + np.clip((t90 - a) / np.maximum(b - a, 1e-12), 0, 1)
    return p90 - p10


def ck_edge_profile(ctx, c):
    """Anti-aliasing and sharpness of height steps between outer and inner, per orientation (pooled value)."""
    metric = c.get("metric", "aa_frac")
    stat = c.get("stat", "median")
    pool = {"ramp": [], "peak": [], "rise": []}
    det = {}
    for o in listify(c.get("orientations", ORIENTATIONS)):
        if o not in ORIENTATIONS:
            raise ConfigError("edge_profile orientation '%s' unknown" % o)
        w = edge_windows(ctx, c, o)
        mm = ctx.mmy if o in ("top", "bottom") else ctx.mmx
        lo, hi = w.min(1), w.max(1)
        t10, t90 = lo + 0.1 * (hi - lo), hi - 0.1 * (hi - lo)
        ramp = ((w > t10[:, None]) & (w < t90[:, None])).sum(1)
        peak = np.degrees(np.arctan(np.abs(np.diff(w, axis=1)).max(1) / mm)) if w.size else np.array([])
        rise = rise_px(w, t10, t90) * mm if w.size else np.array([])
        for k, a in (("ramp", ramp), ("peak", peak), ("rise", rise)):
            pool[k].append(a)
        det[o] = {"profiles": int(w.shape[0]),
                  "aa_frac": round(float((ramp >= 1).mean()), 4) if ramp.size else None,
                  "mean_ramp_px": round(float(ramp.mean()), 4) if ramp.size else None,
                  "peak_slope_deg_p25_50_75": [round(pct(peak, q), 2) for q in (25, 50, 75)],
                  "rise_10_90_mm_median": round(stat_of(rise, "median"), 3)}
    ramp, peak, rise = (np.concatenate(pool[k]) for k in ("ramp", "peak", "rise"))
    det["n_key"], det["n_key_unit"] = int(ramp.size), "profiles"
    if metric == "aa_frac":
        val = float((ramp >= 1).mean()) if ramp.size else float("nan")
    elif metric == "mean_ramp_px":
        val = float(ramp.mean()) if ramp.size else float("nan")
    elif metric == "peak_slope_deg":
        val = stat_of(peak, stat)
    elif metric == "rise_10_90_mm":
        val = stat_of(rise, stat)
    else:
        raise ConfigError("edge_profile metric '%s' unknown" % metric)
    return val, det


def signed_distance_mm(ctx, R, reach_px):
    """Signed distance (mm) to the boundary of R, + inside and - outside, exact up to reach_px (wrapped)."""
    d_in = wrap_edt(~R, reach_px)
    d_out = wrap_edt(R, reach_px)
    return (np.where(R, d_in - 0.5, 0.5 - d_out) * ctx.mm).astype(np.float32)


def ck_boundary_profile(ctx, c):
    """Statistic of a map (optionally divided by a local reference level) in bins of signed distance from a region's
    boundary; the value is the min or max bin over range_mm, or the statistic pooled over it."""
    R = ctx.region(c["region"])
    v = ctx.map_values(c.get("map", "basecolor"), c.get("space", "linear"), c.get("channel", "luma"))
    lo, hi, step = (list(c.get("bins_mm", [-10.0, 10.0])) + [ctx.mm])[:3]
    ex = float(c.get("exclude_mm", 0.0))
    sd = signed_distance_mm(ctx, R, ctx.px(max(abs(lo), abs(hi), ex)) + 2)
    det = {}
    if c.get("reference"):
        ref = ctx.region(c["reference"]) & (sd < -ex)
        size = 2 * int(round(ctx.px(c.get("radius_mm", 20.0)))) + 1
        v = v / box_mean(v, ref, size, int(c.get("ref_min_px", 10)))
        det["reference_px"] = int(ref.sum())
    sel = (sd >= lo) & (sd < hi) & np.isfinite(v)
    if c.get("within"):
        sel &= ctx.region(c["within"])
    nb = int(math.ceil((hi - lo) / step - 1e-9))
    b = np.clip(np.floor((sd[sel] - lo) / step).astype(int), 0, nb - 1)
    order = np.argsort(b, kind="stable")
    b, vals = b[order], v[sel][order]
    cuts = np.searchsorted(b, np.arange(nb + 1))
    centres = lo + (np.arange(nb) + 0.5) * step
    stat, min_n = c.get("stat", "median"), int(c.get("bin_min_px", 20))
    prof = []
    for i in range(nb):
        seg = vals[cuts[i]:cuts[i + 1]]
        prof.append([round(float(centres[i]), 3), int(seg.size), round(stat_of(seg, stat), 4) if seg.size >= min_n else None])
    rlo, rhi = c.get("range_mm", [lo, hi])
    inr = [i for i in range(nb) if rlo <= centres[i] <= rhi]
    how = c.get("value", "min")
    if how == "pooled":
        seg = np.concatenate([vals[cuts[i]:cuts[i + 1]] for i in inr]) if inr else np.array([])
        val = stat_of(seg, stat)
    elif how in ("min", "max"):
        good = [prof[i][2] for i in inr if prof[i][2] is not None]
        val = (min(good) if how == "min" else max(good)) if good else float("nan")
    else:
        raise ConfigError("boundary_profile value must be min, max or pooled")
    det.update(profile_mm_n_stat=prof, range_mm=[rlo, rhi], n_key=int(sum(prof[i][1] for i in inr)))
    return val, det


def wrap_centroids(lab, n):
    """Centroids (y, x) in px of labels 1..n, averaged on the circle so parts split by the tile border stay whole."""
    ys, xs = np.nonzero(lab)
    ids = lab[ys, xs]
    out = []
    for coord, size in ((ys, lab.shape[0]), (xs, lab.shape[1])):
        ang = coord * (2 * np.pi / size)
        s, co = np.bincount(ids, np.sin(ang), n + 1)[1:], np.bincount(ids, np.cos(ang), n + 1)[1:]
        out.append((np.arctan2(s, co) % (2 * np.pi)) * size / (2 * np.pi))
    return out


def ck_dispersion(ctx, c):
    """Index of dispersion (variance / mean) of feature counts in window_mm windows, and the empty-window fraction.
    Poisson scatter gives about 1; natural clustering gives more, and more empty windows."""
    R = ctx.region(c["region"])
    H, W = R.shape
    lab, n = label_wrap(R, c.get("connectivity", 8))
    eq_d = 2.0 * np.sqrt(np.bincount(lab.ravel(), minlength=n + 1)[1:] * ctx.mmx * ctx.mmy / math.pi)
    keep = eq_d >= float(c.get("min_mm", 0.0))
    cy, cx = wrap_centroids(lab, n) if n else (np.array([]), np.array([]))
    cy, cx = (cy[keep] + 0.5) % H, (cx[keep] + 0.5) % W  # pixel centres sit at i + 0.5; wrap back into the tile
    win = float(c.get("window_mm", 30.0))
    ny, nx = max(1, int(round(H * ctx.mmy / win))), max(1, int(round(W * ctx.mmx / win)))
    ey, ex = np.linspace(0, H, ny + 1), np.linspace(0, W, nx + 1)
    counts = np.histogram2d(cy, cx, bins=[ey, ex])[0]
    use = np.ones(counts.shape, bool)
    if c.get("within"):
        iy = np.minimum(((np.arange(H) + 0.5) * ny / H).astype(int), ny - 1)
        ix = np.minimum(((np.arange(W) + 0.5) * nx / W).astype(int), nx - 1)
        cell = (iy[:, None] * nx + ix[None, :]).ravel()
        cover = np.bincount(cell, ctx.region(c["within"]).ravel(), ny * nx) / np.bincount(cell, minlength=ny * nx)
        use = cover.reshape(ny, nx) >= float(c.get("min_cover", 0.5))
    cnt = counts[use]
    mean = float(cnt.mean()) if cnt.size else float("nan")
    index = float(cnt.var(ddof=1) / mean) if cnt.size > 1 and mean > 0 else float("nan")
    empty = float((cnt == 0).mean()) if cnt.size else float("nan")
    det = {"features": int(keep.sum()), "windows": int(cnt.size), "window_mm": win, "mean_count": round(mean, 3),
           "index": round(index, 4), "empty_window_frac": round(empty, 4), "n_key": int(keep.sum()),
           "n_key_unit": "features"}
    metric = c.get("metric", "index")
    if metric not in ("index", "empty_window_frac"):
        raise ConfigError("dispersion metric must be index or empty_window_frac")
    return (index if metric == "index" else empty), det


def ck_step(ctx, c):
    """Fraction of neighbouring pixel pairs inside a region (eroded by 1 px) whose height differs by > threshold_mm."""
    h = ctx.height_mm()
    E = erode(ctx.region(c["region"]), 1.0)
    thr = float(c.get("threshold_mm", 1.0))
    axes = {"x": (1,), "y": (0,), "both": (1, 0)}[c.get("axis", "both")]
    pairs = steps = 0
    det = {"threshold_mm": thr, "n_key": int(E.sum())}
    for ax in axes:
        d = np.abs(np.roll(h, -1, ax) - h)
        both = E & np.roll(E, -1, ax)
        s = both & (d > thr)
        p, k = int(both.sum()), int(s.sum())
        det["x" if ax == 1 else "y"] = {"pairs": p, "steps": k, "frac": round(k / p, 6) if p else None,
                                        "max_mm": round(float(d[both].max()), 3) if p else None}
        pairs, steps = pairs + p, steps + k
    return (steps / pairs if pairs else float("nan")), det


def ck_normal_valid(ctx, c):
    """1 if the normal's green convention matches, x tilts against the height gradient, z > 0, and the slope scale
    median((n.x/n.z) / (-dh/dx)) is within 1 +- scale_tolerance (this validates height_depth_mm and tile_m)."""
    n = ctx.main.map(c.get("map", "normal"))[..., :3] * np.float32(2.0) - np.float32(1.0)
    ln = np.linalg.norm(n, axis=2)
    h = ctx.height_mm()
    gx, gy = grad_mm(ctx, h)  # gy: derivative along image rows (down)
    g = np.hypot(gx, gy)
    sel = g > np.percentile(g, 75)
    cx = float(np.corrcoef(n[..., 0][sel], gx[sel])[0, 1]) if sel.sum() > 10 else float("nan")
    cy = float(np.corrcoef(n[..., 1][sel], gy[sel])[0, 1]) if sel.sum() > 10 else float("nan")
    detected = "opengl" if cy > 0 else "directx"
    expect = c.get("normal_format", ctx.normal_format)
    zneg = float((n[..., 2] < 0).mean())
    # slope scale: tangent of the normal's tilt over the height map's slope, on sloped pixels
    nz = np.maximum(n[..., 2], 1e-3)
    ax, ay = np.abs(gx), np.abs(gy)
    sx = (ax > max(np.percentile(ax, 75), 1e-4)) & (n[..., 2] > 0.05)
    sy = (ay > max(np.percentile(ay, 75), 1e-4)) & (n[..., 2] > 0.05)
    ratio = float(np.median((n[..., 0] / nz)[sx] / -gx[sx])) if sx.sum() > 10 else float("nan")
    sign_y = 1.0 if detected == "opengl" else -1.0
    ratio_y = float(np.median((n[..., 1] / nz)[sy] / (sign_y * gy[sy]))) if sy.sum() > 10 else float("nan")
    tol = float(c.get("scale_tolerance", 0.15))
    fails = []
    if detected != expect:
        fails.append("green convention is %s, expected %s" % (detected, expect))
    if not cx < 0:
        fails.append("n.x does not tilt against dh/dx")
    if zneg >= 1e-3:
        fails.append("z < 0 on %.2g of pixels" % zneg)
    if not abs(ratio - 1.0) <= tol:
        fails.append("slope scale %.3f outside 1 +- %g: check height_depth_mm and tile_m" % (ratio, tol))
    det = {"detected": detected, "expected": expect, "corr_nx_dhdx": round(cx, 3), "corr_ny_dhdrow": round(cy, 3),
           "slope_scale_ratio": round(ratio, 4), "slope_scale_ratio_y": round(ratio_y, 4), "scale_tolerance": tol,
           "length": summary(ln), "frac_z_negative": round(zneg, 6), "failed": fails}
    return (0.0 if fails else 1.0), det


def ck_height_usage(ctx, c):
    h = ctx.main.gray("height")
    levels = int(np.unique(np.round(h * 65535)).size)
    det = {"min": round(float(h.min()), 5), "max": round(float(h.max()), 5),
           "frac_at_0": round(float((h <= 1 / 65535).mean()), 5), "frac_at_1": round(float((h >= 1 - 1 / 65535).mean()), 5),
           "unique_levels": levels, "looks_8bit": levels <= 256}
    metric = c.get("metric", "range_used")
    if metric == "clipped_frac":
        return det["frac_at_0"] + det["frac_at_1"], det
    if metric == "unique_levels":
        return float(levels), det
    return float(h.max() - h.min()), det


CHECKS = {
    "run_length": ck_run_length, "components": ck_components, "coverage": ck_coverage,
    "concentration": ck_concentration, "height_diff": ck_height_diff, "order": ck_order,
    "mask_invariance": ck_mask_invariance, "envelope": ck_envelope, "per_element": ck_per_element,
    "slope": ck_slope, "lowfreq": ck_lowfreq, "seam": ck_seam, "value_range": ck_value_range,
    "value_order": ck_value_order, "orientation": ck_orientation, "spacing": ck_spacing,
    "ridge": ck_ridge, "normal_valid": ck_normal_valid, "height_usage": ck_height_usage,
    "edge_profile": ck_edge_profile, "boundary_profile": ck_boundary_profile, "dispersion": ck_dispersion,
    "step": ck_step,
}

# target shortcuts that read naturally in checks.json
TARGET_KEYS = {"max_violation_frac": (None, "v"), "max_changed_frac": (None, "v"), "max_frac": (None, "v")}


def target_of(c):
    if "target" in c:
        return c["target"]
    for k in ("target_mm", "target_deg"):
        if k in c:
            return c[k]
    for k in TARGET_KEYS:
        if k in c:
            return [None, c[k]]
    if c["type"] in ("value_order", "normal_valid"):
        return [1, None]
    return None


def evaluate(value, target):
    if target is None or value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    lo, hi = target
    return (lo is None or value >= lo - 1e-12) and (hi is None or value <= hi + 1e-12)


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        if v != 0 and (abs(v) < 0.01 or abs(v) >= 10000):
            return "%.3g" % v
        return ("%.4f" % v).rstrip("0").rstrip(".")
    return str(v)


def fmt_target(t):
    if t is None:
        return "info"
    lo, hi = t
    if lo is None:
        return "<= %s" % fmt(float(hi))
    if hi is None:
        return ">= %s" % fmt(float(lo))
    return "%s .. %s" % (fmt(float(lo)), fmt(float(hi)))


# ----------------------------------------------------------------------------- manifest


def image_size(path):
    try:
        with Image.open(path) as im:
            return im.size
    except OSError:
        return None


def manifest_report(ctx):
    """Header info from <dir>/<prefix>manifest.json (graph, export time, params) and warnings for map files that
    predate their export or whose sizes differ."""
    info, warn, sizes = None, [], {}
    for rname, R in [("", ctx.main)] + sorted(ctx.compare.items()):
        files = {k: R.path(k) for k in R.names()}
        files.update(R.files)
        files = {k: p for k, p in files.items() if os.path.exists(p)}
        tag = "%s: " % rname if rname else ""
        for k, p in files.items():
            sizes[tag + os.path.basename(p)] = image_size(p)
        mp = os.path.join(R.dir, R.prefix + "manifest.json")
        if not os.path.exists(mp):
            continue
        try:
            with open(mp) as fh:
                m = json.load(fh)
        except (OSError, ValueError) as e:
            warn.append("%sunreadable manifest %s: %s" % (tag, mp, e))
            continue
        if not rname:
            info = {"path": mp, "graph": m.get("graph"), "package": m.get("package"),
                    "exported_at": m.get("exported_at", m.get("export_time")),
                    "params": m.get("graph_params", m.get("params")), "instances": m.get("instances"),
                    "note": m.get("note")}
        # sdkit writes the maps first and the manifest last; a map older than the export window is stale
        start = os.path.getmtime(mp) - float(m.get("total_s") or 60.0) - 2.0
        for k, p in sorted(files.items()):
            age = start - os.path.getmtime(p)
            if age > 0:
                warn.append("%s%s is older than its manifest (%.0f s before that export started): stale map?"
                            % (tag, os.path.basename(p), age))
        for row in m.get("outputs", []):
            p = row.get("path")
            got = image_size(p) if p and os.path.exists(p) else None
            if got and row.get("size") and list(got) != list(row["size"]):
                warn.append("%s%s is %dx%d, its manifest says %s" % (tag, os.path.basename(p), got[0], got[1], row["size"]))
    distinct = sorted({s for s in sizes.values() if s})
    if len(distinct) > 1:
        groups = {s: [k for k, v in sizes.items() if v == s] for s in distinct}
        warn.append("map sizes differ: " + "; ".join("%dx%d: %s" % (s[0], s[1], ", ".join(sorted(g)[:6]) +
                                                                     (" ..." if len(g) > 6 else ""))
                                                       for s, g in groups.items()))
    return info, warn


# ----------------------------------------------------------------------------- main


def run_check(ctx, c):
    """One scorecard row; a check below its min_px (default 1) on its key set is vacuous: passed null, no error."""
    row = {"id": c.get("id"), "type": c.get("type"), "severity": c.get("severity", "soft"),
           "why": c.get("why", ""), "target": target_of(c)}
    fn = CHECKS.get(c.get("type"))
    if fn is None:
        row.update(value=None, passed=None, error="unknown check type")
        return row
    t0 = time.time()
    try:
        val, det = fn(ctx, c)
        row.update(value=val, details=det, passed=evaluate(val, row["target"]))
        n_key = det.get("n_key")
        if c.get("min_px") is not None and n_key is None:
            raise ConfigError("min_px: check type '%s' has no region to count" % c["type"])
        if n_key is not None and n_key < float(c.get("min_px", 1)):
            row.update(passed=None, note="vacuous: %d %s" % (n_key, det.get("n_key_unit", "px")))
    except ConfigError as e:
        row.update(value=None, passed=None, error=str(e))
    except Exception as e:  # keep going: one broken check should not hide the rest
        row.update(value=None, passed=None, error="%s: %s" % (type(e).__name__, e))
    row["seconds"] = round(time.time() - t0, 2)
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("config")
    ap.add_argument("--out", help="directory for scorecard_<variant>.json/.md (default: config 'out_dir', else next to the config)")
    ap.add_argument("--only", help="comma-separated check ids")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    try:
        with open(a.config) as fh:
            cfg = json.load(fh)
        base = os.path.dirname(os.path.abspath(a.config))
        ctx = Ctx(cfg, base)
    except (ConfigError, KeyError, ValueError, OSError) as e:
        print("config error: %s" % e, file=sys.stderr)
        return 2
    only = set(a.only.split(",")) if a.only else None
    results = [run_check(ctx, c) for c in cfg.get("checks", [])
               if not c.get("skip") and not (only and c.get("id") not in only)]
    manifest, warnings = manifest_report(ctx)
    hard_fail = [r["id"] for r in results if r["severity"] == "hard" and r["passed"] is False]
    errors = [r["id"] for r in results if r.get("error")]
    soft_fail = [r["id"] for r in results if r["severity"] != "hard" and r["passed"] is False]
    vacuous = [r["id"] for r in results if r.get("note", "").startswith("vacuous")]
    card = {"material": cfg.get("material"), "variant": cfg.get("variant"), "config": os.path.abspath(a.config),
            "scale": {"mm_per_px": round(ctx.mm, 4), "height_depth_mm": ctx.depth_mm, "tile_m": ctx.tile_m},
            "manifest": manifest, "note": ctx.note, "notes": ctx.notes, "warnings": warnings,
            "hard_failed": hard_fail, "soft_failed": soft_fail, "vacuous": vacuous, "errors": errors,
            "seconds": round(time.time() - t0, 1), "results": results}
    out = a.out or cfg.get("out_dir") or base
    out = out if os.path.isabs(out) else os.path.normpath(os.path.join(base, out))
    os.makedirs(out, exist_ok=True)
    name = "scorecard_%s" % (cfg.get("variant") or os.path.splitext(os.path.basename(a.config))[0])
    with open(os.path.join(out, name + ".json"), "w") as fh:
        json.dump(card, fh, indent=1, default=lambda o: float(o) if isinstance(o, np.floating) else int(o))
    lines = ["# Scorecard: %s / %s" % (cfg.get("material", "?"), cfg.get("variant", "?")), "",
             "%.4f mm/px, height depth %g mm. Hard failures: %s. Soft misses: %s. Vacuous: %s. Errors: %s." % (
                 ctx.mm, ctx.depth_mm, ", ".join(hard_fail) or "none", ", ".join(soft_fail) or "none",
                 ", ".join(vacuous) or "none", ", ".join(errors) or "none"), ""]
    if manifest:
        lines += ["Export: graph `%s` at %s (%s). Params: `%s`" % (
            manifest["graph"], manifest["exported_at"], manifest["path"],
            json.dumps(manifest["params"], sort_keys=True, default=str)), ""]
    lines += ["- Note: %s" % n for n in ctx.notes] + ["- **Warning**: %s" % w for w in warnings]
    if ctx.notes or warnings:
        lines.append("")
    lines += ["| check | type | value | target | result | severity | why |", "|---|---|---|---|---|---|---|"]
    for r in results:
        if r.get("error"):
            res = "ERROR: " + r["error"]
        else:
            res = r.get("note") or {True: "pass", False: "FAIL", None: "info"}[r["passed"]]
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (r["id"], r["type"], fmt(r["value"]), fmt_target(r["target"]),
                                                               res, r["severity"], r["why"].replace("|", "/")))
    md = "\n".join(lines) + "\n"
    with open(os.path.join(out, name + ".md"), "w") as fh:
        fh.write(md)
    if not a.quiet:
        print(md)
        print("wrote %s/%s.{json,md}" % (out, name))
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
