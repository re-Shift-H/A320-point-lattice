#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the A320 point lattice inside CATIA V5 via COM automation.

Requirements
------------
  - Windows + CATIA V5 (tested against R32 / V5-6R2022)
  - pywin32    ( pip install pywin32 )

What it does
------------
  1. Connects to a running CATIA, or launches it (visible); closes stale parts.
  2. Creates a new Part.
  3. For each component CSV in ./csv : creates a Geometrical Set and imports
     every point as a coordinate point (HybridShapePointCoord) -- the 点阵.
  4. Builds closed splines (cross-section rings) + open splines (spanwise /
     longitudinal guides) so the lattice is visible as a wireframe.
  5. Creates a multi-section loft surface per (component, side).

Run
---
  python build_in_catia.py
"""

import os
import time

import win32com.client

HERE = os.path.dirname(os.path.abspath(__file__))
COMPONENTS = ['Fuselage', 'Wing', 'Winglet', 'H_Tail', 'V_Tail', 'Engine']


def log(msg):
    print(msg, flush=True)


def connect_catia():
    try:
        catia = win32com.client.GetActiveObject('CATIA.Application')
        log('[1/6] Connected to a running CATIA instance.')
    except Exception:
        log('[1/6] Launching CATIA (~30-60 s, may ask for a license) ...')
        catia = win32com.client.Dispatch('CATIA.Application')
        log('[1/6] CATIA launched.')
    catia.Visible = True
    try:
        catia.DisplayFileAlerts = False
    except Exception:
        pass
    return catia


def close_existing_parts(catia):
    try:
        n = catia.Documents.Count
        for i in range(n, 0, -1):
            try:
                catia.Documents.Item(i).Close()
            except Exception:
                pass
    except Exception:
        pass


def load_structured(name):
    rows = []
    with open(os.path.join(HERE, 'csv', name + '.csv')) as f:
        f.readline()  # header
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = line.split(',')
            rows.append(dict(
                station=int(p[1]), section=int(p[2]), side=p[3],
                x=float(p[4]), y=float(p[5]), z=float(p[6]),
            ))
    return rows


def group_rings(rows):
    rings = {}
    for r in rows:
        rings.setdefault((r['side'], r['station']), []).append(r)
    for k in rings:
        rings[k].sort(key=lambda r: r['section'])
    return rings


def group_guides(rows):
    guides = {}
    for r in rows:
        guides.setdefault((r['side'], r['section']), []).append(r)
    for k in guides:
        guides[k].sort(key=lambda r: r['station'])
    return guides


def main():
    catia = connect_catia()
    log('[2/6] Closing stale parts ...')
    close_existing_parts(catia)

    log('[2/6] Creating a new Part ...')
    doc = catia.Documents.Add('Part')
    part = doc.Part
    hsf = part.HybridShapeFactory

    total_pts = total_rings = total_guides = total_lofts = 0
    t0 = time.time()

    for name in COMPONENTS:
        log('\n[3/6] Importing %s ...' % name)
        rows = load_structured(name)
        hb = part.HybridBodies.Add()
        hb.Name = name

        # ---- points (the lattice) ----
        pts = {}
        for i, r in enumerate(rows):
            pt = hsf.AddNewPointCoord(r['x'], r['y'], r['z'])
            hb.AppendHybridShape(pt)
            pts[(r['side'], r['station'], r['section'])] = pt
            total_pts += 1
            if (i + 1) % 1000 == 0:
                log('    ... %d points (%.0f s)' % (i + 1, time.time() - t0))

        # ---- closed rings (cross-sections) ----
        ring_refs = {}
        for (side, station), ring_rows in group_rings(rows).items():
            # drop a trailing duplicate point (closed airfoil loops have TE == TE)
            r0, r1 = ring_rows[0], ring_rows[-1]
            d = ((r0['x'] - r1['x']) ** 2 + (r0['y'] - r1['y']) ** 2
                 + (r0['z'] - r1['z']) ** 2) ** 0.5
            use = ring_rows[:-1] if d < 1.0 else ring_rows
            if len(use) < 3:
                continue
            try:
                sp = hsf.AddNewSpline()
                sp.SetSplineType(0)       # cubic
                sp.SetClosing(1)          # closed
                for r in use:
                    sp.AddPoint(part.CreateReferenceFromObject(
                        pts[(side, station, r['section'])]))
                hb.AppendHybridShape(sp)
                ring_refs[(side, station)] = part.CreateReferenceFromObject(sp)
                total_rings += 1
            except Exception as e:
                log('    [warn] ring side=%s station=%d: %s' % (side, station, e))

        # ---- open guides (spanwise / longitudinal) ----
        for (side, section), g_rows in group_guides(rows).items():
            if len(g_rows) < 3:
                continue
            try:
                sp = hsf.AddNewSpline()
                sp.SetSplineType(0)
                sp.SetClosing(0)
                for r in g_rows:
                    sp.AddPoint(part.CreateReferenceFromObject(
                        pts[(side, r['station'], section)]))
                hb.AppendHybridShape(sp)
                total_guides += 1
            except Exception as e:
                log('    [warn] guide side=%s section=%d: %s' % (side, section, e))

        # ---- multi-section loft surface per side ----
        for side in sorted({k[0] for k in ring_refs}):
            section_refs = [ring_refs[k] for k in sorted(ring_refs) if k[0] == side]
            if len(section_refs) < 2:
                continue
            try:
                loft = hsf.AddNewLoft()
                for sr in section_refs:
                    loft.AddSectionToLoft(sr, 1, None)
                hb.AppendHybridShape(loft)
                total_lofts += 1
                log('    [loft] side=%s -> surface (%d sections)'
                    % (side, len(section_refs)))
            except Exception as e:
                log('    [warn] loft side=%s: %s' % (side, e))

        log('    %s done: %d points' % (name, len(rows)))

    log('\n[4/6] Updating part ...')
    try:
        part.Update()
        log('    update OK')
    except Exception as e:
        log('    [warn] part.Update failed: %s' % e)

    log('[5/6] Fitting view ...')
    try:
        catia.StartCommand('Fit All In')
    except Exception as e:
        log('    [warn] Fit All In failed: %s' % e)

    log('\n[6/6] DONE in %.0f s' % (time.time() - t0))
    log('  points : %d' % total_pts)
    log('  rings  : %d' % total_rings)
    log('  guides : %d' % total_guides)
    log('  lofts  : %d' % total_lofts)
    log('  The part is on screen (untitled CATPart). Save it from CATIA.')


if __name__ == '__main__':
    main()
