import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from lib import *

C = lambda *a: tuple(a)

STEM_GREEN = [(0.0, C(0.065, 0.12, 0.028)), (0.5, C(0.085, 0.15, 0.038)), (1.0, C(0.075, 0.135, 0.032))]


# =============================================================== DAHLIA
def dahlia(rng, tilt, yaw, spin, scale=1.0):
    mat = mat_petal('dahlia',
                    [(0.0, C(0.66, 0.50, 0.22)), (0.22, C(0.86, 0.73, 0.56)),
                     (0.65, C(0.92, 0.83, 0.69)), (1.0, C(0.93, 0.86, 0.74))],
                    rough=0.55, transl=0.38, sheen=0.35, bump=0.1, vein_scale=(2.5, 30),
                    vein_amt=0.10, mottle=0.05, inner=C(0.86, 0.56, 0.48), inner_pow=1.5,
                    inner_amt=0.8, var=0.05, hue_var=0.012)
    mb = MB()
    N = 170
    for i in range(N):
        t = (i + 0.5) / N
        az = i * GOLD + rng.normal(0, 0.05)
        Lp = (0.7 + 4.5 * t ** 0.85) * rng.uniform(0.92, 1.06) * scale
        W = (0.30 + 0.95 * t ** 0.9) * rng.uniform(0.9, 1.1) * scale
        elev = math.radians(88 - 96 * t ** 0.85 + rng.normal(0, 4))
        bend = 1.5 * (1 - t) ** 1.4 - 0.25 * t ** 2
        cup = (0.55 + 0.35 * (1 - t)) * rng.uniform(0.8, 1.15)
        r0 = (0.15 + 0.9 * t ** 1.2) * scale
        z0 = (0.9 * (1 - t) ** 2 - 0.2 * t) * scale
        P, U, V = petal(Lp, w_ovate(W, pw=0.55, tip=0.8, base=0.15), nu=13, nv=11, cup=cup,
                        bend=bend, reflex=0.35 * t ** 3, ruffle=0.05 * t, rfreq=2.0,
                        rphase=rng.uniform(0, 6), rng=rng, jitter=0.02, tip_notch=0.08 * W * t)
        M = place(az, elev, (r0 * math.cos(az), r0 * math.sin(az), z0))
        mb.grid(xform(P, M), U, V, aux=(rng.uniform(0, 1), t))
    # green bracts behind
    mbg = MB()
    for k in range(8):
        az = k * 2 * math.pi / 8 + rng.normal(0, 0.1)
        P, U, V = petal(1.6 * scale, w_ovate(0.55 * scale, tip=0.7), nu=8, nv=7, cup=0.3, bend=-0.4, rng=rng)
        M = place(az, math.radians(-35), (0.4 * math.cos(az), 0.4 * math.sin(az), -0.35))
        mbg.grid(xform(P, M), U, V, aux=(rng.uniform(0, 1), 1))
    pos = (0, -2.2, 5.0)
    H, f = head_matrix(pos, tilt, yaw, spin)
    ob = mb.build('dahlia', mat, subsurf=1)
    ob.matrix_world = H
    g = mbg.build('bracts', mat_petal('bract', [(0, C(0.07, 0.13, 0.03)), (1, C(0.10, 0.17, 0.045))], rough=0.5, transl=0.15, sheen=0.1))
    g.matrix_world = H
    ms = MB()
    stem_with_neck(ms, pos, f, r0=0.42, r1=0.4, neck_back=0.3)
    ms.build('stem', mat_stem('st', STEM_GREEN))
    return {'head': pos, 'headR': 5.6 * scale}


