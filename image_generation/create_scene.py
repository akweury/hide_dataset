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

    render_args = bpy.context.scene.render
    render_args.engine = "CYCLES"
    render_args.filepath = str(root / "render.png")
    render_args.resolution_x = 160
    render_args.resolution_y = 120
    render_args.resolution_percentage = 100

    bpy.data.worlds["World"].cycles.sample_as_light = True
    bpy.context.scene.cycles.blur_glossy = 2.0
    bpy.context.scene.cycles.samples = 32
    bpy.context.scene.cycles.transparent_min_bounces = 8
    bpy.context.scene.cycles.transparent_max_bounces = 8

    # scene ground-truth
    scene_struct = {
        "split": "none",
        "image_index": 0,
        "image_filename": os.path.basename("render.png"),
        "objects": [],
        "directions": {},
    }

    # add a plane
    bpy.ops.mesh.primitive_plane_add(size=10)
    plane = bpy.context.object

    # add a camera
    bpy.ops.object.camera_add(location=(7.48,-6.51,5.34), rotation=(63.6,0.62, 46.7))
    camera = bpy.data.objects['Camera']
    plane_normal = plane.data.vertices[0].normal

    # cam_behind = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    # cam_left = camera.matrix_world.to_quaternion() @ Vector((-1, 0, 0))
    # cam_up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    # plane_behind = (cam_behind - cam_behind.project(plane_normal)).normalized()
    # plane_left = (cam_left - cam_left.project(plane_normal)).normalized()
    # plane_up = cam_up.project(plane_normal).normalized()

    # scene_struct['directions']['behind'] = tuple(plane_behind)
    # scene_struct['directions']['front'] = tuple(-plane_behind)
    # scene_struct['directions']['left'] = tuple(plane_left)
    # scene_struct['directions']['right'] = tuple(-plane_left)
    # scene_struct['directions']['above'] = tuple(plane_up)
    # scene_struct['directions']['below'] = tuple(-plane_up)

    # objects, blender_objects = utils.add_random_objects(scene_struct, 3, args, camera)

    # scene_struct["objects"] = objects
    # scene_struct["relationships"] = utils.compute_all_relationships(scene_struct)
    # while True:
    #     try:
    #         bpy.ops.render.render(write_still=True)
    #         break
    #     except Exception as e:
    #         print(e)
    #
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
