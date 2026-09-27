"""Shared helpers for procedural flower rendering in Blender (bpy as a module).
Units: 1 Blender unit = 1 cm. Camera looks from -Y towards +Y, Z is up."""
import bpy, math, json, os
import numpy as np
from mathutils import Vector, Matrix

GOLD = math.radians(137.50776)
PPC = 30  # pixels per cm in final renders


# ---------------------------------------------------------------- scene
def reset_scene(samples=96):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.transmission_bounces = 6
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    try:
        sc.view_settings.view_transform = 'Khronos PBR Neutral'
    except Exception:
        pass
    sc.view_settings.exposure = 0.0
    sc.render.threads_mode = 'AUTO'

    # warm ivory ambient
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.98, 0.95, 0.90, 1)
    bg.inputs[1].default_value = 0.32

    def sun(name, rot, strength, angle, col=(1, 1, 1)):
        d = bpy.data.lights.new(name, 'SUN')
        d.energy = strength
        d.angle = math.radians(angle)
        d.color = col
        o = bpy.data.objects.new(name, d)
        o.rotation_euler = [math.radians(a) for a in rot]
        sc.collection.objects.link(o)

    # key: soft window light from upper-left front
    sun('key', (50, 0, -40), 3.4, 14, (1.0, 0.96, 0.90))
    # fill from right
    sun('fill', (72, 0, 50), 0.55, 30, (0.95, 0.97, 1.0))
    # rim from behind/top
    sun('rim', (-35, 0, 170), 1.4, 12, (1.0, 0.98, 0.94))
    return sc


