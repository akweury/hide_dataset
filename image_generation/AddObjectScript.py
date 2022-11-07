import bpy


class TestPanel(bpy.types.Panel):
    bl_label = "Test Panel"
    bl_idname = "PT_TestPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "My 1st addon"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text="Add an object", icon="CUBE")
        row = layout.row()
        row.operator("mesh.primitive_cube_add", icon="CUBE")
        row = layout.row()
        row.operator("mesh.primitive_uv_sphere_add", icon="SPHERE")
        bpy.data.objects["Sphere.001"].location[0]
        row = layout.row()
        row.operator("object.text_add")
        
        
def register():
    bpy.utils.register_class(TestPanel)
    
    
def unregister():
    bpy.utils.unregister_class(TestPanel)
    
if __name__ == "__main__":
    bpy.ops.mesh.primitive_cube_add()
    so = bpy.context.active_object
    
    so.location[0] = 5