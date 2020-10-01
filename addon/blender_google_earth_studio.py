
#https://blender.stackexchange.com/questions/57306/how-to-create-a-custom-ui
#!/usr/bin/python
# -*- coding: utf-8 -*-
bl_info = {
    "name": "Blender Google Earth Studio",
    "description": "secelct Google Earth Studio folder and click create to see the magic!",
    "author": "Pascal Jardin",
    "version": (0, 0, 0),
    "blender": (2, 90, 0),
    "location": "3D View > BGES",
    "warning": "still a work in progress", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}
import pathlib
path = pathlib.Path(__file__).parent.absolute()


import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class MyProperties(PropertyGroup):

    my_path: StringProperty(
        name = "Directory",
        description="Choose a directory:",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------
import json 
class WM_OT_HelloWorld(Operator):
    bl_label = "create google earth studio"
    bl_idname = "wm.hello_world"

    def execute(self, context):
        scene = bpy.context.scene
        mytool = scene.my_tool

        # print the values to the console
        print("Hello World")
        print("string value:", mytool.my_path)
        
        filepath_full = bpy.path.abspath(mytool.my_path)
        #https://blender.stackexchange.com/questions/12152/absolute-path-of-files-in-blender-with-python
        #filepath_full = filepath_full.replace(" ", "\ ")#handle spaces
        print(filepath_full)
       
        google_earth_studio(filepath_full)
    
    
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------

class OBJECT_PT_CustomPanel(Panel):
    bl_label = "Blender Google Earth Studio"
    bl_idname = "OBJECT_PT_google_earth_studio_panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "BGES"

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        mytool = scene.my_tool

        layout.prop(mytool, "my_path")
        layout.operator("wm.hello_world")
        layout.separator()

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    WM_OT_HelloWorld,
    OBJECT_PT_CustomPanel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()





# ========================================================================
#    code for google earth studio... should be in another file but im lazy 
# ========================================================================
import bpy
from bpy.types import Panel, Operator,Property
from bpy import context
import fnmatch


import json

import math
 
#https://stackoverflow.com/questions/58447896/understanding-matrix-operations-in-blender
import mathutils

#https://github.com/sobotka/blender-addons/blob/master/io_import_images_as_planes.py
from bpy_extras.image_utils import load_image



#---needed functions
def asRadians(degrees):
    return degrees * math.pi / 180

def getXYpos(relativeNullPoint, p):
    #Calculates X and Y distances in meters.
    
    deltaLatitude = p["latitude"] - relativeNullPoint["latitude"] 
    deltaLongitude = p["longitude"] - relativeNullPoint["longitude"]
    latitudeCircumference = 40075160 * math.cos(asRadians(relativeNullPoint["latitude"] ))
    resultX = deltaLongitude * latitudeCircumference / 360
    resultY = deltaLatitude * 40008000 / 360
    return resultX, resultY
#-------------

#get file locations-------
def folder(f):
    folder_loc = f

    if folder_loc[0] != "/":
        folder_loc = "/" + folder_loc

    folderName = folder_loc.split("/")

    if (folderName[-1] == ""):
        folderName = folderName[-2]
    else:
        folderName = folderName[-1]
        folder_loc += "/"
        
    rendered_frames_loc = folder_loc + "footage/" + folderName + "_000.jpeg"
    
    
    return folder_loc, folderName, rendered_frames_loc

#--------------------------
def creat_empty():
    scene = bpy.context.scene
    empty = None
    
    for obj in scene.objects:
        if fnmatch.fnmatchcase(obj.name, "google_earth_empty"):
            empty = obj 
            empty.rotation_euler = [0,0,0]
            empty.location = [0,0,0]
            empty.scale = [1,1,1]
            empty.matrix_world = clearMatrix
            break
        else:
            obj.select_set(False)

    if (empty == None):
        bpy.ops.object.empty_add(type='SPHERE', align='WORLD', location=(0,0,0), scale=(1, 1, 1))
        empty = bpy.context.object
        empty.name = "google_earth_empty"
        
    return empty


def creat_camera():
    scene = bpy.context.scene
    #https://github.com/imagiscope/Blender_GES_Import/blob/master/GES_importscript.py
    rendered_frames = bpy.data.movieclips.load(rendered_frames_loc)
    
    
    #--delet camera if it already exsist 
    camera = None
    for obj in scene.objects:
        if fnmatch.fnmatchcase(obj.name, "google_earth_camera*"):
            camera = obj 
            camera.rotation_euler = [0,0,0]
            camera.location = [0,0,0]
            camera.scale = [1,1,1]
            camera.matrix_world = clearMatrix
            break
        else:
            obj.select_set(False)
      
    #bpy.ops.object.delete()

    #creat new camera
    if (camera == None):
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.object.rotation_mode = 'ZYX'

        camera = bpy.context.object

        camera.name = "google_earth_camera"




    camera.data.show_background_images = True
    camera.data.background_images.clear() #!!!needed to clear out old!
    bg = camera.data.background_images.new()
    bg.clip = rendered_frames
    bg.alpha = 1
    bg.source = "MOVIE_CLIP"

    camera.data.sensor_width = 35 
    camera.data.type = 'PERSP'
    camera.data.lens_unit = 'FOV'
    camera.data.angle = math.radians(34.8)

    return camera
    

def composeter():
    #set up scene
    #-------
    bpy.context.scene.sync_mode = 'AUDIO_SYNC'
    #------

    rendered_frames = bpy.data.movieclips.load(rendered_frames_loc)
    
    #-----------------
    #bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.use_nodes = True


    #setup node compositor
    #https://blender.stackexchange.com/questions/19500/controling-compositor-by-python

    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree

    # clear default nodes
    for node in tree.nodes:
        tree.nodes.remove(node)


    # create input layer
    NodeRLayers = tree.nodes.new(type='CompositorNodeRLayers')
    NodeRLayers.location = 0,-200

    MovieClip = tree.nodes.new(type='CompositorNodeMovieClip')
    MovieClip.location = 0,200
    MovieClip.clip = rendered_frames#very important!

    #alpha over node
    AlphaOver = tree.nodes.new(type='CompositorNodeAlphaOver')
    AlphaOver.location = 400,0

    # create output nodes
    comp_node = tree.nodes.new('CompositorNodeComposite')   
    comp_node.location = 800,-200

    view_node = tree.nodes.new('CompositorNodeViewer')   
    view_node.location = 800,200


    # link nodes
    links = tree.links
    link = links.new(NodeRLayers.outputs[0], AlphaOver.inputs[2])
    link = links.new(MovieClip.outputs[0], AlphaOver.inputs[1])

    link = links.new(AlphaOver.outputs[0], comp_node.inputs[0])
    link = links.new(AlphaOver.outputs[0], view_node.inputs[0])
    #-----------------



def get_json():
    # read file
    with open(folder_loc  + folderName + ".json", 'r') as myfile:
        data=myfile.read()
        
    # parse file
    move = json.loads(data)
    
    bpy.context.scene.frame_start = 2 #becouse rendered images are slightly off by camera movements 
    bpy.context.scene.frame_end = len(move["cameraFrames"])
    
    return move


def moveCamera():

    scene = bpy.context.scene



    #-----varables for loop
    start_point = move["cameraFrames"][0]["coordinate"]
    start_rot = move["cameraFrames"][0]["rotation"]

    lat = asRadians(start_point["latitude"])
    lon = asRadians(start_point["longitude"])

    mat_rot_lon = mathutils.Matrix.Rotation(-lon, 4, 'Z')
    mat_rot_lat = mathutils.Matrix.Rotation( (lat - math.pi / 2), 4, 'Y')

    original_matrix =  mat_rot_lat @ mat_rot_lon  @ camera.matrix_world
     
    fc = 1 #need to start at one for it to be correct offset

    #-------------

    #https://stackoverflow.com/questions/3024404/transform-longitude-latitude-into-meters
    for frame in move["cameraFrames"]:
      
        #camera location
        #--------------------------
        newY, newX = getXYpos(start_point,frame["coordinate"])
        
        newZ = frame["coordinate"]['altitude'] - start_point['altitude']

        matrix_loc = mathutils.Matrix.Translation((-newX,newY,newZ))
     
        #rotation
        #--------------------------
        frame_rot = frame["rotation"]
        #camera.rotation_euler = [ asRadians(frame_rot["x"]) ,  asRadians(frame_rot["y"]) - asRadians(180), asRadians(180) - asRadians(frame_rot["z"])]
        rot_x = mathutils.Matrix.Rotation(asRadians(frame_rot["x"]) , 4, 'X')    
        rot_y = mathutils.Matrix.Rotation(asRadians(frame_rot["y"]) - asRadians(180) , 4, 'Y')   
        rot_z = mathutils.Matrix.Rotation( asRadians(180) - asRadians(frame_rot["z"]) , 4, 'Z')   
        
        #apply matrixes
        camera.matrix_world = matrix_loc @ original_matrix @ rot_x @ rot_y @ rot_z
        
        #set keframes
        camera.keyframe_insert('rotation_euler', frame=fc)
        camera.keyframe_insert('location', frame=fc)
         
        fc += 1


def create_mat():
    # Get material
    mat_shadow_catcher = bpy.data.materials.get("google_earth_shadow_catcher")
    if mat_shadow_catcher is None:
        # create material
        mat_shadow_catcher = bpy.data.materials.new(name="google_earth_shadow_catcher")
        
    mat_shadow_catcher.use_nodes = True
    tree = mat_shadow_catcher.node_tree

    # clear default nodes
    for node in tree.nodes:
        tree.nodes.remove(node)

    #output
    output = tree.nodes.new('ShaderNodeOutputMaterial')   
    output.location = 600,0
    
    #Diffuse
    diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')   
    diffuse.location = 400,0

    #text
    text = tree.nodes.new('ShaderNodeTexImage')   
    text.location = 0,0
    
    img = bpy.data.images.load(rendered_frames_loc)
    img.source = 'SEQUENCE'
 
    text.image = img
    
    text.image_user.frame_start = 2
    text.image_user.frame_duration = len(move["cameraFrames"])
    text.image_user.use_auto_refresh = True
    text.image_user.use_cyclic = True

    #map
    map = tree.nodes.new('ShaderNodeMapping')   
    map.location = -200,0

    #texCoord 
    texCoord = tree.nodes.new('ShaderNodeTexCoord')   
    texCoord.location = -400,0

    #link nodes
    links = tree.links
    link = links.new(texCoord.outputs[5], map.inputs[0])
    link = links.new(map.outputs[0], text.inputs[0])
    link = links.new(text.outputs[0], diffuse.inputs[0])
    link = links.new(diffuse.outputs[0], output.inputs[0])

    return mat_shadow_catcher




def create_tracked_points():
    scene = bpy.context.scene
    
    start_point = move["cameraFrames"][0]["coordinate"]
    start_rot = move["cameraFrames"][0]["rotation"]

    lat = asRadians(start_point["latitude"])
    lon = asRadians(start_point["longitude"])
    
    #setup for tracked points 
    #-----------------------
    frame_pos =  move["cameraFrames"][0]["position"]
    r = (frame_pos["x"] **2 +frame_pos["y"] ** 2 + frame_pos["z"] ** 2)**.5


    # offset camera rotation matrix
    mat_rot_lon = mathutils.Matrix.Rotation(-lon, 4, 'Z')
    mat_rot_lat = mathutils.Matrix.Rotation( (lat - math.pi / 2), 4, 'Y')

    #offset camera - earth radius
    mat_loc = mathutils.Matrix.Translation((0.0, 0.0, -r))

    camera_offset = mat_loc @ mat_rot_lat @ mat_rot_lon @ clearMatrix
        
    #-----------------------


    #------ make track points
    for t in move["trackPoints"]:
       
        name = "shadow_catcher_" + t["name"] 
        
        shadow_catcher = None
        for obj in scene.objects:
            if fnmatch.fnmatchcase(obj.name, name):
                shadow_catcher = obj 
                shadow_catcher.rotation_euler = [0,0,0]
                shadow_catcher.location = [0,0,0]

            else:
                obj.select_set(False)

        if (shadow_catcher == None):
            bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0,0,0), scale=(1, 1, 1))
            shadow_catcher = bpy.context.object
            shadow_catcher.name = name

            #make monkey
            bpy.ops.mesh.primitive_monkey_add(enter_editmode=False, align='WORLD', location=(2, 0, 2), scale=(1, 1, 1))
            monkey = bpy.context.object
            monkey.parent = shadow_catcher
            
        #https://blender.stackexchange.com/questions/23433/how-to-assign-a-new-material-to-an-object-in-the-scene-from-python
        # Assign it to object
        if shadow_catcher.data.materials:
            # assign to 1st material slot
            shadow_catcher.data.materials[0] = shadow_catcher_mat
        else:
            # no slots
            shadow_catcher.data.materials.append(shadow_catcher_mat)
                
        #camera location matrix
        track_pos = t["position"]
        mat_shadow_catcher = mathutils.Matrix.Translation((track_pos["x"],track_pos["y"],track_pos["z"] ))

        # apply matrix. 
        shadow_catcher.matrix_world = camera_offset @ mat_shadow_catcher

        #clear rotation
        shadow_catcher.rotation_euler = [0,0,0]
        
        shadow_catcher.parent = empty
    
    
