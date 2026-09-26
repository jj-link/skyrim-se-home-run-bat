"""Generate the original Home Run Bat, its SSE NIF, DDS textures and Blender source.

Run with Windows Python 3.13 plus Pillow and NumPy:
    python tools/build_bat.py --fetch-exporter

The pinned PyNifly release is fetched from its official upstream into .local only.
Creation Kit's installed xtexconv writes desktop BC1/BC3 DDS with full mip chains;
Blender runs headlessly to save an editable scene and render an inspection image.
No installed-game files are modified and no vanilla assets are used by this tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".local" / "art-tools"
SOURCE = ROOT / "assets" / "model"
MESH = ROOT / "Data" / "Meshes" / "HomeRunBat" / "HomeRunBat.nif"
TEXTURES = ROOT / "Data" / "Textures" / "HomeRunBat"
EXPORTER = CACHE / "pynifly" / "io_scene_nifly"
RELEASE = "https://github.com/BadDogSkyrim/PyNifly/releases/download/V28.3.0/io_scene_nifly.zip"
RELEASE_SHA256 = "d879ca2fd9477f40bb7ea8a017d59ba83eaf35bd845ac776461f6896678bed43"
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition")
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")
HAVOK_SCALE = 69.99125
SEGMENTS = 64
SIZE = 2048
SIDE_V = 0.875
# NIF units, +Y along the barrel. The two-hand grip surrounds the weapon origin.
# This matches the coordinate convention of the game's greatsword animation set.
PROFILE = [
    (-22.0, 2.35), (-21.8, 2.65), (-21.4, 2.8), (-20.4, 2.8),
    (-19.9, 2.55), (-19.4, 1.85), (-18.8, 1.62), (-17.0, 1.55),
    (-5.0, 1.58), (4.0, 1.62), (8.0, 1.69), (10.0, 1.73),
    (17.0, 2.0), (25.0, 2.65), (34.0, 3.38), (42.0, 3.88),
    (49.0, 4.2), (65.0, 4.2), (70.0, 4.19), (73.0, 4.03),
    (75.0, 3.76), (76.5, 3.25), (77.3, 2.62), (77.8, 1.8), (78.0, 0.9),
]
# Three original convex pieces retain the narrow handle and overhanging knob.
# Radial profiles are concave functions of Y, so every plane bounds its hull.
COLLISION = [
    [(-22.0, 2.35), (-21.5, 2.8), (-20.4, 2.8), (-19.0, 1.6)],
    [(-19.1, 1.63), (8.2, 1.72)],
    [(8.0, 1.72), (40.0, 3.85), (49.0, 4.2), (70.0, 4.2),
     (73.0, 4.03), (75.0, 3.76), (76.5, 3.25), (77.3, 2.62),
     (77.8, 1.8), (78.0, 0.9)],
]


def exporter(fetch: bool):
    if not (EXPORTER / "NiflyDLL.dll").is_file():
        if not fetch:
            raise RuntimeError("Missing local PyNifly. Run again with --fetch-exporter.")
        CACHE.mkdir(parents=True, exist_ok=True)
        archive = CACHE / "io_scene_nifly-V28.3.0.zip"
        urllib.request.urlretrieve(RELEASE, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != RELEASE_SHA256:
            raise RuntimeError("Upstream PyNifly archive checksum mismatch")
        with zipfile.ZipFile(archive) as package:
            package.extractall(EXPORTER.parent)
    sys.path.insert(0, str(EXPORTER))
    from pyn import pynifly
    return pynifly


def geometry():
    vertices, normals, uvs, triangles = [], [], [], []
    for row, (y, radius) in enumerate(PROFILE):
        before = PROFILE[max(0, row - 1)]
        after = PROFILE[min(len(PROFILE) - 1, row + 1)]
        slope = (after[1] - before[1]) / (after[0] - before[0])
        normal_scale = math.sqrt(1.0 + slope * slope)
        for col in range(SEGMENTS + 1):
            angle = math.tau * col / SEGMENTS
            cosine, sine = math.cos(angle), math.sin(angle)
            vertices.append((radius * cosine, y, radius * sine))
            normals.append((cosine / normal_scale, -slope / normal_scale, sine / normal_scale))
            uvs.append((col / SEGMENTS, (78.0 - y) / 100.0 * SIDE_V))
        if row:
            for col in range(SEGMENTS):
                a = (row - 1) * (SEGMENTS + 1) + col
                b = a + SEGMENTS + 1
                triangles.extend(((a, b, a + 1), (a + 1, b, b + 1)))
    for end, center_u in ((0, 0.25), (-1, 0.75)):
        y, radius = PROFILE[end]
        sign = -1.0 if end == 0 else 1.0
        center = len(vertices)
        vertices.append((0.0, y, 0.0))
        normals.append((0.0, sign, 0.0))
        uvs.append((center_u, 0.94))
        for col in range(SEGMENTS):
            angle = math.tau * col / SEGMENTS
            cosine, sine = math.cos(angle), math.sin(angle)
            vertices.append((radius * cosine, y, radius * sine))
            normals.append((0.0, sign, 0.0))
            uvs.append((center_u + cosine * 0.05, 0.94 + sine * 0.05))
        for col in range(SEGMENTS):
            a, b = center + 1 + col, center + 1 + (col + 1) % SEGMENTS
            triangles.append((center, a, b) if end == 0 else (center, b, a))
    return {"vertices": vertices, "normals": normals, "uvs": uvs, "triangles": triangles}


def paint_textures():
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter

    # Deterministic ash grain: wandering growth bands, finer vessels and pores.
    rng = np.random.default_rng(271828)
    v, u = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32) / SIZE
    y = 78.0 - v / SIDE_V * 100.0
    phase = u * 19 + 0.42 * np.sin(v * 10) + 0.16 * np.sin(v * 27 + u * math.tau)
    wave = np.sin(phase * math.tau)
    bands = np.maximum(0, wave) ** 10
    fine = np.sin((u * 179 + 0.2 * np.sin(v * 31) + wave * 0.4) * math.tau)
    fibers = np.maximum(0, fine) ** 20
    noise = rng.normal(0, 1.3, (SIZE, SIZE)).astype(np.float32)
    variation = -bands * 15 - fibers * 6 + noise + 4 * np.sin(phase * math.pi)
    color = np.stack((181 + variation, 132 + variation * 0.84, 77 + variation * 0.62), axis=-1)
    height = -bands * 0.13 - fibers * 0.06 + noise * 0.002
    specular = np.full((SIZE, SIZE), 72, dtype=np.float32)

    grip = (y > -18.5) & (y < 7.5)
    spiral = ((y + 18.5) / 3.6 - u) % 1.0
    seam = np.exp(-((spiral - 0.055) / 0.034) ** 2)
    fabric = np.sin(u * math.tau * 420) * np.sin(v * math.tau * 690)
    wear = 4 * np.sin(u * math.tau * 3 + y * 0.1) + 3 * np.cos(y * 0.63)
    grip_color = np.stack((51 + wear - 19 * seam + noise, 42 + wear * 0.8 - 16 * seam + noise,
                           31 + wear * 0.6 - 12 * seam + noise), axis=-1)
    color[grip] = grip_color[grip]
    height[grip] = (-seam * 0.23 + fabric * 0.018)[grip]
    specular[grip] = 24
    # Narrow bindings and edge wear keep the wrap restrained, not a metal hilt.
    for edge in (-18.0, 7.0):
        binding = abs(y - edge) < 0.35
        color[binding] = np.array((87, 67, 42)) + noise[binding, None]
        height[binding] += 0.12

    for cu in (0.25, 0.75):
        dx, dy = (u - cu) / 0.05, (v - 0.94) / 0.05
        radius = np.sqrt(dx * dx + dy * dy)
        rings = np.sin(radius * 37 + 0.8 * np.sin(np.arctan2(dy, dx) * 3))
        region = (abs(u - cu) < 0.065) & (v > 0.879)
        cap = np.stack((167 + rings * 11, 117 + rings * 9, 67 + rings * 6), axis=-1)
        color[region] = cap[region]
        height[region] = rings[region] * 0.08

    image = Image.fromarray(np.clip(color, 0, 255).astype(np.uint8), "RGB")
    # Original geometric lettering; no font dependency or third-party artwork.
    glyphs = {
        "H": ["101", "101", "111", "101", "101"],
        "O": ["111", "101", "101", "101", "111"],
        "M": ["10001", "11011", "10101", "10001", "10001"],
        "E": ["111", "100", "110", "100", "111"],
        "R": ["110", "101", "110", "101", "101"],
        "U": ["101", "101", "101", "101", "111"],
        "N": ["1001", "1101", "1011", "1001", "1001"],
    }
    stamp = Image.new("L", (440, 180))
    draw = ImageDraw.Draw(stamp)
    draw.ellipse((8, 8, 431, 171), outline=160, width=5)
    draw.ellipse((18, 18, 421, 161), outline=110, width=2)
    scale = 7
    for text, top in (("HOME", 42), ("RUN", 101)):
        width = sum(len(glyphs[c][0]) + 1 for c in text) * scale - scale
        left = (440 - width) // 2
        for char in text:
            for row, line in enumerate(glyphs[char]):
                for col, bit in enumerate(line):
                    if bit == "1":
                        draw.rectangle((left + col * scale, top + row * scale,
                                        left + (col + 1) * scale - 2, top + (row + 1) * scale - 2), fill=185)
            left += (len(glyphs[char][0]) + 1) * scale
    stamp = stamp.filter(ImageFilter.GaussianBlur(0.55))
    # Two opposite faces, positioned on the full-width barrel (about Y=57).
    for center in (SIZE // 4, 3 * SIZE // 4):
        ink = Image.new("RGB", stamp.size, (55, 33, 15))
        image.paste(ink, (center - 220, 285), stamp)
    image.save(SOURCE / "HomeRunBat.png")

    # Tangent-space DirectX normal; alpha carries Skyrim's specular mask.
    dv, du = np.gradient(height)
    normal = np.stack((-du * 3, -dv * 3, np.ones_like(du)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    rgba = np.concatenate((normal * 127.5 + 127.5, specular[..., None]), axis=-1)
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA").save(SOURCE / "HomeRunBat_n.png")


def collision_hull(profile, sides=12):
    vertices = []
    for y, radius in profile:
        for col in range(sides):
            a = math.tau * col / sides
            vertices.append((radius * math.cos(a) / HAVOK_SCALE, y / HAVOK_SCALE,
                             radius * math.sin(a) / HAVOK_SCALE))
    planes = [(0, -1, 0, profile[0][0] / HAVOK_SCALE),
              (0, 1, 0, -profile[-1][0] / HAVOK_SCALE)]
    apothem = math.cos(math.pi / sides)
    for (y0, r0), (y1, r1) in zip(profile, profile[1:]):
        slope = (r1 - r0) / (y1 - y0) * apothem
        scale = math.sqrt(1 + slope * slope)
        distance = -(r0 * apothem - slope * y0) / HAVOK_SCALE / scale
        for col in range(sides):
            a = math.tau * (col + 0.5) / sides
            planes.append((math.cos(a) / scale, -slope / scale, math.sin(a) / scale, distance))
    # A malformed supporting plane makes a Havok convex shape invalid.
    assert all(sum(p[i] * v[i] for i in range(3)) + p[3] < 1e-6 for p in planes for v in vertices)
    return vertices, planes


def mass_properties():
    import numpy as np
    # Integrate thin disks of the actual wood profile in Havok units.
    sample_y = np.linspace(PROFILE[0][0], PROFILE[-1][0], 4096)
    radius = np.interp(sample_y, [p[0] for p in PROFILE], [p[1] for p in PROFILE]) / HAVOK_SCALE
    positions = sample_y / HAVOK_SCALE
    mass = 4.0
    weights = radius * radius
    weights *= mass / weights.sum()
    center = float(np.sum(weights * positions) / mass)
    transverse = float(np.sum(weights * (radius * radius / 4 + (positions - center) ** 2)))
    axial = float(np.sum(weights * radius * radius / 2))
    return mass, center, transverse, axial


def write_nif(nifly, mesh):
    from pyn.nifdefs import NiShapeBuf, PynBufferTypes, bhkRigidBodyProps, bhkListShapeProps, bhkConvexVerticesShapeProps
    from pyn.nifconstants import BSXFlagsValues, ShaderFlags1, ShaderFlags2, SkyrimHavokMaterial

    nif = nifly.NifFile()
    nif.initialize("SKYRIMSE", str(MESH), root_type="BSFadeNode", root_name="HomeRunBat")
    nif.root.flags = 524302
    # A rotationally symmetric bat needs no -X/-Z authoring rotation baked into its root.
    nifly.BSXFlags.New(nif, flags=BSXFlagsValues.HAVOC | BSXFlagsValues.DYNAMIC | BSXFlagsValues.ARTICULATED, parent=nif.root)
    nifly.BSInvMarker.New(nif, rotation=(1570, 0, 3141), zoom=1.15, parent=nif.root)
    nifly.NiStringExtraData.New(nif, name="Prn", string_value="WeaponBack", parent=nif.root)
    props = NiShapeBuf()
    props.bufType = PynBufferTypes.BSTriShapeBufType
    props.flags = 524302
    props.hasVertices = props.hasNormals = props.hasUV = 1
    # Use the half-precision vertex layout of native Skyrim SE weapons.
    props.hasFullPrecision = 0
    shape = nif.createShapeFromData("HomeRunBat_WoodAndGrip", mesh["vertices"], mesh["triangles"],
                                    mesh["uvs"], mesh["normals"], props=props, parent=nif.root)
    shader = shape.shader.properties
    shader.Shader_Type = 0
    shader.Shader_Flags_1 = int(ShaderFlags1.SPECULAR | ShaderFlags1.RECEIVE_SHADOWS | ShaderFlags1.CAST_SHADOWS | ShaderFlags1.ZBUFFER_TEST)
    shader.Shader_Flags_2 = int(ShaderFlags2.ZBUFFER_WRITE)
    shader.Glossiness = 18.0
    shader.Spec_Str = 0.32
    shader.Spec_Color = (0.85, 0.77, 0.65)
    shader.Alpha = 1.0
    shader.Emissive_Mult = 0.0
    shader.UV_Scale_U = shader.UV_Scale_V = 1.0
    shape.save_shader_attributes()
    shape.set_texture("Diffuse", r"textures\HomeRunBat\HomeRunBat.dds")
    shape.set_texture("Normal", r"textures\HomeRunBat\HomeRunBat_n.dds")

    collision = nif.root.add_collision(None, flags=129)
    body = bhkRigidBodyProps()
    body.collisionFilter_layer = body.collisionFilterCopy_layer = 5  # WEAPON
    body.worldObjCapFlags = 0x80000000
    body.rotation = (0, 0, 0, 1)
    body.mass, cy, transverse, axial = mass_properties()
    body.center = (0, cy, 0, 0)
    body.inertiaMatrix = (transverse, 0, 0, 0, 0, axial, 0, 0, 0, 0, transverse, 0)
    body.motionSystem = 3  # SPHERE_STABILIZED, also used by stock dropped weapons
    body.qualityType = 4  # MOVING
    body.solverDeactivation = 2
    body.penetrationDepth = 0.016
    body.restitution = 0.18
    body.friction = 0.6
    body.rollingFrictionMult = 0.0
    body.collisionResponse2 = 1
    body.processContactCallbackDelay2 = 65535
    body.numShapeKeysInContactPointProps = 3
    rigid_body = collision.add_body(body)
    group_props = bhkListShapeProps()
    group_props.bhkMaterial = SkyrimHavokMaterial.WOOD
    group_props.childShape_flags = group_props.childFilter_flags = 0x80000000
    group = nif.add_shape(group_props, parent=rigid_body)
    for profile in COLLISION:
        vertices, planes = collision_hull(profile)
        hull = bhkConvexVerticesShapeProps()
        hull.bhkMaterial = SkyrimHavokMaterial.WOOD
        hull.bhkRadius = 0.002
        hull.verticesProp_flags = hull.normalsProp_flags = 0x80000000
        nif.add_shape(hull, parent=group, vertices=vertices, normals=planes)
    nif.save()
    if nifly.NifFile.message_log():
        raise RuntimeError(nifly.NifFile.message_log())

    # PyNifly 28.3 recalculates an approximate sphere in saveNif and its shape
    # setter ignores explicit bounds. Finalize this single-shape metadata after
    # export; require a unique exact match and validate with the DLL reader below.
    exported = nifly.NifFile(str(MESH))
    bounds = exported.shapes[0].properties
    old = struct.pack("<4f", *bounds.boundingSphereCenter, bounds.boundingSphereRadius)
    center = (0.0, 28.0, 0.0)
    radius = max(math.dist(v, center) for v in mesh["vertices"]) + 0.001
    data = MESH.read_bytes()
    if data.count(old) != 1:
        raise RuntimeError("Cannot uniquely identify the exported bat bounding sphere")
    MESH.write_bytes(data.replace(old, struct.pack("<4f", *center, radius), 1))


def inspect_nif(nifly):
    nif = nifly.NifFile(str(MESH))
    assert nif.root.get_extra_data(name="Prn").string_data == "WeaponBack"
    assert nif.game == "SKYRIMSE" and nif.root.blockname == "BSFadeNode"
    assert len(nif.shapes) == 1
    shape = nif.shapes[0]
    assert shape.blockname == "BSTriShape"
    bounds = [[min(v[i] for v in shape.verts), max(v[i] for v in shape.verts)] for i in range(3)]
    assert all(abs(a - b) < 0.01 for got, expected in zip(bounds, ((-4.2, 4.2), (-22, 78), (-4.2, 4.2))) for a, b in zip(got, expected))
    sphere_center = list(shape.properties.boundingSphereCenter)
    sphere_radius = shape.properties.boundingSphereRadius
    assert all(math.dist(v, sphere_center) <= sphere_radius for v in shape.verts)
    assert shape.textures["Diffuse"] == r"textures\HomeRunBat\HomeRunBat.dds"
    assert shape.textures["Normal"] == r"textures\HomeRunBat\HomeRunBat_n.dds"
    assert all(math.isfinite(x) for v in shape.verts for x in v)
    assert all(len(set(t)) == 3 for t in shape.tris)
    collision = nif.root.collision_object
    assert collision.flags == 129
    body = collision.body
    assert body.properties.collisionFilter_layer == 5 and body.properties.motionSystem == 3
    assert body.properties.mass == 4 and body.properties.qualityType == 4
    children = body.shape.children
    assert len(children) == 3
    hulls = []
    for child in children:
        assert child.blockname == "bhkConvexVerticesShape"
        assert child.properties.bhkMaterial == 500811281
        assert len(child.vertices) >= 24 and len(child.normals) >= 14
        hulls.append({"vertices": len(child.vertices), "planes": len(child.normals)})
    report = {"game": nif.game, "root": nif.root.blockname, "shape": shape.blockname,
              "vertices": len(shape.verts), "triangles": len(shape.tris), "bounds": bounds,
              "bounding_sphere": {"center": sphere_center, "radius": sphere_radius},
              "textures": shape.textures, "collision": {"body": body.blockname, "mass": body.properties.mass,
              "layer": body.properties.collisionFilter_layer, "motion": body.properties.motionSystem,
              "quality": body.properties.qualityType, "hulls": hulls}}
    print(json.dumps(report, indent=2))
    return report


def write_dds(converter):
    from PIL import Image
    for name, format_ in (("HomeRunBat", "BC1_UNORM"), ("HomeRunBat_n", "BC3_UNORM")):
        output = TEXTURES / f"{name}.dds"
        output.unlink(missing_ok=True)
        subprocess.run([str(converter), "-nologo", "-f", format_, "-m", "0", "-sepalpha", "-o", str(TEXTURES),
                        str(SOURCE / f"{name}.png")], check=True)
        # CK's converter emits uppercase .DDS; keep release paths consistently lowercase.
        generated = TEXTURES / f"{name}.DDS"
        generated.rename(output)
        header = output.read_bytes()[:128]
        assert header[:4] == b"DDS "
        assert struct.unpack_from("<III", header, 12)[:2] == (SIZE, SIZE)
        assert struct.unpack_from("<I", header, 28)[0] == 12
        assert header[84:88] == (b"DXT1" if format_ == "BC1_UNORM" else b"DXT5")
        with Image.open(output) as texture:
            texture.load()
            assert texture.size == (SIZE, SIZE)
        print(f"{output.relative_to(ROOT)}: {SIZE}x{SIZE}, {format_}, 12 mip levels, decoded with Pillow")


def blender_scene():
    import bpy
    from mathutils import Vector

    mesh_data = json.loads((CACHE / "bat-scene.json").read_text())
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mesh = bpy.data.meshes.new("Original turned ash bat")
    mesh.from_pydata(mesh_data["vertices"], [], mesh_data["triangles"])
    mesh.update()
    uv = mesh.uv_layers.new(name="Bat atlas")
    for face in mesh.polygons:
        face.use_smooth = True
        for loop in face.loop_indices:
            u, v = mesh_data["uvs"][mesh.loops[loop].vertex_index]
            uv.data[loop].uv = (u, 1 - v)
    mesh.normals_split_custom_set_from_vertices(mesh_data["normals"])
    bat = bpy.data.objects.new("HomeRunBat", mesh)
    bpy.context.collection.objects.link(bat)
    bat["NIF axis"] = "+Y barrel; grip at origin; units exported 1:1"
    bat["Havok units"] = HAVOK_SCALE
    material = bpy.data.materials.new("Oiled ash and worn brown grip")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.46
    diffuse = nodes.new("ShaderNodeTexImage")
    diffuse.image = bpy.data.images.load(str(SOURCE / "HomeRunBat.png"))
    diffuse.image.filepath = "//HomeRunBat.png"
    links.new(diffuse.outputs["Color"], shader.inputs["Base Color"])
    normal = nodes.new("ShaderNodeTexImage")
    normal.image = bpy.data.images.load(str(SOURCE / "HomeRunBat_n.png"))
    normal.image.filepath = "//HomeRunBat_n.png"
    normal.image.colorspace_settings.name = "Non-Color"
    # DirectX Y must be inverted for Blender's OpenGL tangent basis.
    invert = nodes.new("ShaderNodeVectorMath")
    invert.operation = "MULTIPLY_ADD"
    invert.inputs[1].default_value = (1, -1, 1)
    invert.inputs[2].default_value = (0, 1, 0)
    normal_map = nodes.new("ShaderNodeNormalMap")
    links.new(normal.outputs["Color"], invert.inputs[0])
    links.new(invert.outputs["Vector"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    bat.data.materials.append(material)
    collision_collection = bpy.data.collections.new("Havok collision source - 3 convex hulls")
    bpy.context.scene.collection.children.link(collision_collection)
    for index, profile in enumerate(COLLISION):
        points, _ = collision_hull(profile)
        hull_mesh = bpy.data.meshes.new(f"CollisionHull{index}")
        hull_mesh.from_pydata([tuple(c * HAVOK_SCALE for c in v) for v in points], [], [])
        hull_mesh.update()
        obj = bpy.data.objects.new(f"bhkConvexVerticesShape_{index}", hull_mesh)
        collision_collection.objects.link(obj)
        obj.hide_render = True
        obj.hide_set(True)
        obj["material"] = "WOOD"
        obj["radius"] = 0.002
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.world.color = (0.12, 0.12, 0.12)
    camera_data = bpy.data.cameras.new("Asset inspection")
    camera = bpy.data.objects.new("Asset inspection", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (85, 8, 125)
    target = Vector((0, 27, 0))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 120
    scene.camera = camera
    for name, location, energy, size in (("Key", (40, 20, 80), 160000, 65),
                                          ("Fill", (-35, 15, 30), 85000, 70),
                                          ("Rim", (15, 80, -15), 100000, 45)):
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy, light_data.shape, light_data.size = energy, "DISK", size
        light = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light)
        light.location = location
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(ROOT / ".local" / "evidence" / "home-run-bat-render.png")
    scene.view_settings.view_transform = "AgX"
    bpy.context.view_layer.objects.active = bat
    bat.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / "HomeRunBat.blend"))
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-exporter", action="store_true")
    parser.add_argument("--blender", type=Path, default=BLENDER)
    parser.add_argument("--texconv", type=Path, default=GAME / "Tools" / "Elric" / "xtexconv.exe")
    args = parser.parse_args()
    if not args.blender.is_file() or not args.texconv.is_file():
        parser.error("Installed Blender and CK xtexconv are required; override --blender and --texconv if needed.")
    for directory in (CACHE, SOURCE, MESH.parent, TEXTURES, ROOT / ".local" / "evidence"):
        directory.mkdir(parents=True, exist_ok=True)
    nifly = exporter(args.fetch_exporter)
    mesh = geometry()
    paint_textures()
    write_dds(args.texconv)
    write_nif(nifly, mesh)
    report = inspect_nif(nifly)
    # Authoring scene and preview use the exported NIF read-back, not an unexported mesh.
    exported_file = nifly.NifFile(str(MESH))
    exported = exported_file.shapes[0]
    mesh = {"vertices": exported.verts, "normals": exported.normals,
            "uvs": exported.uvs, "triangles": exported.tris}
    scene_path = CACHE / "bat-scene.json"
    scene_path.write_text(json.dumps(mesh), encoding="utf-8")
    subprocess.run([str(args.blender), "--background", "--factory-startup", "--python-exit-code", "1",
                    "--python", str(Path(__file__).resolve()), "--", "--scene-only"], check=True)
    scene_path.unlink()
    (SOURCE / "HomeRunBat.blend1").unlink(missing_ok=True)
    (ROOT / ".local" / "evidence" / "home-run-bat-inspection.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Original bat assets generated and re-read successfully. Game placement/drop checks remain in-game acceptance.")


if __name__ == "__main__":
    if "--scene-only" in sys.argv:
        blender_scene()
    else:
        main()
