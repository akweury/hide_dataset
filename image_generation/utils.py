import math, sys, random, argparse, json, os, tempfile
from collections import Counter
from pathlib import Path

import bpy, bpy_extras

root = Path(__file__).parents[0]


def print_hello():
    print("hello")


def extract_args(input_argv=None):
    """
    Pull out command-line arguments after "--". Blender ignores command-line flags
    after --, so this lets us forward command line arguments from the blender
    invocation to our own script.
    """
    if input_argv is None:
        input_argv = sys.argv
    output_argv = []
    if '--' in input_argv:
        idx = input_argv.index('--')
        output_argv = input_argv[(idx + 1):]
    return output_argv


def load_materials(material_dir):
    """
    Load materials from a directory. We assume that the directory contains .blend
    files with one material each. The file X.blend has a single NodeTree item named
    X; this NodeTree item must have a "Color" input that accepts an RGBA value.
    """
    for fn in os.listdir(material_dir):
        if not fn.endswith('.blend'): continue
        name = os.path.splitext(fn)[0]
        filepath = os.path.join(material_dir, fn, 'NodeTree', name)
        bpy.ops.wm.append(filename=filepath)


def add_material(name, **properties):
    """
    Create a new material and assign it to the active object. "name" should be the
    name of a material that has been previously loaded using load_materials.
    """
    # Figure out how many materials are already in the scene
    mat_count = len(bpy.data.materials)

    # Create a new material; it is not attached to anything and
    # it will be called "Material"
    bpy.ops.material.new()

    # Get a reference to the material we just created and rename it;
    # then the next time we make a new material it will still be called
    # "Material" and we will still be able to look it up by name
    mat = bpy.data.materials['Material']
    mat.name = 'Material_%d' % mat_count

    # Attach the new material to the active object
    # Make sure it doesn't already have materials
    obj = bpy.context.active_object
    assert len(obj.data.materials) == 0
    obj.data.materials.append(mat)

    # Find the output node of the new material
    output_node = None
    for n in mat.node_tree.nodes:
        if n.name == 'Material Output':
            output_node = n
            break

    # Add a new GroupNode to the node tree of the active material,
    # and copy the node tree from the preloaded node group to the
    # new group node. This copying seems to happen by-value, so
    # we can create multiple materials of the same type without them
    # clobbering each other
    group_node = mat.node_tree.nodes.new('ShaderNodeGroup')
    group_node.node_tree = bpy.data.node_groups[name]

    # Find and set the "Color" input of the new group node
    for inp in group_node.inputs:
        if inp.name in properties:
            inp.default_value = properties[inp.name]

    # Wire the output of the new group node to the input of
    # the MaterialOutput node
    mat.node_tree.links.new(
        group_node.outputs['Shader'],
        output_node.inputs['Surface'],
    )


def add_object(object_dir, name, scale, loc, theta=0):
    """
    Load an object from a file. We assume that in the directory object_dir, there
    is a file named "$name.blend" which contains a single object named "$name"
    that has unit size and is centered at the origin.

    - scale: scalar giving the size that the object should be in the scene
    - loc: tuple (x, y) giving the coordinates on the ground plane where the
      object should be placed.
    """
    # First figure out how many of this object are already in the scene so we can
    # give the new object a unique name
    count = 0
    for obj in bpy.data.objects:
        if obj.name.startswith(name):
            count += 1

    filename = os.path.join(object_dir, '%s.blend' % name, 'Object', name)
    bpy.ops.wm.append(filename=filename)

    # Give it a new name to avoid conflicts
    new_name = '%s_%d' % (name, count)
    bpy.data.objects[name].name = new_name

    # Set the new object as active, then rotate, scale, and translate it
    x, y = loc
    bpy.context.view_layer.objects.active = bpy.data.objects[new_name]
    bpy.context.object.rotation_euler[2] = theta
    bpy.ops.transform.resize(value=(scale, scale, scale))
    bpy.ops.transform.translate(value=(x, y, scale))


def delete_object(obj):
    """ Delete a specified blender object """
    for o in bpy.data.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.delete()


