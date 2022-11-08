import argparse, os, json
from pathlib import Path

import bpy, bpy_extras
from mathutils import Vector
import utils

utils.print_hello()
root = Path(__file__).parents[1]
parser = argparse.ArgumentParser()


def render_scene(args):
    utils.load_materials(str(root / "materials"))

    # scene ground-truth
    scene_struct = {
        "split": "none",
        "image_index": 0,
        "image_filename": os.path.basename("render.png"),
        "objects": [],
        "directions": {},
    }

    render_args = bpy.context.scene.render
    render_args.engine = "CYCLES"
    render_args.filepath = str(root / "render.png")
    render_args.resolution_x = 320
    render_args.resolution_y = 320
    render_args.resolution_percentage = 100
    render_args.pixel_aspect_x = 4.6
    render_args.pixel_aspect_y = 4.6

    bpy.data.worlds["World"].cycles.sample_as_light = True
    bpy.context.scene.cycles.blur_glossy = 2.0
    bpy.context.scene.cycles.samples = 512
    bpy.context.scene.cycles.transparent_min_bounces = 8
    bpy.context.scene.cycles.transparent_max_bounces = 8

    # add a camera
    # https://blender.stackexchange.com/questions/151319/adding-camera-to-scene
    cam1 = bpy.data.cameras.new("Camera_1")
    cam1.lens = 35
    cam1.shift_y = 0.22
    cam_obj1 = bpy.data.objects.new("Camera_1", cam1)
    bpy.context.scene.collection.objects.link(cam_obj1)
    cam_obj1.location = (5.62, -5.77, 4.44)
    cam_obj1.rotation_euler = (0.75, 0.01, 0.82)
    bpy.context.view_layer.objects.active = cam_obj1
    bpy.context.scene.camera = cam_obj1

    # add a plane
    bpy.ops.mesh.primitive_plane_add(size=8)
    plane = bpy.context.object
    plane_normal = plane.data.vertices[0].normal

    # add ambient light 1 (back)
    light_data_1 = bpy.data.lights.new(name='ambient_light_1', type='AREA')
    light_data_1.energy = 50
    light_data_1.size = 1
    # light_data_1.rotation_euler[0] = -0.40
    # light_data_1.rotation_euler[1] = -0.17
    # light_data_1.rotation_euler[2] = -0.03
    light_obj_1 = bpy.data.objects.new(name="ambient_light_1", object_data=light_data_1)
    bpy.context.collection.objects.link(light_obj_1)
    bpy.context.view_layer.objects.active = light_obj_1
    light_obj_1.location = (-1.17, 2.65, 5.82)
    light_obj_1.rotation_euler[0] = -0.40
    light_obj_1.rotation_euler[1] = -0.17
    light_obj_1.rotation_euler[2] = -0.03

    # add ambient light 2 (fill)
    light_data_2 = bpy.data.lights.new(name='ambient_light_2', type='AREA')
    light_data_2.energy = 30
    light_data_2.size = 0.5
    light_data_2.color[0] = 0.762
    light_data_2.color[1] = 0.818
    light_data_2.color[2] = 1
    # light_data_2.rotation_euler[0] = 1.03
    # light_data_2.rotation_euler[1] = -0.53
    # light_data_2.rotation_euler[2] = -0.56
    light_obj_2 = bpy.data.objects.new(name="ambient_light_2", object_data=light_data_2)
    bpy.context.collection.objects.link(light_obj_2)
    bpy.context.view_layer.objects.active = light_obj_2
    light_obj_2.location = (-4.67, -4.01, 3.01)
    light_obj_2.rotation_euler[0] = 1.03
    light_obj_2.rotation_euler[1] = -0.53
    light_obj_2.rotation_euler[2] = -0.56

    # add ambient light 3 (key)
    light_data_3 = bpy.data.lights.new(name='ambient_light_3', type='AREA')
    light_data_3.energy = 100
    light_data_3.size = 0.5
    light_data_3.color[0] = 1
    light_data_3.color[1] = 0.932
    light_data_3.color[2] = 0.817

    light_obj_3 = bpy.data.objects.new(name="ambient_light_3", object_data=light_data_3)
    bpy.context.collection.objects.link(light_obj_3)
    bpy.context.view_layer.objects.active = light_obj_3
    light_obj_3.location = (6.45, -2.91, 4.26)
    light_obj_3.rotation_euler[0] = -0.225
    light_obj_3.rotation_euler[1] = 1.002
    light_obj_3.rotation_euler[2] = -0.664

    cam_behind = cam_obj1.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    cam_left = cam_obj1.matrix_world.to_quaternion() @ Vector((-1, 0, 0))
    cam_up = cam_obj1.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    plane_behind = (cam_behind - cam_behind.project(plane_normal)).normalized()
    plane_left = (cam_left - cam_left.project(plane_normal)).normalized()
    plane_up = cam_up.project(plane_normal).normalized()

    scene_struct['directions']['behind'] = tuple(plane_behind)
    scene_struct['directions']['front'] = tuple(-plane_behind)
    scene_struct['directions']['left'] = tuple(plane_left)
    scene_struct['directions']['right'] = tuple(-plane_left)
    scene_struct['directions']['above'] = tuple(plane_up)
    scene_struct['directions']['below'] = tuple(-plane_up)

    objects, blender_objects = utils.add_random_objects(scene_struct, 3, args, cam_obj1)

    bpy.ops.render.render(write_still=True)

    # scene_struct["objects"] = objects
    # scene_struct["relationships"] = utils.compute_all_relationships(scene_struct)
    # with open("render.json", "w") as f:
    #     json.dump(scene_struct, f, indent=2)


def main(args):
    render_scene(args)
    # print("...")


if __name__ == "__main__":
    # pass args
    argv = utils.extract_args()
    args = parser.parse_args(argv)
    # start the simulation
    main(args)
