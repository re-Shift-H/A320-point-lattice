#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A320 点阵生成器 / A320 Point-Lattice Generator
================================================

Generates a structured point lattice (点阵) of an approximate Airbus A320-200
geometry, intended for CATIA surface lofting (multi-section surfaces / NURBS
skinning / "Mesh surface from cloud").

Outputs
-------
  - A320_point_lattice.xlsx   one sheet per component + a "Parameters" sheet
  - csv/<component>.csv       one CSV per component, for direct CATIA import

Coordinate system (CATIA absolute axis)
---------------------------------------
  - Origin O : nose tip, on the fuselage centreline (Y = 0), at the fuselage
               longitudinal axis height (Z = 0)
  - +X       : longitudinal, towards the tail
  - +Y       : lateral / spanwise, towards the STARBOARD (right) wing
  - +Z       : vertical, upwards
  - Units    : millimetres (mm)   [ 1 m = 1000 mm ]

Lattice structure
-----------------
Each sheet carries a `Station` index (longitudinal / spanwise / height direction)
and a `Section` index (around the cross-section or around the airfoil loop).
Connecting equal `Section` indices across successive `Station`s yields the guide
curves that CATIA can loft. `Side` is L/R/C where the component has two halves.

IMPORTANT
---------
All dimensions are representative public / approximate A320-200 values and are
NOT engineering or certified data. This is a coarse "outer mould line" reference
model for layout / visualisation / teaching purposes only.
"""

import os
import numpy as np
import pandas as pd

# ===========================================================================
# 1. Airfoil -- NACA 4-digit series, returned as a CLOSED loop
# ===========================================================================
def naca4(m, p, t, n=80):
    """Return a closed-loop NACA 4-digit airfoil in fraction-of-chord units.

    xi  : chordwise position, 0 (leading edge) .. 1 (trailing edge)
    eta : normal offset (camber + thickness), fraction of chord
    Loop order: TE(lower) -> LE -> TE(upper).  The same order is used at every
    station, so corresponding points can be connected across stations.
    """
    x = np.linspace(0.0, 1.0, n)               # chord stations LE -> TE
    # thickness distribution (closed trailing edge)
    yt = (t / 0.2) * (0.2969 * np.sqrt(x)
                      - 0.1260 * x
                      - 0.3516 * x ** 2
                      + 0.2843 * x ** 3
                      - 0.1015 * x ** 4)
    # camber mean line and its slope
    if m == 0.0 or p == 0.0:
        yc = np.zeros_like(x)
        dyc = np.zeros_like(x)
    else:
        front = x < p
        yc = np.where(front,
                      m / p ** 2 * (2.0 * p * x - x ** 2),
                      m / (1.0 - p) ** 2 * ((1.0 - 2.0 * p) + 2.0 * p * x - x ** 2))
        dyc = np.where(front,
                       2.0 * m / p ** 2 * (p - x),
                       2.0 * m / (1.0 - p) ** 2 * (p - x))
    th = np.arctan(dyc)
    xu = x - yt * np.sin(th);  yu = yc + yt * np.cos(th)
    xl = x + yt * np.sin(th);  yl = yc - yt * np.cos(th)
    # closed loop: TE lower -> LE -> TE upper
    xi = np.concatenate([xl[::-1], xu[1:]])
    eta = np.concatenate([yl[::-1], yu[1:]])
    return xi, eta


# ===========================================================================
# 2. Symmetric span-station helper (for wing / horizontal tail)
# ===========================================================================
def symmetric_span(y_root, half_span, n_st, include_center=False):
    """Return a list of (y, side) span stations, symmetric about the centreline."""
    if include_center:
        y_pos = np.linspace(y_root, half_span, n_st)   # starts at y_root (==0)
        pts = [(float(y_pos[0]), 'C')]
        pts += [(float(y), 'R') for y in y_pos[1:]]
        pts += [(-float(y), 'L') for y in y_pos[1:]]
    else:
        y_pos = np.linspace(y_root, half_span, n_st)
        pts = [(float(y), 'R') for y in y_pos]
        pts += [(-float(y), 'L') for y in y_pos]
    return pts


# ===========================================================================
# 3. Lifting-surface loft (wing-like): swept + tapered + dihedral
# ===========================================================================
def lofted_surface(span_pts, y_root, half_span, c_root, c_tip,
                   le_root_x, sweep_deg, dihedral_deg, z_root,
                   m, p, t, n_chord):
    """Build a structured lattice for a swept/tapered/dihedral lifting surface."""
    xi, eta = naca4(m, p, t, n_chord)
    th = np.radians(dihedral_deg)
    n_c = len(xi)

    Xs, Ys, Zs, st, sec, side = [], [], [], [], [], []
    for i, (y_s, s) in enumerate(span_pts):
        r = abs(y_s) - y_root                     # radial span position (>= 0)
        c = c_root + (c_tip - c_root) * r / (half_span - y_root)
        x_le = le_root_x + r * np.tan(np.radians(sweep_deg))
        z_ref = z_root + r * np.tan(th)           # dihedral raises both tips

        side_sign = +1.0 if s in ('R', 'C') else -1.0
        n_y = -side_sign * np.sin(th)             # section normal (inward)
        n_z = np.cos(th)

        X = x_le + xi * c
        Y = y_s + eta * c * n_y
        Z = z_ref + eta * c * n_z

        Xs.extend(X); Ys.extend(Y); Zs.extend(Z)
        st.extend([i] * n_c); sec.extend(range(n_c)); side.extend([s] * n_c)

    return Xs, Ys, Zs, st, sec, side


# ===========================================================================
# 4. Fuselage (body of revolution, elliptical cross-section)
# ===========================================================================
def fuselage(n_st=50, n_circ=32):
    # radius profile: (x_mm, half-width_mm)  -- nose -> tail
    ctrl = [
        (0.0, 40.0),      # nose tip
        (300, 150),
        (700, 380),
        (1200, 680),
        (1800, 980),
        (2600, 1260),
        (3600, 1520),
        (5000, 1740),
        (7000, 1900),
        (10000, 1970),
        (18000, 1975),    # max constant section
        (28000, 1975),
        (32000, 1960),
        (34500, 1880),
        (36000, 1680),
        (37000, 1350),
        (37400, 850),
        (37540, 300),
        (37570, 0.0),     # tail tip
    ]
    ctrl_x = np.array([c[0] for c in ctrl])
    ctrl_r = np.array([c[1] for c in ctrl])
    HR = 1.05             # cross-section height/width ratio (double-bubble-ish)

    xs = np.linspace(0.0, 37570.0, n_st)
    rs = np.interp(xs, ctrl_x, ctrl_r)
    th = np.linspace(0.0, 2.0 * np.pi, n_circ, endpoint=False)

    Xs, Ys, Zs, st, sec = [], [], [], [], []
    for i, (x, r) in enumerate(zip(xs, rs)):
        aY = r          # semi-width
        aZ = r * HR     # semi-height
        for j, a in enumerate(th):
            Xs.append(x)
            Ys.append(aY * np.cos(a))
            Zs.append(aZ * np.sin(a))
            st.append(i); sec.append(j)
    return Xs, Ys, Zs, st, sec


# ===========================================================================
# 5. Vertical tail / fin (symmetric airfoil sections stacked in height)
# ===========================================================================
def vertical_tail(n_st=10, n_chord=36):
    z_base = 1800.0      # fin base height (top of aft fuselage), mm
    height = 6200.0      # fin height
    c_root = 5600.0
    c_tip = 1700.0
    le_root_x = 30000.0
    sweep_deg = 40.0

    xi, eta = naca4(0.0, 0.0, 0.10, n_chord)   # NACA 0010, symmetric
    n_c = len(xi)

    zs = np.linspace(0.0, height, n_st)
    Xs, Ys, Zs, st, sec = [], [], [], [], []
    for i, h in enumerate(zs):
        c = c_root + (c_tip - c_root) * h / height
        x_le = le_root_x + h * np.tan(np.radians(sweep_deg))
        X = x_le + xi * c
        Y = eta * c            # thickness acts in the Y direction
        Z = np.full(n_c, z_base + h)
        Xs.extend(X); Ys.extend(Y); Zs.extend(Z)
        st.extend([i] * n_c); sec.extend(range(n_c))
    return Xs, Ys, Zs, st, sec


# ===========================================================================
# 6. Engine nacelle (body of revolution, CFM56-5B class)
# ===========================================================================
def nacelle(x0, y0, z0, n_len=20, n_circ=24):
    L = 3300.0
    ctrl_x = [0, 300, 700, 1300, 2000, 2600, 3100, 3300]
    ctrl_r = [985, 1005, 985, 950, 880, 760, 640, 600]
    xs = np.linspace(0.0, L, n_len)
    rs = np.interp(xs, ctrl_x, ctrl_r)
    th = np.linspace(0.0, 2.0 * np.pi, n_circ, endpoint=False)

    Xs, Ys, Zs, st, sec = [], [], [], [], []
    for i, (x, r) in enumerate(zip(xs, rs)):
        for j, a in enumerate(th):
            Xs.append(x0 + x)
            Ys.append(y0 + r * np.cos(a))
            Zs.append(z0 + r * np.sin(a))
            st.append(i); sec.append(j)
    return Xs, Ys, Zs, st, sec


# ===========================================================================
# 7. Build everything
# ===========================================================================
def build():
    sheets = {}   # name -> dict of column arrays

    # ---- Fuselage ---------------------------------------------------------
    X, Y, Z, st, sec = fuselage()
    sheets['Fuselage'] = dict(X=X, Y=Y, Z=Z, Station=st, Section=sec, Side=[''] * len(X))

    # ---- Wing (NACA 2412, swept + tapered + dihedral) ---------------------
    wing = dict(
        y_root=1975.0, half_span=17050.0, c_root=7400.0, c_tip=1400.0,
        le_root_x=11500.0, sweep_deg=25.0, dihedral_deg=5.1, z_root=-500.0,
        m=0.02, p=0.4, t=0.12, n_chord=44,
    )
    span = symmetric_span(wing['y_root'], wing['half_span'], 12)
    X, Y, Z, st, sec, side = lofted_surface(
        span, wing['y_root'], wing['half_span'], wing['c_root'], wing['c_tip'],
        wing['le_root_x'], wing['sweep_deg'], wing['dihedral_deg'], wing['z_root'],
        wing['m'], wing['p'], wing['t'], wing['n_chord'])
    sheets['Wing'] = dict(X=X, Y=Y, Z=Z, Station=st, Section=sec, Side=side)

    # ---- Horizontal tail (NACA 0012) --------------------------------------
    ht = dict(
        y_root=0.0, half_span=6225.0, c_root=3000.0, c_tip=1050.0,
        le_root_x=33500.0, sweep_deg=30.0, dihedral_deg=0.0, z_root=1600.0,
        m=0.0, p=0.0, t=0.12, n_chord=34,
    )
    span = symmetric_span(ht['y_root'], ht['half_span'], 9, include_center=True)
    X, Y, Z, st, sec, side = lofted_surface(
        span, ht['y_root'], ht['half_span'], ht['c_root'], ht['c_tip'],
        ht['le_root_x'], ht['sweep_deg'], ht['dihedral_deg'], ht['z_root'],
        ht['m'], ht['p'], ht['t'], ht['n_chord'])
    sheets['H_Tail'] = dict(X=X, Y=Y, Z=Z, Station=st, Section=sec, Side=side)

    # ---- Vertical tail (fin) ---------------------------------------------
    X, Y, Z, st, sec = vertical_tail()
    sheets['V_Tail'] = dict(X=X, Y=Y, Z=Z, Station=st, Section=sec, Side=[''] * len(X))

    # ---- Engine nacelles (two, under each wing) ---------------------------
    y_eng = 5750.0                       # engine spanwise centreline
    # wing geometry at the engine span station (to hang the nacelle below the wing)
    r = y_eng - wing['y_root']
    c_eng = wing['c_root'] + (wing['c_tip'] - wing['c_root']) * r / (wing['half_span'] - wing['y_root'])
    x_le_eng = wing['le_root_x'] + r * np.tan(np.radians(wing['sweep_deg']))
    z_ref_eng = wing['z_root'] + r * np.tan(np.radians(wing['dihedral_deg']))
    R_nac = 1005.0
    nac_z = z_ref_eng - 950.0                        # engine centreline ~0.95 m below wing chord line
    x0 = x_le_eng + 0.5 * c_eng - 1650.0             # nacelle mid-length at mid-chord

    for sgn, side in ((+1.0, 'R'), (-1.0, 'L')):
        X, Y, Z, st, sec = nacelle(x0, sgn * y_eng, nac_z)
        # merge into single Engine sheet, prefixing Station by side block
        if side == 'R':
            XE, YE, ZE, stE, secE, sideE = X, Y, Z, st, sec, [side] * len(X)
        else:
            XE += X; YE += Y; ZE += Z
            stE += [i + 20 for i in st]   # keep L/R stations distinct
            secE += sec; sideE += [side] * len(X)
    sheets['Engine'] = dict(X=XE, Y=YE, Z=ZE, Station=stE, Section=secE, Side=sideE)

    return sheets


def to_dataframes(sheets):
    """Convert raw arrays to tidy DataFrames (columns rounded to 0.01 mm)."""
    out = {}
    for name, d in sheets.items():
        n = len(d['X'])
        df = pd.DataFrame({
            'ID': np.arange(1, n + 1),
            'Station': d['Station'],
            'Section': d['Section'],
            'Side': d['Side'],
            'X': np.round(d['X'], 2),
            'Y': np.round(d['Y'], 2),
            'Z': np.round(d['Z'], 2),
        })
        out[name] = df
    return out


PARAMETERS = [
    ("Fuselage length", 37570, "37.57 m"),
    ("Fuselage max width", 3950, "3.95 m"),
    ("Fuselage max height", 4140, "4.14 m"),
    ("Wingspan", 34100, "34.10 m (standard wingtip fence)"),
    ("Wing root chord", 7400, "7.40 m"),
    ("Wing tip chord", 1400, "1.40 m"),
    ("Wing LE sweep", 25.0, "deg (approx.)"),
    ("Wing dihedral", 5.1, "deg (approx.)"),
    ("Horizontal tail span", 12450, "12.45 m"),
    ("Vertical tail height", 6200, "6.20 m"),
    ("Nacelle max diameter", 2010, "2.01 m"),
    ("Engine spanwise position", 11500, "5.75 m from centreline, each side"),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sheets = build()
    frames = to_dataframes(sheets)

    # Excel workbook
    xlsx = os.path.join(here, 'A320_point_lattice.xlsx')
    with pd.ExcelWriter(xlsx, engine='openpyxl') as w:
        params = pd.DataFrame([
            {"Dimension": d, "Value (mm)": v, "Value (m)": u} for d, v, u in PARAMETERS
        ])
        params.to_excel(w, sheet_name='Parameters', index=False)
        for name in ['Fuselage', 'Wing', 'H_Tail', 'V_Tail', 'Engine']:
            frames[name].to_excel(w, sheet_name=name, index=False)

    # CSVs
    csv_dir = os.path.join(here, 'csv')
    os.makedirs(csv_dir, exist_ok=True)
    for name, df in frames.items():
        df.to_csv(os.path.join(csv_dir, name + '.csv'), index=False)

    print("Generated A320 point lattice:")
    total = 0
    for name in ['Fuselage', 'Wing', 'H_Tail', 'V_Tail', 'Engine']:
        n = len(frames[name])
        total += n
        print(f"  {name:<10} {n:>6} points")
    print(f"  {'TOTAL':<10} {total:>6} points")
    print(f"\nWrote: {xlsx}")
    print(f"       {csv_dir}")


if __name__ == '__main__':
    main()
