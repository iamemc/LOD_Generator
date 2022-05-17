bl_info = {
    "name": "Lod Generator",
    "description": "Blender addon wrapper of Swagger's Lod Generator.",
    "author": "Swagger, Lorenzo-Feral",
    "version": (1, 0, 0),
    "blender": (3, 1, 2),
    "category": "3D View"
}


#####   IMPORTS

import bpy
import os


#####   FUNCTIONS (Swagger Tool Functions)

def addDecimateModifier(context, decimate_ratio):
    bpy.ops.object.select_all(action='SELECT')
    print("Decimating ratio: ", decimate_ratio)
    for obj in context.selected_objects:
        if obj.type in ('MESH'):
            mod = obj.modifiers.get("DECIMATE")
            if mod is None:
                obj.modifiers.new("DECIMATE", 'DECIMATE').ratio = decimate_ratio

def applyDecimateModifier(context):
    bpy.ops.object.select_all(action='SELECT')
    for obj in context.selected_objects:
        if obj.type in ('MESH'):
            context.view_layer.objects.active = obj
            for modifier in obj.modifiers:
                if modifier.type == 'DECIMATE':
                    bpy.ops.object.modifier_apply(
                        modifier=modifier.name)

def renameUVMaps(context, file_name):
    for obj in context.selected_objects:
        if obj.type in ('MESH'):
            for uvmap in obj.data.uv_layers:
                uvmap.name = file_name[:-4]

def purgeObjects():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    bpy.ops.outliner.orphans_purge(num_deleted=0, do_local_ids=True,\
                                   do_linked_ids=True, do_recursive=True)

def joinChildObjects(context):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in context.scene.objects:
        if obj.type in ('MESH'):
            if obj.name not in ("ARMATURE", "armature","Armature",\
                                "primary_weapon", "primary__weapon",\
                                "secondary_weapon", "secondary__weapon"):
                if ("Upper Pteryges") in obj.name or\
                    ("Wide Lower Pteryges") in obj.name or\
                    ("wide_lower_pteryges") in obj.name:
                    print(obj.name)
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.flip_normals()
                    bpy.ops.object.mode_set()
                bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
                bpy.data.objects[obj.name].select_set(state=True)
                bpy.ops.object.join()
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.normals_make_consistent(inside=False)
                bpy.ops.object.mode_set()

def limitBoneWeighting(context):
    armature_exists = False
    bpy.ops.object.select_all(action='DESELECT')
    for obj in context.scene.objects:
        if obj.name in ("ARMATURE", "armature","Armature"):
            armature_exists = True
    if armature_exists == True:
        for obj in context.scene.objects:
            if obj.name not in ("ARMATURE", "armature","Armature",\
                                "primary_weapon", "secondary_weapon",\
                                "secondary_weapon", "secondary__weapon"):
                print(obj.name)
                print("Limiting Bone Weights Now")
                bpy.ops.paint.weight_paint_toggle()
                context.object.data.use_paint_mask_vertex = True
                bpy.ops.paint.vert_select_all(action='SELECT')
                bpy.ops.object.vertex_group_limit_total(limit=1)
                bpy.ops.paint.weight_paint_toggle()

def checkIfDirectoryExists(file_name_string):
    if not os.path.isdir(file_name_string):
        os.mkdir(file_name_string[:-4])

def generate_LODs(context, input_dir, output_dir, decimate_ratio):
    LOD_level = "lod1" if (decimate_ratio >= 0.5) else "lod2" if (decimate_ratio >= 0.25) else "lod3"
    purgeObjects()
    for filename in os.listdir(input_dir):
        file = os.path.join(input_dir, filename)
        # checking if it is a file
        if os.path.isfile(file):
            if file.endswith("dae"):
                file_name = os.path.basename(file)
                print("FILENAME: ", file_name)
                bpy.ops.wm.collada_import(filepath="{0}\\{1}".format(input_dir, file_name))
                
                renameUVMaps(context = context, file_name = file_name)
                
                joinChildObjects(context = context)
                
                addDecimateModifier(context = context, decimate_ratio = decimate_ratio)
                
                applyDecimateModifier(context = context)

## REQUIRED - make sure to deselect everything
                bpy.ops.object.mode_set(mode='OBJECT')
                for polygon in bpy.context.active_object.data.polygons:
                    polygon.select = False
                for edge in bpy.context.active_object.data.edges:
                    edge.select = False
                for vertex in bpy.context.active_object.data.vertices:
                    vertex.select = False
