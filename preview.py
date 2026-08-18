#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render a quick shaded preview of the A320 point-lattice mesh (A320.obj)
as a PNG, so the complete model can be checked without opening a CAD tool.

Requires matplotlib (pip install matplotlib).
"""
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def load_obj(path):
    verts, faces = [], []
    with open(path) as f:
        for line in f:
            p = line.split()
            if not p:
                continue
            if p[0] == 'v':
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif p[0] == 'f':
                faces.append([int(q.split('/')[0]) - 1 for q in p[1:4]])
    return np.array(verts), faces


def main():
    verts, faces = load_obj('A320.obj')
    v = verts / 1000.0  # mm -> m

    fig = plt.figure(figsize=(15, 6.5))
    ax = fig.add_subplot(111, projection='3d')
    polys = [[v[i] for i in tri] for tri in faces]
    coll = Poly3DCollection(polys, facecolor='#7fb2d9', edgecolor='none', alpha=0.95)
    ax.add_collection3d(coll)

    ax.set_xlim(v[:, 0].min(), v[:, 0].max())
    ax.set_ylim(v[:, 1].min(), v[:, 1].max())
    ax.set_zlim(v[:, 2].min(), v[:, 2].max())
    ax.set_box_aspect((np.ptp(v[:, 0]), np.ptp(v[:, 1]), np.ptp(v[:, 2])))
    ax.view_init(elev=18, azim=-62)
    ax.set_xlabel('X (m) - tail ->'); ax.set_ylabel('Y (m) - right'); ax.set_zlabel('Z (m)')
    ax.set_title('A320 point-lattice model (approximate)')
    plt.tight_layout()
    plt.savefig('preview.png', dpi=110)
    print('saved preview.png  (%d verts, %d triangles)' % (len(verts), len(faces)))


if __name__ == '__main__':
    main()