def get_camera_coords(cam, pos):
    """
    For a specified point, get both the 3D coordinates and 2D pixel-space
    coordinates of the point from the perspective of the camera.

    Inputs:
    - cam: Camera object
    - pos: Vector giving 3D world-space position

    Returns a tuple of:
    - (px, py, pz): px and py give 2D image-space coordinates; pz gives depth
      in the range [-1, 1]
    """
    scene = bpy.context.scene
    x, y, z = bpy_extras.object_utils.world_to_camera_view(scene, cam, pos)
    scale = scene.render.resolution_percentage / 100.0
    w = int(scale * scene.render.resolution_x)
    h = int(scale * scene.render.resolution_y)
    px = int(round(x * w))
    py = int(round(h - y * h))
    return (px, py, z)


def set_layer(obj, layer_idx):
    """ Move an object to a particular layer """
    # Set the target layer to True first because an object must always be on
    # at least one layer.
    obj.layers[layer_idx] = True
    for i in range(len(obj.layers)):
        obj.layers[i] = (i == layer_idx)


# def render_shadeless(blender_objects, path='flat.png'):
#     """
#     Render a version of the scene with shading disabled and unique materials
#     assigned to all objects, and return a set of all colors that should be in the
#     rendered image. The image itself is written to path. This is used to ensure
#     that all objects will be visible in the final rendered scene.
#     """
#     render_args = bpy.context.scene.render
#
#     # Cache the render args we are about to clobber
#     old_filepath = render_args.filepath
#     old_engine = render_args.engine
#     old_use_antialiasing = render_args.use_antialiasing
#
#     # Override some render settings to have flat shading
#     render_args.filepath = path
#     render_args.engine = 'CYCLES'
#     render_args.use_antialiasing = False
#
#     # Move the lights and ground to layer 2 so they don't render
#     set_layer(bpy.data.objects['Lamp_Key'], 2)
#     set_layer(bpy.data.objects['Lamp_Fill'], 2)
#     set_layer(bpy.data.objects['Lamp_Back'], 2)
#     set_layer(bpy.data.objects['Ground'], 2)
#
#     # Add random shadeless materials to all objects
#     object_colors = set()
#     old_materials = []
#     for i, obj in enumerate(blender_objects):
#         old_materials.append(obj.data.materials[0])
#         bpy.ops.material.new()
#         mat = bpy.data.materials['Material']
#         mat.name = 'Material_%d' % i
#         while True:
#             r, g, b = [random.random() for _ in range(3)]
#             if (r, g, b) not in object_colors: break
#         object_colors.add((r, g, b))
#         mat.diffuse_color = [r, g, b]
#         mat.use_shadeless = True
#         obj.data.materials[0] = mat
#
#     # Render the scene
#     bpy.ops.render.render(write_still=True)
#
#     # Undo the above; first restore the materials to objects
#     for mat, obj in zip(old_materials, blender_objects):
#         obj.data.materials[0] = mat
#
#     # Move the lights and ground back to layer 0
#     set_layer(bpy.data.objects['Lamp_Key'], 0)
#     set_layer(bpy.data.objects['Lamp_Fill'], 0)
#     set_layer(bpy.data.objects['Lamp_Back'], 0)
#     set_layer(bpy.data.objects['Ground'], 0)
#
#     # Set the render settings back to what they were
#     render_args.filepath = old_filepath
#     render_args.engine = old_engine
#     render_args.use_antialiasing = old_use_antialiasing
#
#     return object_colors


def check_visibility(blender_objects, min_pixels_per_object):
    """
    Check whether all objects in the scene have some minimum number of visible
    pixels; to accomplish this we assign random (but distinct) colors to all
    objects, and render using no lighting or shading or antialiasing; this
    ensures that each object is just a solid uniform color. We can then count
    the number of pixels of each color in the output image to check the visibility
    of each object.

    Returns True if all objects are visible and False otherwise.
    """
    f, path = tempfile.mkstemp(suffix='.png')
    # object_colors = render_shadeless(blender_objects, path=path)
    img = bpy.data.images.load(path)
    p = list(img.pixels)
    color_count = Counter((p[i], p[i + 1], p[i + 2], p[i + 3])
                          for i in range(0, len(p), 4))
    os.remove(path)
    if len(color_count) != len(blender_objects) + 1:
        return False
    for _, count in color_count.most_common():
        if count < min_pixels_per_object:
            return False
    return True


def load_property_json(file_name):
    with open(str(root / file_name), 'r') as f:
        properties = json.load(f)
        color_name_to_rgba = {}
        for name, rgb in properties['colors'].items():
            rgba = [float(c) / 255.0 for c in rgb] + [1.0]
            color_name_to_rgba[name] = rgba
        material_mapping = [(v, k) for k, v in properties['materials'].items()]
        object_mapping = [(v, k) for k, v in properties['shapes'].items()]
        size_mapping = list(properties['sizes'].items())
    return material_mapping, object_mapping, size_mapping,color_name_to_rgba