## /REQUIRED - make sure to deselect everything

                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)
                bpy.ops.mesh.delete_loose()
                bpy.ops.object.mode_set(mode = 'OBJECT')

                # delete any previous lod naming
                file_name = file_name.replace("_lod0","")
                output_file_name = '{file_name}_{lod_level}.dae'.format(file_name = file_name[:-4], lod_level = LOD_level)
                limitBoneWeighting(context)
                limitBoneWeighting(context)
                print(output_file_name)
                # Export Mesh
                bpy.ops.wm.collada_export(filepath=os.path.join(output_dir, output_file_name))
                purgeObjects() #REQUIRED, so the next loop doesn't inherit data from the previous models

#####    END FUNCTIONS


#####    PANELS
class FERAL_PT_Main_Panel(bpy.types.Panel):
    bl_label = "LOD Generator Options"
    bl_idname = "FERAL_PT_Feral_Decimation_Main_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Mod - Rome Remastered'
    bl_order = 0


    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        try:
            layout = self.layout
        except Exception as exc:
            print(str(exc) + " | Error in Feral - Decimation Panel header")

    def draw(self, context):
        try:
            layout = self.layout
        except Exception as exc:
            print(str(exc) + " | Error in Feral - Decimation Panel")


class FERAL_PT_Decimation_Tool(bpy.types.Panel):
    bl_label = "DAE Decimation Tool"
    bl_idname = "FERAL_PT_Decimation_Tool"
    bl_parent_id = "FERAL_PT_Feral_Decimation_Main_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        try:
            layout = self.layout
        except Exception as exc:
            print(str(exc) + " | Error in Feral Decimation Tool subpanel header")

    def draw(self, context):
        try:
            layout = self.layout
            col = layout.column(align=False)

            row = col.row(align=True)
            row.prop(context.scene, "decimation_input_basedir")

            row = col.row(align=True)
            row.prop(context.scene, "decimation_output_basedir")


            row = col.row(align=True)
            row.prop(context.scene, "decimation_amount")

            col.separator(factor=1.0)

            op = col.operator("feral_dae_decimation.decimate_folder", text=r"Generate LODs", emboss=True, depress=False, icon_value=0)
        except Exception as exc:
            print(str(exc) + " | Error in Feral Decimation Tool subpanel")

####    END PANELS

####    OPERATORS

class FERAL_OT_Decimate_DAE(bpy.types.Operator):
    bl_idname = "feral_dae_decimation.decimate_folder"
    bl_label = "decimate_folder"
    bl_description = "Decimate all dae file in a folder."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.decimation_input_basedir != ""

    def execute(self, context):
        try:
            input_dir = context.scene.decimation_input_basedir
            if context.scene.decimation_output_basedir != "":
                output_dir = context.scene.decimation_output_basedir
            else:
                output_dir = input_dir

            decimate_ratio = context.scene.decimation_amount

            generate_LODs(context = context, input_dir = input_dir, output_dir = output_dir, decimate_ratio = decimate_ratio)

        except Exception as exc:
            print(str(exc) + " | Error in execute function of slice")
        return {"FINISHED"}

    def invoke(self, context, event):
        try:
            pass
        except Exception as exc:
            print(str(exc) + " | Error in invoke function of slice")
        return self.execute(context)


####    END OPERATORS


#####    REGISTER PROPERTIES
def register_properties():
    bpy.types.Scene.decimation_input_basedir = bpy.props.StringProperty(
        name = "Input directory",
        default = "",
        description = "Directory with dae files to decimate.",
        subtype = 'DIR_PATH'
    )
    bpy.types.Scene.decimation_output_basedir = bpy.props.StringProperty(
        name = "Output directory",
        default = "",
        description = "Directory to export decimated dae models to.",
        subtype = 'DIR_PATH'
    )
    bpy.types.Scene.decimation_amount = bpy.props.FloatProperty(
        name='Decimation Ratio',
        description='Decimation ratio from 0 to 1.',
        subtype='NONE',
        options=set(),
        default=.75,
        min=0,
        max=1
    )

def unregister_properties():
    del bpy.types.Scene.decimation_input_basedir
    del bpy.types.Scene.decimation_output_basedir
    del bpy.types.Scene.decimation_amount


####    REGISTER ADDON

def register():
    register_properties()

    bpy.utils.register_class(FERAL_PT_Main_Panel)
    bpy.utils.register_class(FERAL_PT_Decimation_Tool)

    bpy.utils.register_class(FERAL_OT_Decimate_DAE)
    


####    UNREGISTER ADDON

def unregister():
    unregister_properties()

    bpy.utils.unregister_class(FERAL_OT_Decimate_DAE)

    bpy.utils.unregister_class(FERAL_PT_Decimation_Tool)
    bpy.utils.unregister_class(FERAL_PT_Main_Panel)



if __name__ == "__main__":
    register()