def create_sun():
    scene = bpy.context.scene
    #---------create sun
    sun = None    
    for obj in scene.objects:
        if fnmatch.fnmatchcase(obj.name, "google_earth_sun"):
            sun = obj 
            break
        else:
            obj.select_set(False)
                
    if (sun == None):    
        bpy.context.scene.view_settings.view_transform = 'Standard'
        bpy.ops.object.light_add(type='SUN', align='WORLD', location=(0, 0, 0), rotation=(0, 0.785398, 0), scale=(1, 1, 1))
        sun = bpy.context.object


        sun.data.color = (1, 0.9, 0.571428)
        sun.data.energy = 4

        sun.name = "google_earth_sun"
    #-----------


#--------- set up world
#https://blender.stackexchange.com/questions/89096/setting-up-a-sky-bpy-context-world-none
def creat_world_mat():
    scene = bpy.context.scene
    
    new_world = bpy.data.worlds.new("google_earth_world")

    new_world.use_nodes = True
    tree = new_world.node_tree

    # clear default nodes
    for node in tree.nodes:
        tree.nodes.remove(node)

    # create ShaderNodeOutputWorld nodes
    out_put_node = tree.nodes.new('ShaderNodeOutputWorld')   
    out_put_node.location = 800,0

    #Background
    background = tree.nodes.new('ShaderNodeBackground')   
    background.location = 600,0

    #color_ramp
    color_ramp = tree.nodes.new('ShaderNodeValToRGB')   
    color_ramp.location = 300,0

    color_ramp.color_ramp.interpolation = 'B_SPLINE'

    color_ramp.color_ramp.elements[0].position = (0.195454)
    color_ramp.color_ramp.elements[1].position =(0.377273)
    color_ramp.color_ramp.elements.new(0.452273)
    color_ramp.color_ramp.elements.new(0.5)
    color_ramp.color_ramp.elements.new(0.531818)

    color_ramp.color_ramp.elements[0].color = [0.035,0.081,0.405,1]
    color_ramp.color_ramp.elements[1].color = [0.282,0.500,1.000,1]
    color_ramp.color_ramp.elements[2].color = [0.380,0.600,0.703,1]
    color_ramp.color_ramp.elements[3].color = [0.757,0.777,1.000,1]
    color_ramp.color_ramp.elements[4].color = [0,0,0,1]

    #math add 
    math_add = tree.nodes.new('ShaderNodeMath')   
    math_add.location = 100,0

    #map_range 
    map_range_top = tree.nodes.new('ShaderNodeMapRange')   
    map_range_top.location = -100,300
    map_range_top.inputs[3].default_value = 0.5
    map_range_top.inputs[4].default_value = 0

    map_range_bottom = tree.nodes.new('ShaderNodeMapRange')   
    map_range_bottom.location = -100,-300
    map_range_bottom.inputs[3].default_value = 0
    map_range_bottom.inputs[4].default_value = 0.5

    #gradient 
    gradient_top = tree.nodes.new('ShaderNodeTexGradient')   
    gradient_top.location = -300,300

    gradient_bottom = tree.nodes.new('ShaderNodeTexGradient')   
    gradient_bottom.location = -300,-300

    #mapping 
    mapping_top = tree.nodes.new('ShaderNodeMapping')   
    mapping_top.location = -600,300
    mapping_top.inputs[2].default_value[1] = 1.5708

    mapping_bottom = tree.nodes.new('ShaderNodeMapping')   
    mapping_bottom.location = -600,-300
    mapping_bottom.inputs[2].default_value[1] = -1.5708

    #texCoord
    texCoord = tree.nodes.new('ShaderNodeTexCoord')   
    texCoord.location = -800,0

    #link nodes

    links = tree.links
    link = links.new(texCoord.outputs[0], mapping_top.inputs[0])
    link = links.new(texCoord.outputs[0], mapping_bottom.inputs[0])

    link = links.new(mapping_top.outputs[0], gradient_top.inputs[0])
    link = links.new(mapping_bottom.outputs[0], gradient_bottom.inputs[0])

    link = links.new(gradient_top.outputs[0], map_range_top.inputs[0])
    link = links.new(gradient_bottom.outputs[0], map_range_bottom.inputs[0])

    link = links.new(map_range_top.outputs[0], math_add.inputs[0])
    link = links.new(map_range_bottom.outputs[0], math_add.inputs[1])

    link = links.new(math_add.outputs[0], color_ramp.inputs[0])

    link = links.new(color_ramp.outputs[0], background.inputs[0])

    link = links.new(background.outputs[0], out_put_node.inputs[0])

    scene.world = new_world
    #----------
   
    
#------ global var
clearMatrix = mathutils.Matrix(((1,0,0,0),
    (0,1,0,0),
    (0,0,1,0) ,
    (0,0,0,1)))
   
folder_loc = ""
folderName = ""
rendered_frames_loc = ""

empty = None
camera = None
move = None
shadow_catcher_mat = None
#-----------------


def google_earth_studio(f):


    global folder_loc, folderName, rendered_frames_loc, empty, camera, move, shadow_catcher_mat  

    folder_loc, folderName, rendered_frames_loc = folder(f)
        
    #set up composeter 
    composeter()

    #-----create empty
    empty = creat_empty()

    #-----create camera
    camera = creat_camera()

    #-----parent camera to empty
    camera.parent = empty
    #-------------

    move = get_json()

    moveCamera()

    shadow_catcher_mat = create_mat()

    create_tracked_points()

    create_sun()

    creat_world_mat()
    
    