def add_random_objects(scene_struct, num_objects, args, camera):
    """
    Add random objects to the current blender scene
    """

    # Load the property file
    material_mapping, object_mapping, size_mapping,color_name_to_rgba = load_property_json("properties.json")
    positions = []
    objects = []
    blender_objects = []

    for i in range(num_objects):
        # Choose a random size
        size_name, r = random.choice(size_mapping)

        # Try to place the object, ensuring that we don't intersect any existing
        # objects and that we are more than the desired margin away from all existing
        # objects along all cardinal directions.
        num_tries = 0
        while True:
            # If we try and fail to place an object too many times, then delete all
            # the objects in the scene and start over.
            num_tries += 1
            if num_tries > 50:
                for obj in blender_objects:
                    delete_object(obj)
                return add_random_objects(scene_struct, num_objects, args, camera)
            x = random.uniform(-3, 3)
            y = random.uniform(-3, 3)
            # Check to make sure the new object is further than min_dist from all
            # other objects, and further than margin along the four cardinal directions
            dists_good = True
            margins_good = True
            for (xx, yy, rr) in positions:
                dx, dy = x - xx, y - yy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist - r - rr < 0.25:
                    dists_good = False
                    break
                for direction_name in ['left', 'right', 'front', 'behind']:
                    direction_vec = scene_struct['directions'][direction_name]
                    assert direction_vec[2] == 0
                    margin = dx * direction_vec[0] + dy * direction_vec[1]
                    if 0 < margin < 0.4:
                        print(margin, 0.4, direction_name)
                        print('BROKEN MARGIN!')
                        margins_good = False
                        break
                if not margins_good:
                    break

            if dists_good and margins_good:
                break

        # Choose random color and shape
        obj_name, obj_name_out = random.choice(object_mapping)
        color_name, rgba = random.choice(list(color_name_to_rgba.items()))


        # For cube, adjust the size a bit
        if obj_name == 'Cube':
            r /= math.sqrt(2)

        # Choose random orientation for the object.
        theta = 360.0 * random.random()

        # Actually add the object to the scene
        add_object(str(root / "shape"), obj_name, r, (x, y), theta=theta)
        obj = bpy.context.object
        blender_objects.append(obj)
        positions.append((x, y, r))

        # Attach a random material
        mat_name, mat_name_out = random.choice(material_mapping)
        add_material(mat_name, Color=rgba)

        # Record data about the object in the scene data structure
        pixel_coords = get_camera_coords(camera, obj.location)
        objects.append({
            'shape': obj_name_out,
            'size': size_name,
            'material': mat_name_out,
            '3d_coords': tuple(obj.location),
            'rotation': theta,
            'pixel_coords': pixel_coords,
            'color': color_name,
        })

    # Check that all objects are at least partially visible in the rendered image
    # all_visible = check_visibility(blender_objects, 200)
    # if not all_visible:
    #     # If any of the objects are fully occluded then start over; delete all
    #     # objects from the scene and place them all again.
    #     print('Some objects are occluded; replacing objects')
    #     for obj in blender_objects:
    #         delete_object(obj)
    #     return add_random_objects(scene_struct, num_objects, args, camera)

    return objects, blender_objects


def compute_all_relationships(scene_struct, eps=0.2):
    """
    Computes relationships between all pairs of objects in the scene.

    Returns a dictionary mapping string relationship names to lists of
    integers, where output[rel][i] gives a list of object indices that have the
    relationship rel with object i. For example if j is in output['left'][i] then
    object j is left of object i.
    """
    all_relationships = {}
    for name, direction_vec in scene_struct['directions'].items():
        if name == 'above' or name == 'below': continue
        all_relationships[name] = []
        for i, obj1 in enumerate(scene_struct['objects']):
            coords1 = obj1['3d_coords']
            related = set()
            for j, obj2 in enumerate(scene_struct['objects']):
                if obj1 == obj2: continue
                coords2 = obj2['3d_coords']
                diff = [coords2[k] - coords1[k] for k in [0, 1, 2]]
                dot = sum(diff[k] * direction_vec[k] for k in [0, 1, 2])
                if dot > eps:
                    related.add(j)
            all_relationships[name].append(sorted(list(related)))
    return all_relationships