# =============================================================== ANTHURIUM
def anthurium(rng, tilt, yaw, spin, scale=1.0):
    mat = mat_petal('anth', [(0.0, C(0.075, 0.003, 0.012)), (0.45, C(0.13, 0.006, 0.02)), (1.0, C(0.115, 0.005, 0.018))],
                    rough=0.3, transl=0.0, sheen=0.0, coat=0.4, bump=0.22, vein_scale=(1.2, 14), vein_amt=0.06,
                    mottle=0.05, var=0.06, spec=0.5, blister=0.6, blister_scale=13, back_tint=1.6)
    keys = [(0, 1.0), (20, 0.9), (45, 0.76), (80, 0.63), (110, 0.575), (135, 0.56), (152, 0.52), (165, 0.38), (174, 0.2), (180, 0.1)]
    ka = np.radians([k[0] for k in keys]); kr = np.array([k[1] for k in keys])
    Ls = 10.5 * scale * rng.uniform(0.93, 1.05)
    ns, nt = 24, 90
    S = np.linspace(0, 1, ns)
    TH = np.linspace(-math.pi, math.pi, nt)
    P = np.zeros((ns, nt, 3))
    for i, s in enumerate(S):
        for j, th in enumerate(TH):
            r = s * np.interp(abs(th), ka, kr) * Ls
            x, y = r * math.cos(th), r * math.sin(th)
            z = -0.045 * x * x / Ls + 0.035 * y * y / Ls
            z += -0.5 * max(0.0, x / Ls - 0.55) ** 2 * Ls
            z += 0.05 * Ls * math.exp(-(r / (0.18 * Ls)) ** 2)
            # impressed curving veins
            z -= 0.035 * math.exp(-((math.sin(3.2 * th + 0.8 * s)) / 0.18) ** 2) * s * (1 - s) * 4
            P[i, j] = (x, y, z)
    mb = MB()
    mb.grid(P, S, (TH + math.pi) / (2 * math.pi), aux=(rng.uniform(0, 1), 1))
    # spadix: rises from the attachment point, up (-X) and out of the face (+Z)
    msp = MB()
    Lsp = 5.2 * scale
    curve = bezier((0, 0, 0.1), (-0.15 * Lsp, 0, 0.45 * Lsp), (-0.55 * Lsp, 0.05 * Lsp, 0.75 * Lsp), (-0.85 * Lsp, 0.1 * Lsp, 0.8 * Lsp), n=24)
    rad = [0.42 * scale * (1 - 0.5 * (k / 23) ** 1.2) for k in range(24)]
    rad[-1] = 0.06
    tube(msp, curve, rad, seg=18, aux=(rng.uniform(0, 1), 1), cap=True)
    spmat = mat_petal('spadix', [(0.0, C(0.30, 0.06, 0.06)), (0.3, C(0.66, 0.46, 0.20)), (1.0, C(0.80, 0.68, 0.30))],
                      rough=0.6, transl=0.05, sheen=0.3, bump=0.6, vein_scale=(4, 4), vein_amt=0.15, mottle=0.1,
                      blister=1.0, blister_scale=70, axis='X')
    side = rng.uniform(-0.55, 0.55)
    tipd = Vector((math.sin(side), -0.5, -math.cos(side))).normalized()
    face0 = Vector((0, -1, 0.3))
    face = (face0 - face0.dot(tipd) * tipd).normalized()
    yv = face.cross(tipd)
    R = Matrix((tipd, yv, face)).transposed().to_4x4()
    pos = (0, -0.6, 2.2)
    M = T(pos) @ Rz(yaw) @ R
    ob = mb.build('spathe', mat, subsurf=1); ob.matrix_world = M
    sp = msp.build('spadix', spmat, subsurf=1); sp.matrix_world = M
    f = np.array(M.to_3x3() @ Vector((0, 0, 1)))
    ms = MB()
    stem_with_neck(ms, pos, f, r0=0.34, r1=0.28, neck_back=0.2)
    ms.build('stem', mat_stem('st', [(0, C(0.06, 0.12, 0.025)), (1, C(0.08, 0.15, 0.035))], coat=0.25, rough=0.35))
    td = np.array(M.to_3x3() @ Vector((1, 0, 0)))
    center = np.array(pos) + td * Ls * 0.42
    return {'head': tuple(center), 'headR': Ls * 0.55}


