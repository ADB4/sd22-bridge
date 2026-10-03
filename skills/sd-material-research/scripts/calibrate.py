#!/usr/bin/env python3
"""Histogram Scan Position for a target coverage, from a probe of the scan's INPUT.

Designer's Histogram Scan thresholds at centre = 1 - Position (higher Position = more white), so for a target white
coverage c inside a region: Position = 1 - quantile(input in region, 1 - c).

Usage:
    python calibrate.py <scan_input.png> 0.01 0.03 0.06 [--region mask.png [--threshold 0.5] [--invert]]
    python calibrate.py <scan_input.png> --map wear 0.1:0.01 0.6:0.05      # affine Position(param) through 2 points

Prints Positions (and an sdkit function spec for --map). Re-run after ANY upstream change: in the brick build a noise
swap or a facet/cap change shifted coverage 5-30x. Stretch a compressed input with Levels first if the Positions
come out crowded near 0 or 1.
"""
import argparse
import sys

import numpy as np

from matcheck import load_image, to_gray


def position_for(values, coverage):
    return float(1.0 - np.quantile(values, 1.0 - coverage))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input")
    ap.add_argument("targets", nargs="*", help="coverages (0-1), or param:coverage pairs with --map")
    ap.add_argument("--region")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--map", help="parameter (graph input id) for an affine Position(param) through two points")
    a = ap.parse_args(argv)
    v = to_gray(load_image(a.input))
    if a.region:
        m = to_gray(load_image(a.region)) >= a.threshold
        if a.invert:
            m = ~m
        v = v[m]
    v = v.ravel()
    q = np.quantile(v, [0.5, 0.9, 0.95, 0.99, 0.999])
    print("input in region: n=%d  p50 %.4f  p90 %.4f  p95 %.4f  p99 %.4f  p99.9 %.4f" % ((v.size,) + tuple(q)))
    if a.map:
        pts = [tuple(float(x) for x in t.split(":")) for t in a.targets]
        if len(pts) != 2:
            print("--map needs exactly two param:coverage pairs")
            return 2
        (p1, c1), (p2, c2) = pts
        y1, y2 = position_for(v, c1), position_for(v, c2)
        slope = (y2 - y1) / (p2 - p1)
        icpt = y1 - slope * p1
        print("Position(%s=%g) = %.4f for %.3g coverage; Position(%s=%g) = %.4f for %.3g" % (a.map, p1, y1, c1, a.map, p2, y2, c2))
        print('sdkit spec: ("add", %.5f, ("mul", ("get", "%s"), %.5f))' % (icpt, a.map, slope))
        return 0
    for t in a.targets:
        c = float(t)
        print("coverage %.4g -> Position %.4f" % (c, position_for(v, c)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