# ---------------------------------------------------------------- mesh builder
class MB:
    def __init__(self):
        self.v, self.f, self.uv, self.aux = [], [], [], []

    def grid(self, P, U, V, aux=(0.0, 0.0), wrap=False):
        base = len(self.v)
        nu, nv = P.shape[:2]
        for i in range(nu):
            for j in range(nv):
                self.v.append(tuple(P[i, j]))
                self.uv.append((float(U[i]), float(V[j])))
                self.aux.append(aux)
        for i in range(nu - 1):
            for j in range(nv - 1):
                a = base + i * nv + j
                self.f.append((a, a + 1, a + nv + 1, a + nv))

    def build(self, name, mat, subsurf=0, coll=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        li = np.zeros(len(me.loops), dtype=np.int32)
        me.loops.foreach_get('vertex_index', li)
        l0 = me.uv_layers.new(name='UVMap')
        l0.data.foreach_set('uv', np.array(self.uv, dtype=np.float32)[li].ravel())
        l1 = me.uv_layers.new(name='Aux')
        l1.data.foreach_set('uv', np.array(self.aux, dtype=np.float32)[li].ravel())
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        if subsurf:
            m = ob.modifiers.new('ss', 'SUBSURF')
            m.levels = subsurf
            m.render_levels = subsurf
        return ob


def xform(P, M):
    """Apply 4x4 Matrix M to array (...,3)."""
    A = np.array(M)
    sh = P.shape
    Q = P.reshape(-1, 3) @ A[:3, :3].T + A[:3, 3]
    return Q.reshape(sh)


def Rz(a):
    return Matrix.Rotation(a, 4, 'Z')


def Ry(a):
    return Matrix.Rotation(a, 4, 'Y')


def Rx(a):
    return Matrix.Rotation(a, 4, 'X')


def T(v):
    return Matrix.Translation(Vector(v))


def align_z(d):
    """Rotation matrix taking +Z to direction d."""
    d = Vector(d).normalized()
    return Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()


def place(az, elev, pos=(0, 0, 0)):
    """Petal placement: petal local +X goes outward at azimuth az, raised by elev."""
    return T(pos) @ Rz(az) @ Ry(-elev)


# ---------------------------------------------------------------- petal
def petal(L, wfn, nu=14, nv=9, cup=0.0, bend=0.0, bend_p=1.5, reflex=0.0,
          ruffle=0.0, rfreq=3.0, rphase=0.0, twist=0.0, fold=0.0, rng=None,
          jitter=0.0, tip_notch=0.0):
    U = np.linspace(0, 1, nu)
    V = np.linspace(-1, 1, nv)
    ang = bend * U ** bend_p - reflex * np.clip((U - 0.55) / 0.45, 0, 1) ** 2
    ds = L / (nu - 1)
    x = np.zeros(nu)
    z = np.zeros(nu)
    for i in range(1, nu):
        x[i] = x[i - 1] + ds * math.cos(ang[i - 1])
        z[i] = z[i - 1] + ds * math.sin(ang[i - 1])
    P = np.zeros((nu, nv, 3))
    ph2 = rng.uniform(0, 6.28) if rng is not None else 0.0
    for i, u in enumerate(U):
        w = wfn(u)
        n = np.array([-math.sin(ang[i]), 0.0, math.cos(ang[i])])
        t = np.array([math.cos(ang[i]), 0.0, math.sin(ang[i])])
        for j, v in enumerate(V):
            y = v * w
            dz = cup * (v ** 2) * w
            dz += fold * abs(v) * w * (1 - u) * 0.5
            dz += ruffle * math.sin(rfreq * math.pi * v + rphase) * (u ** 2) * max(w, 0.2)
            dz += ruffle * 0.5 * math.sin(rfreq * 1.7 * math.pi * v + ph2) * (abs(v) ** 2) * u * max(w, 0.2)
            if jitter and rng is not None:
                dz += rng.normal(0, jitter) * u * abs(v)
            ta = twist * u
            yy = y * math.cos(ta) - dz * math.sin(ta)
            zz = y * math.sin(ta) + dz * math.cos(ta)
            # notch at tip centre
            dx = 0.0
            if tip_notch and u > 0.85:
                dx = -tip_notch * math.exp(-(v / 0.25) ** 2) * ((u - 0.85) / 0.15)
            P[i, j] = np.array([x[i], 0, z[i]]) + t * dx + np.array([0, 1.0, 0]) * yy + n * zz
    return P, U, (V + 1) / 2


def w_ovate(W, pw=0.6, tip=0.85, base=0.12):
    def f(u):
        if u <= tip:
            s = math.sin(math.pi / 2 * min(u / tip, 1.0)) ** pw
            return W * (base + (1 - base) * s)
        k = (u - tip) / (1 - tip)
        return W * math.sqrt(max(0.0, 1 - k * k)) + 1e-3
    return f


def w_lance(W, peak=0.35):
    def f(u):
        if u < peak:
            return W * math.sin(math.pi / 2 * u / peak) ** 0.7 + 0.02
        k = (u - peak) / (1 - peak)
        return W * (1 - k) ** 1.15 + 0.005
    return f


# ---------------------------------------------------------------- tube
def tube(mb, pts, radii, seg=12, aux=(0, 0), cap=False):
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tans = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tans.append((b - a).normalized())
    ref = Vector((1, 0, 0)) if abs(tans[0].x) < 0.9 else Vector((0, 1, 0))
    nrm = tans[0].cross(ref).normalized()
    P = np.zeros((n, seg + 1, 3))
    acc = 0.0
    U = []
    for i in range(n):
        if i > 0:
            # parallel transport
            q = tans[i - 1].rotation_difference(tans[i])
            nrm = (q @ nrm).normalized()
            acc += (pts[i] - pts[i - 1]).length
        U.append(acc)
        bn = tans[i].cross(nrm).normalized()
        for j in range(seg + 1):
            a = 2 * math.pi * j / seg
            p = pts[i] + radii[i] * (math.cos(a) * nrm + math.sin(a) * bn)
            P[i, j] = (p.x, p.y, p.z)
    U = np.array(U)
    U = U / max(U[-1], 1e-6)
    mb.grid(P, U, np.linspace(0, 1, seg + 1), aux=aux)
    if cap:
        c = len(mb.v)
        e = pts[-1]
        mb.v.append((e.x, e.y, e.z))
        mb.uv.append((1.0, 0.5))
        mb.aux.append(aux)
        base = c - (seg + 1)
        for j in range(seg):
            mb.f.append((base + j, base + j + 1, c))


def bezier(p0, p1, p2, p3, n=16):
    p0, p1, p2, p3 = map(np.array, (p0, p1, p2, p3))
    out = []
    for t in np.linspace(0, 1, n):
        out.append(((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    return out


# ---------------------------------------------------------------- materials
def _ramp(nt, cols):
    r = nt.nodes.new('ShaderNodeValToRGB')
    el = r.color_ramp.elements
    el[0].position, el[0].color = cols[0][0], (*cols[0][1], 1)
    el[1].position, el[1].color = cols[-1][0], (*cols[-1][1], 1)
    for p, c in cols[1:-1]:
        e = el.new(p)
        e.color = (*c, 1)
    return r


def mat_petal(name, cols, rough=0.5, transl=0.3, sheen=0.25, coat=0.0,
              bump=0.12, vein_scale=(3.0, 38.0), vein_amt=0.12, mottle=0.06,
              inner=None, inner_pow=2.0, inner_amt=0.6, var=0.06, hue_var=0.01,
              spec=0.35, blister=0.0, blister_scale=9.0, sss=0.0, back_tint=1.15,
              axis='X'):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    L = nt.links
    for n in list(N):
        N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    pr = N.new('ShaderNodeBsdfPrincipled')
    tr = N.new('ShaderNodeBsdfTranslucent')
    mix = N.new('ShaderNodeMixShader')
    uv = N.new('ShaderNodeUVMap'); uv.uv_map = 'UVMap'
    ax = N.new('ShaderNodeUVMap'); ax.uv_map = 'Aux'
    sep = N.new('ShaderNodeSeparateXYZ')
    sepa = N.new('ShaderNodeSeparateXYZ')
    L.new(uv.outputs['UV'], sep.inputs[0])
    L.new(ax.outputs['UV'], sepa.inputs[0])
    ramp = _ramp(nt, cols)
    L.new(sep.outputs[axis], ramp.inputs[0])
    col = ramp.outputs['Color']

    # veins: noise stretched along petal length
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (vein_scale[0], vein_scale[1], 1)
    L.new(uv.outputs['UV'], mp.inputs[0])
    vn = N.new('ShaderNodeTexNoise')
    vn.inputs['Scale'].default_value = 1.0
    vn.inputs['Detail'].default_value = 4.0
    vn.inputs['Roughness'].default_value = 0.55
    L.new(mp.outputs[0], vn.inputs['Vector'])
    # mottling
    mn = N.new('ShaderNodeTexNoise')
    mn.inputs['Scale'].default_value = 6.0
    mn.inputs['Detail'].default_value = 3.0
    L.new(uv.outputs['UV'], mn.inputs['Vector'])

    mixv = N.new('ShaderNodeMix'); mixv.data_type = 'RGBA'; mixv.blend_type = 'MULTIPLY'
    mixv.inputs['Factor'].default_value = vein_amt
    L.new(col, mixv.inputs['A'])
    L.new(vn.outputs['Color'], mixv.inputs['B'])
    col = mixv.outputs['Result']
    mixm = N.new('ShaderNodeMix'); mixm.data_type = 'RGBA'; mixm.blend_type = 'OVERLAY'
    mixm.inputs['Factor'].default_value = mottle
    L.new(col, mixm.inputs['A'])
    L.new(mn.outputs['Color'], mixm.inputs['B'])
    col = mixm.outputs['Result']

    if inner is not None:
        # blend towards inner colour for small aux.y (inner petals)
        inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        L.new(sepa.outputs['Y'], inv.inputs[1])
        pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = inner_pow
        L.new(inv.outputs[0], pw.inputs[0])
        mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = inner_amt
        L.new(pw.outputs[0], mul.inputs[0])
        # also stronger near petal base
        base = N.new('ShaderNodeMath'); base.operation = 'SUBTRACT'; base.inputs[0].default_value = 1.15
        L.new(sep.outputs['X'], base.inputs[1])
        mul2 = N.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'; mul2.use_clamp = True
        L.new(mul.outputs[0], mul2.inputs[0]); L.new(base.outputs[0], mul2.inputs[1])
        mi = N.new('ShaderNodeMix'); mi.data_type = 'RGBA'
        L.new(mul2.outputs[0], mi.inputs['Factor'])
        L.new(col, mi.inputs['A'])
        mi.inputs['B'].default_value = (*inner, 1)
        col = mi.outputs['Result']

    # per-piece random variation (aux.x)
    hsv = N.new('ShaderNodeHueSaturation')
    mr = N.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = 1 - var
    mr.inputs['To Max'].default_value = 1 + var
    L.new(sepa.outputs['X'], mr.inputs['Value'])
    L.new(mr.outputs['Result'], hsv.inputs['Value'])
    mh = N.new('ShaderNodeMapRange')
    mh.inputs['To Min'].default_value = 0.5 - hue_var
    mh.inputs['To Max'].default_value = 0.5 + hue_var
    L.new(sepa.outputs['X'], mh.inputs['Value'])
    L.new(mh.outputs['Result'], hsv.inputs['Hue'])
    L.new(col, hsv.inputs['Color'])
    col = hsv.outputs['Color']

    L.new(col, pr.inputs['Base Color'])
    pr.inputs['Roughness'].default_value = rough
    pr.inputs['Specular IOR Level'].default_value = spec
    pr.inputs['Sheen Weight'].default_value = sheen
    pr.inputs['Sheen Roughness'].default_value = 0.4
    pr.inputs['Coat Weight'].default_value = coat
    pr.inputs['Coat Roughness'].default_value = 0.14
    if sss:
        pr.inputs['Subsurface Weight'].default_value = sss
        pr.inputs['Subsurface Radius'].default_value = (0.3, 0.12, 0.08)
        pr.inputs['Subsurface Scale'].default_value = 0.05

    bright = N.new('ShaderNodeHueSaturation')
    bright.inputs['Value'].default_value = back_tint
    bright.inputs['Saturation'].default_value = 1.1
    L.new(col, bright.inputs['Color'])
    L.new(bright.outputs['Color'], tr.inputs['Color'])

    # bump
    bh = vn.outputs['Fac']
    if blister:
        vo = N.new('ShaderNodeTexVoronoi')
        vo.feature = 'SMOOTH_F1' if hasattr(vo, 'feature') else vo.feature
        vo.inputs['Scale'].default_value = blister_scale
        L.new(uv.outputs['UV'], vo.inputs['Vector'])
        add = N.new('ShaderNodeMath'); add.operation = 'MULTIPLY_ADD'
        L.new(vo.outputs['Distance'], add.inputs[0]); add.inputs[1].default_value = blister
        L.new(vn.outputs['Fac'], add.inputs[2])
        bh = add.outputs[0]
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.05
    L.new(bh, bp.inputs['Height'])
    L.new(bp.outputs['Normal'], pr.inputs['Normal'])
    L.new(bp.outputs['Normal'], tr.inputs['Normal'])

    mix.inputs[0].default_value = transl
    L.new(pr.outputs[0], mix.inputs[1])
    L.new(tr.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def mat_stem(name, cols, rough=0.55, sheen=0.1, coat=0.0, var=0.04):
    return mat_petal(name, cols, rough=rough, transl=0.08, sheen=sheen, coat=coat,
                     bump=0.06, vein_scale=(2.0, 60.0), vein_amt=0.12, mottle=0.08,
                     var=var, spec=0.4, axis='Y')


# ---------------------------------------------------------------- stem + neck
STEM_L = 30.0


def stem_with_neck(mb, head_pos, face, r0=0.35, r1=0.28, neck_back=0.2, seg=12):
    """Straight vertical stem from (0,0,-STEM_L) to (0,0,0), then a curved neck to the
    back of the head at head_pos (head faces `face`)."""
    face = np.array(face) / np.linalg.norm(face)
    end = np.array(head_pos) - face * neck_back
    k = np.linalg.norm(end) * 0.45
    neck = bezier((0, 0, 0), (0, 0, k), end - face * k, end, n=18)
    straight = [np.array((0, 0, -STEM_L + i * STEM_L / 20)) for i in range(20)]
    pts = straight + neck
    radii = [r0 - (r0 - r1) * (i / (len(pts) - 1)) ** 1.5 for i in range(len(pts))]
    tube(mb, pts, radii, seg=seg)


def head_matrix(pos, tilt, yaw=0.0, spin=0.0):
    """Head built facing +Z; tilt = elevation above horizontal of the face direction
    (towards camera, -Y)."""
    M = T(pos) @ Rz(yaw) @ Rx(math.radians(90) - tilt) @ Rz(spin)
    f = (M.to_3x3() @ Vector((0, 0, 1)))
    return M, np.array(f)


# ---------------------------------------------------------------- render + manifest
def render(outpath, key_points=None, margin=0.6, extra=None):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    xs, zs = [], []
    for ob in sc.objects:
        if ob.type != 'MESH':
            continue
        ev = ob.evaluated_get(dg)
        mw = ev.matrix_world
        for c in ev.bound_box:
            w = mw @ Vector(c)
            xs.append(w.x); zs.append(w.z)
    x0, x1 = min(xs) - margin, max(xs) + margin
    z0, z1 = min(zs) - margin, max(zs) + margin
    W, H = x1 - x0, z1 - z0
    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = max(W, H)
    cam_d.clip_end = 1000
    cam = bpy.data.objects.new('cam', cam_d)
    cam.location = ((x0 + x1) / 2, -200, (z0 + z1) / 2)
    cam.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x = int(round(W * PPC))
    sc.render.resolution_y = int(round(H * PPC))
    sc.render.resolution_percentage = 100
    sc.render.filepath = outpath
    bpy.ops.render.render(write_still=True)

    def px(p):
        return [round((p[0] - x0) * PPC, 1), round((z1 - p[2]) * PPC, 1)]
    meta = {'w': sc.render.resolution_x, 'h': sc.render.resolution_y, 'ppc': PPC,
            'stemX': px((0, 0, 0))[0], 'stemTopY': px((0, 0, 0))[1],
            'stemBottomY': px((0, 0, -STEM_L))[1]}
    if key_points:
        for k, p in key_points.items():
            meta[k] = px(p)
    if extra:
        meta.update(extra)
    return meta