# =============================================================== CAMPANULA
def bell_mesh(mb, rng, H=4.0, Rr=1.8, aux=(0, 1), closed=0.0):
    nu, nv = 22, 75
    off = rng.uniform(0, 1)
    P = np.zeros((nu, nv, 3))
    Hs = np.linspace(0, 1, nu)
    Ph = np.linspace(0, 2 * math.pi, nv)
    for i, h in enumerate(Hs):
        for j, ph in enumerate(Ph):
            lobe = (0.5 + 0.5 * math.cos(5 * (ph + off))) ** 3
            hh = h * (1 + 0.13 * lobe * h ** 3)
            r = 0.32 + (Rr - 0.32) * (hh ** 1.35)
            r *= 1 + 0.05 * math.cos(5 * (ph + off) + math.pi) * math.sin(math.pi * h)
            fl = max(0.0, (hh - 0.78) / 0.35)
            r += (0.55 * Rr * fl ** 2) * (0.55 + 0.45 * lobe) * (1 - closed)
            z = H * hh - 0.35 * H * fl ** 2.2 * (1 - closed) * (0.5 + 0.5 * lobe)
            if closed:
                r *= (1 - closed * 0.55 * h ** 1.5)
            r *= 1 + rng.normal(0, 0.004)
            P[i, j] = (r * math.cos(ph), r * math.sin(ph), z)
    mb.grid(P, Hs, Ph / (2 * math.pi), aux=aux)


def campanula(rng, tilt, yaw, spin, scale=1.0):
    bell_mat = mat_petal('bell', [(0.0, C(0.30, 0.20, 0.50)), (0.25, C(0.17, 0.05, 0.42)),
                                  (0.7, C(0.14, 0.035, 0.38)), (1.0, C(0.17, 0.045, 0.42))],
                         rough=0.5, transl=0.45, sheen=0.4, bump=0.12, vein_scale=(2.0, 55), vein_amt=0.2,
                         mottle=0.05, var=0.06, hue_var=0.015, back_tint=1.25)
    bud_mat = mat_petal('bud', [(0.0, C(0.09, 0.16, 0.04)), (0.5, C(0.16, 0.10, 0.25)), (1.0, C(0.15, 0.05, 0.36))],
                        rough=0.5, transl=0.3, sheen=0.2)
    green = mat_petal('cgreen', [(0, C(0.06, 0.12, 0.025)), (1, C(0.09, 0.16, 0.04))], rough=0.5, transl=0.2, sheen=0.1)
    white = mat_petal('style', [(0, C(0.85, 0.85, 0.75)), (1, C(0.95, 0.94, 0.88))], rough=0.6, transl=0.3)
    mbb, mbu, mbg, mbw, ms = MB(), MB(), MB(), MB(), MB()
    top = 13.0 * scale
    # main stem continues up above z=0 with a slight curve
    lean = rng.normal(0, 0.8)
    stem_pts = [np.array((0, 0, -STEM_L + i * STEM_L / 20)) for i in range(20)]
    stem_pts += bezier((0, 0, 0), (0, 0, top * 0.4), (lean * 0.5, -0.3, top * 0.75), (lean, -0.5, top), n=20)
    tube(ms, stem_pts, [0.26 - 0.1 * (k / 39) for k in range(40)], seg=10)

    def stem_at(z):
        if z <= 0:
            return np.array((0, 0, z))
        u = min(z / top, 1)
        return np.array((lean * u ** 2, -0.5 * u ** 2, z))

    nb = rng.integers(3, 5)
    zs = sorted(rng.uniform(0.5, 0.78, nb) * top)
    head_pts = []
    side = rng.choice([-1, 1])
    for k, z in enumerate(zs):
        side = -side
        base = stem_at(z)
        az = math.radians(-90 + side * rng.uniform(25, 70))  # outward, biased to camera
        el = math.radians(rng.uniform(5, 35))
        d = np.array((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        ped = 1.4 * scale
        end = base + d * ped + np.array((0, 0, 0.3))
        tube(ms, bezier(base, base + np.array((0, 0, 0.5)), end - d * 0.4, end, n=8), [0.12] * 8, seg=8)
        fdir = d + np.array((0, 0, rng.uniform(-0.1, 0.4)))
        fdir = fdir / np.linalg.norm(fdir)
        H = 4.2 * scale * rng.uniform(0.9, 1.08)
        mbl = MB()
        bell_mesh(mbl, rng, H=H, Rr=1.75 * scale * rng.uniform(0.9, 1.08), aux=(rng.uniform(0, 1), 1))
        M = T(end) @ align_z(fdir) @ Rz(rng.uniform(0, 6.3))
        for idx, fc in enumerate(mbl.f):
            pass
        mbb.grid(xform(np.array(mbl.v).reshape(22, 75, 3), M), np.linspace(0, 1, 22), np.linspace(0, 1, 75),
                 aux=(rng.uniform(0, 1), 1))
        head_pts.append(end + fdir * H * 0.5)
        # style + stigma
        tube(mbw, [end + fdir * s for s in np.linspace(0.2, H * 0.72, 6)], [0.07] * 6, seg=6)
        tip = end + fdir * H * 0.72
        for q in range(3):
            a = q * 2 * math.pi / 3
            perp = np.cross(fdir, (0, 0, 1) if abs(fdir[2]) < 0.9 else (1, 0, 0))
            perp /= np.linalg.norm(perp)
            perp2 = np.cross(fdir, perp)
            o = perp * math.cos(a) + perp2 * math.sin(a)
            tube(mbw, bezier(tip, tip + fdir * 0.2 + o * 0.15, tip + o * 0.4, tip + o * 0.35 - fdir * 0.2, n=6), [0.05] * 6, seg=6)
        # calyx
        for q in range(5):
            P, U, V = petal(1.2 * scale, w_lance(0.22 * scale), nu=8, nv=5, cup=0.2, bend=-0.3, rng=rng)
            mm = T(end) @ align_z(fdir) @ place(q * 2 * math.pi / 5, math.radians(-10), (0.25, 0, 0.2))
            mbg.grid(xform(P, mm), U, V, aux=(rng.uniform(0, 1), 1))
    # buds at tip
    for k in range(rng.integers(1, 3)):
        z = top * (0.86 + 0.12 * k)
        base = stem_at(min(z, top))
        d = np.array((rng.normal(0, 0.4), -0.3, 1.0)); d /= np.linalg.norm(d)
        mbl = MB()
        bell_mesh(mbl, rng, H=1.8 * scale, Rr=0.7 * scale, closed=0.85)
        M = T(base) @ align_z(d)
        mbu.grid(xform(np.array(mbl.v).reshape(22, 75, 3), M), np.linspace(0, 1, 22), np.linspace(0, 1, 75),
                 aux=(rng.uniform(0, 1), 1))
    # leaves along the stem
    for k in range(4):
        z = rng.uniform(-3, top * 0.5)
        base = stem_at(z)
        az = rng.uniform(0, 2 * math.pi)
        P, U, V = petal(3.2 * scale, w_lance(0.45 * scale), nu=12, nv=7, cup=0.3, bend=-0.5, rng=rng, ruffle=0.03, rfreq=5)
        mbg.grid(xform(P, place(az, math.radians(40), base)), U, V, aux=(rng.uniform(0, 1), 1))
    mbb.build('bells', bell_mat, subsurf=1)
    mbu.build('buds', bud_mat, subsurf=1)
    mbg.build('green', green, subsurf=1)
    mbw.build('style', white)
    ms.build('stem', mat_stem('st', STEM_GREEN))
    hp = np.mean(head_pts, axis=0)
    return {'head': tuple(hp), 'headR': 4.5 * scale, 'top': (lean, -0.5, top)}


# =============================================================== HYDRANGEA
def hydrangea(rng, tilt, yaw, spin, scale=1.0):
    mat = mat_petal('hyd', [(0.0, C(0.30, 0.45, 0.13)), (0.35, C(0.58, 0.70, 0.36)), (0.8, C(0.74, 0.81, 0.54)), (1.0, C(0.82, 0.86, 0.66))],
                    rough=0.5, transl=0.4, sheen=0.3, bump=0.1, vein_scale=(3, 25), vein_amt=0.14, mottle=0.06,
                    var=0.09, hue_var=0.025, back_tint=1.2)
    cmat = mat_petal('hydc', [(0, C(0.30, 0.40, 0.12)), (1, C(0.55, 0.62, 0.30))], rough=0.6, transl=0.2)
    mb, mbc = MB(), MB()
    R = 7.2 * scale
    n = 300
    cap = math.radians(84)
    for k in range(n):
        t = (k + 0.5) / n
        cp = 1 - t * (1 - math.cos(cap))
        sp = math.sqrt(1 - cp * cp)
        ph = k * GOLD
        nrm = np.array((sp * math.cos(ph), sp * math.sin(ph), cp * 0.85))
        nrm /= np.linalg.norm(nrm)
        jitter = rng.normal(0, 0.18)
        pos = nrm * (R + jitter) * np.array((1.0, 1.0, 0.72)) + np.array((0, 0, -R * 0.25))
        d = nrm + rng.normal(0, 0.18, 3)
        d /= np.linalg.norm(d)
        Mf = T(pos) @ align_z(d) @ Rz(rng.uniform(0, 6.3))
        s = rng.uniform(0.95, 1.4) * scale
        a = rng.uniform(0, 1)
        nsep = 4 if rng.uniform() > 0.12 else 5
        for q in range(nsep):
            az = q * 2 * math.pi / nsep + rng.normal(0, 0.15)
            Ls = s * rng.uniform(0.85, 1.15)
            P, U, V = petal(Ls, w_ovate(0.55 * Ls, pw=0.5, tip=0.62, base=0.1), nu=8, nv=7,
                            cup=rng.uniform(-0.05, 0.25), bend=rng.uniform(-0.2, 0.3),
                            ruffle=0.03, rfreq=2, rphase=rng.uniform(0, 6), rng=rng)
            mb.grid(xform(P, Mf @ place(az, math.radians(rng.uniform(0, 22)), (0, 0, 0.05))), U, V, aux=(a, 1))
        # tiny centre bud
        cb = MB()
        tube(cb, [(0, 0, 0), (0, 0, 0.12), (0, 0, 0.22)], [0.1, 0.1, 0.02], seg=6)
        mbc.grid(xform(np.array(cb.v).reshape(3, 7, 3), Mf), np.linspace(0, 1, 3), np.linspace(0, 1, 7), aux=(a, 1))
    # leaves under the head
    lmat = mat_petal('hleaf', [(0, C(0.03, 0.07, 0.015)), (0.6, C(0.045, 0.095, 0.02)), (1, C(0.04, 0.085, 0.018))],
                     rough=0.45, transl=0.15, sheen=0.05, coat=0.15, bump=0.3, vein_scale=(6, 6), vein_amt=0.15, blister=0.4, blister_scale=14)
    ml = MB()
    for k, az in enumerate([math.radians(-160), math.radians(-25)]):
        Lf = 10 * scale * rng.uniform(0.9, 1.05)

        def wl(u, Lf=Lf):
            b = 0.30 * Lf * math.sin(math.pi * min(u, 0.999) ** 0.8) ** 0.75 + 0.01
            return b * (1 - 0.035 * ((u * 26) % 1.0))
        P, U, V = petal(Lf, wl, nu=24, nv=13, cup=0.12, bend=-0.3, fold=0.5, ruffle=0.06, rfreq=3, rng=rng)
        ml.grid(xform(P, place(az + rng.normal(0, 0.1), math.radians(-5), (0, 0, -R * 0.5))), U, V, aux=(rng.uniform(0, 1), 1))
    pos = (0, -2.0, 6.5)
    H, f = head_matrix(pos, tilt, yaw, spin)
    ob = mb.build('hyd', mat, subsurf=0); ob.matrix_world = H
    oc = mbc.build('hydc', cmat); oc.matrix_world = H
    ol = ml.build('leaves', lmat, subsurf=1); ol.matrix_world = H
    ms = MB()
    stem_with_neck(ms, np.array(pos) - f * (R * 0.5), f, r0=0.55, r1=0.45, neck_back=0.1)
    ms.build('stem', mat_stem('st', [(0, C(0.28, 0.32, 0.14)), (1, C(0.32, 0.36, 0.16))]))
    return {'head': pos, 'headR': R * 1.05}


# =============================================================== EUSTOMA
def eustoma_head(mb, rng, open_=1.0, scale=1.0):
    whorls = [(6, 4.6, 2.2, 26, 0.35, 0.26, 0.0), (5, 4.0, 1.9, 46, 0.55, 0.2, 0.25), (5, 3.1, 1.5, 64, 0.9, 0.14, 0.5),
              (4, 2.2, 1.05, 78, 1.35, 0.08, 0.8)]
    for wi, (n, Lp, W, el, bend, ruf, ti) in enumerate(whorls):
        off = rng.uniform(0, 6.3)
        for q in range(n):
            az = off + q * 2 * math.pi / n + rng.normal(0, 0.1)
            Ls = Lp * scale * rng.uniform(0.9, 1.07)
            P, U, V = petal(Ls, w_ovate(W * scale * rng.uniform(0.9, 1.1), pw=0.8, tip=0.72, base=0.18), 
                            cup=0.25 + 0.2 * wi, bend=bend, twist=0.25, ruffle=ruf * scale, rfreq=5.5, nu=16, nv=15,
                            rphase=rng.uniform(0, 6), rng=rng, jitter=0.03)
            r0 = 0.3 + 0.1 * (3 - wi)
            mb.grid(xform(P, place(az, math.radians(el + rng.normal(0, 4)), (r0 * math.cos(az), r0 * math.sin(az), 0.15 * wi))),
                    U, V, aux=(rng.uniform(0, 1), ti))


def eustoma(rng, tilt, yaw, spin, scale=1.0):
    mat = mat_petal('eus', [(0.0, C(0.22, 0.34, 0.08)), (0.15, C(0.58, 0.66, 0.38)), (0.36, C(0.89, 0.88, 0.77)),
                            (0.85, C(0.93, 0.92, 0.83)), (1.0, C(0.87, 0.89, 0.74))],
                    rough=0.45, transl=0.42, sheen=0.35, bump=0.1, vein_scale=(2.5, 40), vein_amt=0.1, mottle=0.04,
                    inner=C(0.55, 0.66, 0.32), inner_pow=2.0, inner_amt=0.35, var=0.04, hue_var=0.01)
    bmat = mat_petal('eusb', [(0.0, C(0.12, 0.22, 0.05)), (0.6, C(0.40, 0.50, 0.20)), (1.0, C(0.68, 0.72, 0.50))],
                     rough=0.45, transl=0.3, sheen=0.3)
    gmat = mat_petal('eusg', [(0, C(0.08, 0.15, 0.07)), (1, C(0.12, 0.20, 0.10))], rough=0.35, transl=0.15, sheen=0.4, spec=0.5)
    mb, mbb, mbg, ms = MB(), MB(), MB(), MB()
    eustoma_head(mb, rng, scale=scale)
    for q in range(5):
        P, U, V = petal(1.4 * scale, w_lance(0.12 * scale), nu=8, nv=5, bend=0.3, rng=rng)
        mbg.grid(xform(P, place(q * 1.2566, math.radians(55), (0.2, 0, -0.3))), U, V, aux=(0.5, 1))
    pos = (0, -1.8, 4.2)
    H, f = head_matrix(pos, tilt, yaw, spin)
    o = mb.build('eus', mat, subsurf=1); o.matrix_world = H
    og = mbg.build('sep', gmat); og.matrix_world = H
    stem_with_neck(ms, pos, f, r0=0.28, r1=0.22, neck_back=0.35)
    # side branch with twisted bud
    side = rng.choice([-1, 1])
    b0 = np.array((0, 0, -4.0))
    bdir = np.array((side * 0.55, -0.35, 1.0)); bdir /= np.linalg.norm(bdir)
    b1 = b0 + bdir * 5.5 * scale
    tube(ms, bezier(b0, b0 + np.array((0, 0, 1.5)), b1 - bdir * 1.5, b1, n=12), [0.18 - 0.05 * k / 11 for k in range(12)], seg=8)
    for q in range(5):
        P, U, V = petal(3.6 * scale, w_lance(0.62 * scale, peak=0.4), nu=14, nv=7, cup=0.5, bend=0.55, twist=0.9, rng=rng)
        mbb.grid(xform(P, T(b1) @ align_z(bdir) @ place(q * 1.2566 + 0.3, math.radians(80), (0.12, 0, 0))), U, V, aux=(rng.uniform(0, 1), 1))
    for q in range(5):
        P, U, V = petal(1.2 * scale, w_lance(0.1 * scale), nu=6, nv=5, bend=0.2, rng=rng)
        mbg.grid(xform(P, T(b1) @ align_z(bdir) @ place(q * 1.2566, math.radians(70), (0.15, 0, -0.1))), U, V, aux=(0.5, 1))
    # glaucous leaves
    for k, (z, az) in enumerate([(-7.0, 0.3), (-7.0, math.pi + 0.3), (-10.5, 1.9)]):
        P, U, V = petal(5.0 * scale, w_ovate(1.2 * scale, pw=0.6, tip=0.55, base=0.4), nu=14, nv=9, cup=0.35, bend=-0.4, rng=rng)
        mbg.grid(xform(P, place(az + rng.normal(0, 0.2), math.radians(45), (0, 0, z))), U, V, aux=(rng.uniform(0, 1), 1))
    mbb.build('bud', bmat, subsurf=1)
    mbg.build('green', gmat, subsurf=1)
    ms.build('stem', mat_stem('st', [(0, C(0.08, 0.15, 0.06)), (1, C(0.10, 0.18, 0.08))], sheen=0.4))
    return {'head': pos, 'headR': 4.6 * scale}


# =============================================================== TWINE
def twine(rng):
    m = mat_petal('twine', [(0, C(0.40, 0.30, 0.17)), (1, C(0.50, 0.38, 0.23))], rough=0.85, transl=0.05, sheen=0.6,
                  bump=0.8, vein_scale=(90, 8), vein_amt=0.25, mottle=0.12, var=0.05)
    mb = MB()
    Rb, turns, hgt = 1.45, 5, 1.6
    for t_ in range(turns):
        pts, rad = [], []
        for a in np.linspace(math.pi * 1.02, math.pi * 1.98, 26):
            z = hgt / 2 - (t_ + (a - math.pi) / (2 * math.pi)) * hgt / turns + rng.normal(0, 0.01)
            rr = Rb + 0.02 * math.sin(a * 3 + t_)
            pts.append((rr * math.cos(a), rr * math.sin(a), z))
            rad.append(0.15)
        tube(mb, pts, rad, seg=10, aux=(rng.uniform(0, 1), 1))
    # knot + loose ends
    k = np.array((0.25, -Rb - 0.12, -0.1))
    tube(mb, bezier(k, k + np.array((0.25, -0.35, 0.15)), k + np.array((0.55, -0.2, -0.3)), k + np.array((0.2, -0.1, -0.05)), n=12), [0.14] * 12, seg=10)
    for dx, L_ in [(-0.3, 4.6), (0.4, 3.8)]:
        tube(mb, bezier(k, k + np.array((dx * 0.8, -0.35, -1.0)), k + np.array((dx * 2.5, -0.25, -L_ * 0.6)), k + np.array((dx * 3.2, -0.2, -L_)), n=24),
             [0.14] * 23 + [0.1], seg=10, aux=(rng.uniform(0, 1), 1))
    mb.build('twine', m, subsurf=1)
    return {}


FLOWERS = {'dahlia': dahlia, 'anthurium': anthurium, 'campanula': campanula,
           'hydrangea': hydrangea, 'eustoma': eustoma, 'twine': twine}

if __name__ == '__main__':
    kind, variant, seed, outdir = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    samples = int(sys.argv[5]) if len(sys.argv) > 5 else 96
    tilt = math.radians(float(sys.argv[6])) if len(sys.argv) > 6 else math.radians(35)
    yaw = math.radians(float(sys.argv[7])) if len(sys.argv) > 7 else 0.0
    rng = np.random.default_rng(seed)
    reset_scene(samples)
    if kind == 'twine':
        # twine has no stem; fake manifest
        twine(rng)
        meta = render(os.path.join(outdir, f'{kind}-{variant}.png'), key_points={'center': (0, 0, 0)})
    else:
        info = FLOWERS[kind](rng, tilt, yaw, rng.uniform(0, 6.28))
        meta = render(os.path.join(outdir, f'{kind}-{variant}.png'), key_points={'head': info['head']},
                      extra={'headR': round(info['headR'] * PPC, 1)})
    with open(os.path.join(outdir, f'{kind}-{variant}.json'), 'w') as fh:
        json.dump(meta, fh)
    print('META', json.dumps(meta))
