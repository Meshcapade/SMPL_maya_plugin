"""
Copyright 2021 Meshcapade GmbH and Max Planck Gesellschaft.  All rights reserved.

More information about the SMPL model research project is available here http://smpl.is.tue.mpg
For SMPL Model commercial use options, please visit https://meshcapade.com/infopages/licensing.html
For comments or questions, please email us at: support@meshcapade.com


Current versions supported:
--------------------------
Mac OSX: Maya 2014+
Windows: Maya 2014+


Dependencies:
------------
Numpy is required for running this script. Numpy is a python module that
can be installed following the instructions given here:
http://docs.scipy.org/doc/numpy/user/install.html

or here:
http://blog.animateshmanimate.com/post/115538511578/python-numpy-and-maya-osx-and-windows

Please make sure you have numpy installed on your computer and accessible through Maya's python.
We are working towards removing this dependency. 


About the Script:
-----------------
The script displays a UI to apply SMPL's shape and pose blendshapes and to adjust the skeleton to new body shapes.
Load this plugin into Maya. It will create a window with 3 options:

1- Apply Pose Blend Shapes to Current Frame: 
    If you repose the model in Maya, then click this to 
    compute and apply the pose blend shapes in the current frame. 
    You can als ochoose whether or not to set the keyframes for the 
    pose blendshapes. Check the 'Reset Keyframes' checkbox if you 
    would like to lock blendShape values at given frame by setting 
    a keyframe. 

2- Apply Pose Blend Shapes to Frames in above Range: 
    Specify a range of frames in an animation and then compute/apply 
    the pose blendshapes for all the frames in range. Check the 
    'Reset Keyframes' checkbox if you would like to lock blendShape 
    values at given frame range by setting a keyframe at each frame in the 
    given range.
    
3- Set Mesh to Bind-Pose & Recompute Skeleton: 
    When you edit the shape blend shapes to change body shape the 
    skeleton will no longer be correct.  Click first button to set the 
    mesh into the bind-pose. Next, click this to 'Recompute Skeleton' 
    to recompute the skeleton rig to match the new body shape.

Always make sure to cilck on the mesh in the 3D view to select it before 
using any of the functions in the plugin. Select only the mesh of the model 
you want to update and then click the appropriate button on the UI.

"""

import maya.cmds as cmds
# import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
from functools import partial
import sys
# import pickle
from os.path import exists, split
import logging

VERSION = '1.0.6'
SCRIPT_NAME = 'SMPL_maya_plugin'

## TODO:
## 1. Show error messages in plugin window instead of maya script editor
try:
    import numpy as np
except:
    python_version = sys.version_info
    sys.path.append('/usr/local/lib/python%d.%d/site-packages/' % (python_version.major, python_version.minor))
    import numpy as np

units = 'm'
if units == 'mm':
    scale_up = 1000.
elif units == 'cm':
    scale_up = 100.
else:
    scale_up = 1.


class ui:
    def __init__(self, winName='SMPL_model_maya_script'):
        self.winTitle = 'SMPL - Rigging & Pose Corrections Toolbox for Maya'
        self.winName = winName

        self.j_names = {
            0: 'Pelvis',
            1: 'L_Hip', 4: 'L_Knee', 7: 'L_Ankle', 10: 'L_Foot',
            2: 'R_Hip', 5: 'R_Knee', 8: 'R_Ankle', 11: 'R_Foot',
            3: 'Spine1', 6: 'Spine2', 9: 'Spine3', 12: 'Neck', 15: 'Head',
            13: 'L_Collar', 16: 'L_Shoulder', 18: 'L_Elbow', 20: 'L_Wrist',
            14: 'R_Collar', 17: 'R_Shoulder', 19: 'R_Elbow', 21: 'R_Wrist',
        }

    def create(self):
        if cmds.window(self.winName, exists=True):
            cmds.deleteUI(self.winName)

        cmds.window(self.winName, title=self.winTitle)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAlign='center')
        cmds.separator(height=5, style='none')

        ## POSE BLEND SHAPES FOR CURRENT FRAME
        cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 20), (2, 'both', 10)])
        self.frame_checkbox = cmds.checkBox(label=' Reset \n Keyframes', align='center', value=True)
        #current_frame_func = lambda self: self.applyBlendshapes(self)
        #self.bttn_blend = cmds.button(label='Apply Pose Blend Shapes to\nCurrent Frame',
        #                             c=current_frame_func, width=170, height=50)

        self.bttn_blend_current = cmds.button(label='Apply Pose Blend Shapes to\nCurrent Frame',
                                     c=self.applyBlendshapes, width=170, height=50)

        cmds.setParent('..')
        cmds.separator(height=10, style='in')

        ## POSE BLENDSHAPES FOR RANGE
        cmds.rowLayout(numberOfColumns=1, columnAttach=[(1, 'both', -30)])
        self.framesField = cmds.intFieldGrp(numberOfFields=2, label='Frame Range', value1=0, value2=10)
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 20), (2, 'both', 10)])
        self.range_checkbox = cmds.checkBox(label=' Reset \n Keyframes', align='center', value=True)
        #range_frame_func = partial(ui.applyBlendshapes, self, use_timeline=True)
        range_frame_func = lambda *args: self.applyBlendshapes(use_timeline=True)
        self.bttn_blend_range = cmds.button(label='Apply Pose Blend Shapes to\n Frames in above Range ',
                                     c=range_frame_func, width=170, height=50)
        cmds.setParent('..')
        cmds.separator(height=10, style='in')

        ## RECOMPUTE SKELETON
        cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 35), (2, 'both', 10)])
        Tpose_func = lambda *args: ui.getTpose()
        self.bttn_Tpose = cmds.button(label='Set Mesh to \n Bind-Pose', c=Tpose_func, width=120, height=50)
        rerig_func = lambda *args: self.reRig()
        self.bttn_rerig = cmds.button(label='Recompute \n Skeleton', c=rerig_func, width=120, height=50)
        cmds.setParent('..')
        cmds.separator(height=5, style='none')

        cmds.showWindow(self.winName)

    @staticmethod
    def has_no_deformer_of_type(
            maya_geo,
            deformer_type='blendShape'
    ):
        """
        :param maya_geo: transform parent or child geo shape of a Maya geo
        :param deformer_type: the type of the deformer the user wants to check if maya_geo is deformed by.
        :return:
            True if maya_geo is not deformed by any deformer of deformer_type
            False otherwise
        """

        candidate = ui.get_associated_deformer(
            maya_geo,
            deformer_type=deformer_type
        )

        result = True
        if candidate and cmds.objExists(candidate) and cmds.nodeType(candidate) == deformer_type:
            result = False

        return result, candidate

    @staticmethod
    def is_not_skinned(maya_mesh):
        result = ui.has_no_deformer_of_type(
            maya_mesh,
            deformer_type='skinCluster'
        )

        return result

    @staticmethod
    def has_no_blendShape(maya_mesh):
        result = ui.has_no_deformer_of_type(
            maya_mesh,
            deformer_type='blendShape'
        )

        return result

    @staticmethod
    def get_LUT_deformer_to_geo(
            deformer_type='blendShape'
    ):
        deformerLUT = {}
        all_deformers_of_type = cmds.ls(type=deformer_type)
        deformer_geomGetter = partial(cmds.deformer, q=True, geometry=True)
        [deformerLUT.update({x: deformer_geomGetter(x)}) for x in all_deformers_of_type]

        return deformerLUT

    @staticmethod
    def get_LUT_blendShape_to_geo():
        result = ui.get_LUT_deformer_to_geo(
            deformer_type='blendShape'
        )

        return result

    @staticmethod
    def get_LUT_skinCluster_to_geo():
        result = ui.get_LUT_deformer_to_geo(
            deformer_type='skinCluster'
        )

        return result

    @staticmethod
    def get_LUT_geo_to_deformer(
            deformer_type='blendShape',
            deformer_LUT=None
    ):
        if not deformer_LUT:
            deformer_LUT = ui.get_LUT_deformer_to_geo(
                deformer_type=deformer_type
            )

        deformer_reverse_LUT = {}
        for deformer, geometries in deformer_LUT.items():
            for current_geo in geometries:
                if current_geo not in deformer_reverse_LUT:
                    deformer_reverse_LUT.update({current_geo: set()})

                deformer_reverse_LUT[current_geo].add(deformer)

        return deformer_reverse_LUT

    @staticmethod
    def get_LUT_geo_to_blendShape(
            blendShape_LUT=None
    ):
        result = ui.get_LUT_geo_to_deformer(
            deformer_type='blendShape',
            deformer_LUT=blendShape_LUT
        )

        return result

    @staticmethod
    def get_LUT_geo_to_skinCluster(
            skinCluster_LUT=None
    ):
        result = ui.get_LUT_geo_to_deformer(
            deformer_type='skinCluster',
            deformer_LUT=skinCluster_LUT
        )

        return result

    @staticmethod
    def get_info_geo(
            maya_geo
    ):
        """
        :param maya_geo: a transform parent of a geo, or a geo shape child in Maya.
        :return: a dictionary with the transform parent and all the geo shape children
        """
        geo_parent = None
        if cmds.nodeType(maya_geo) == 'transform':
            # maya_geo is a transform, so assume it is the parent of geo geometry shape nodes:
            geo_parent = maya_geo
        else:
            # maya_geo is not a transform so assume it is the sibling of geo geometry shape nodes:
            geo_parent = cmds.listRelatives(maya_geo, parent=True)[0]

        geo_shapes = cmds.listRelatives(geo_parent, children=True, shapes=True)
        geo_shapes = cmds.ls(geo_shapes, type='geometryShape')

        shape_type = None
        if geo_shapes and len(geo_shapes) > 0:
            shape_type = cmds.nodeType(geo_shapes[0])

        result = {}
        result.update({'parent': geo_parent})
        result.update({'shapes': geo_shapes})
        result.update({'shape_type': shape_type})

        return result

    @staticmethod
    def get_info_mesh(
            maya_mesh
    ):
        """
        :param maya_mesh:
        :return: a dictionary of information about maya_mesh(transform parent, mesh shapes)
        """
        result = ui.get_info_geo(
            maya_mesh
        )

        if result['shape_type'] != 'mesh':
            logging.error('No mesh shapes found for geo:  "%s"', maya_mesh)
            result = None

        return result


    @staticmethod
    def get_associated_deformer(
            maya_geo,
            deformer_type='blendShape'
    ):

        objset = cmds.listConnections(maya_geo, type='objectSet')

        result = None
        if objset:
            result = cmds.listConnections(objset, type=deformer_type)

            if result and cmds.objExists(result[0]):
                result = result[0]
                return result

        # if the evaluation is here:  it means a deformer
        # could not be found from deformer membership sets(ie 'objset').
        # Starting ~Maya 2020:  Autodesk started doing away
        # with sets membership preferring "componentTags".
        # ???
        # Anyway:  we'll see if we can find a command to
        # just return the deformer either way:
        deformer_reverse_LUT = ui.get_LUT_geo_to_deformer(
            deformer_type=deformer_type
        )

        geo_info = ui.get_info_geo(
            maya_geo
        )

        geo_parent_and_shapes = [geo_info['parent']]
        geo_parent_and_shapes.extend(geo_info['shapes'])
        geo_parent_and_shapes_set = set(geo_parent_and_shapes)

        result = None
        for elem in geo_parent_and_shapes_set:
            if elem not in deformer_reverse_LUT:
                continue

            # at this point in the evaluation: elem is in deformer_reverse_LUT:
            # so:  return the deformer at this dictionary element:
            result = list(deformer_reverse_LUT[elem])
            if result:
                result = result[0]

            break

        return result

    def applyBlendshapes(
            self,
            use_timeline=False,
            # inst=None,
    ):
        """
        Apply Blendshapes for the given range. If no range is given, apply blendshapes to current frame.
        The script allows user to choose whether or not to remove any existing keyframes from the pose blendshapes
        and set new keyframes for the updated pose blendshapes for the frame (or frames) specified.
        :param use_timeline:  There used to be a parameter called frame_range, PyCharm was complaining
        because an argument with that name does not exist.  So:  here is documentation for use_timeline
        instead.
        :return: None
        """
        rekey = False
        if use_timeline:
            rekey = cmds.checkBox(self.range_checkbox, query=True, value=True)
        else:
            rekey = cmds.checkBox(self.frame_checkbox, query=True, value=True)

        selection = cmds.ls(selection=True, showType=True)

        if len(selection) != 2:
            print('\nError: select only the mesh')
            return

        if selection[1] != 'transform' and selection[1] != 'mesh':
            print("\nError: Please select a mesh object")
            return

        maya_mesh = selection[0] if selection[1] == 'mesh' else cmds.listRelatives(selection[0], type='mesh')[0]

        is_not_skinned, lbs_cluster = ui.is_not_skinned(maya_mesh)
        if is_not_skinned:
            print('\nError: Selected object has no skinCluster node (skeleton is not attached)')
            return

        has_no_blendShape, blendshape_node = ui.has_no_blendShape(maya_mesh)
        if has_no_blendShape:
            print('\nError: Selected object has no blendShape node')
            return

        # TODO:  charID immediately below seems unused:  remove?
        # charID = cmds.listRelatives(maya_mesh, parent=True)[0]

        # Backward compatibility with v1.0.3
        bonePrefix, MODEL_TYPE = self.boneSetup(lbs_cluster)

        if use_timeline:
            f1 = int(cmds.intFieldGrp(self.framesField, query=True, value1=True))
            f2 = int(cmds.intFieldGrp(self.framesField, query=True, value2=True))
            frame_range = [f1, f2 + 1]
            cmds.playbackOptions(min=frame_range[0], max=frame_range[-1], maxPlaybackSpeed=0)
        else:
            currentTime = int(cmds.currentTime(query=True))
            frame_range = [currentTime, currentTime + 1]
        print('frame_range: ', frame_range)

        ## get all bones attached to skin (that excludes root)
        # TODO:  maya_jnt_tree immediately below is unused:  remove?:
        # maya_jnt_tree = cmds.skinCluster(lbs_cluster, query=True, wi=True)
        for frame in range(frame_range[0], frame_range[-1]):
            cmds.currentTime(frame)

            ## Set poseblends for all joints excluding pelvis (there are no blendshapes for pelvis)
            for jidx, j_name in self.j_names.items():
                bone = '%s_%s' % (bonePrefix, j_name)
                if jidx > 0 and (frame_range[-1] - frame_range[0]) > 0:
                    ## Get original 4x4 maya rotation matrix from bone
                    cmds.select(bone, replace=True)
                    real_m = np.array(cmds.xform(query=True, matrix=True)).reshape((4, 4)).T
                    for mi, rot_element in enumerate((real_m[:3, :3] - np.eye(3)).ravel()):
                        bidx = (9 * (jidx - 1)) + mi
                        cmds.setAttr('%s.Pose%03d' % (blendshape_node, bidx), rot_element * scale_up)
                        # cmds.blendShape(blendshape_node, edit=True, w=[(bidx, rot_element * scale_up)])
                        if rekey:
                            cmds.setKeyframe('%s.Pose%03d' % (blendshape_node, bidx), breakdown=False,
                                             controlPoints=False, shape=False)
                # Ignoring extraneous blendshapes for FBX 
                if jidx == 21:
                    break

            ## clear selection
            # cmds.select( clear=True )
            cmds.select(maya_mesh, replace=True)

    @staticmethod
    def getVtxPos(shapeNode):
        """
        Get the vertices of a maya mesh 'shapeNode'
        :param  shapeNode: name of maya mesh
        :return vertices of the maya mesh object
        """
        vtxWorldPosition = []
        vtxIndexList = cmds.getAttr(shapeNode + ".vrts", multiIndices=True)
        for i in vtxIndexList:
            current_vtx = str(shapeNode) + ".pnts[" + str(i) + "]"
            curPointPosition = cmds.xform(
                current_vtx,
                query=True,
                translation=True,
                worldSpace=True
            )  # [1.1269192869360154, 4.5408735275268555, 1.3387055339628269]
            vtxWorldPosition.append(curPointPosition)
        return vtxWorldPosition

    @staticmethod
    def getTpose():
        """
        Set the Mesh & pose blendshapes to 0
        :return: None
        """
        selection = cmds.ls(selection=True, showType=True)

        if len(selection) != 2:
            print('\nError: select only the mesh')
            return

        if selection[1] != 'transform' and selection[1] != 'mesh':
            print("\nError: Please select a mesh object")
            return

        maya_mesh = selection[0] if selection[1] == 'mesh' else cmds.listRelatives(selection[0], type='mesh')[0]

        is_not_skinned, lbs_cluster = ui.is_not_skinned(maya_mesh)
        if is_not_skinned:
            print('\nError: Selected object has no Skin Cluster node (skeleton is not attached)')
            return

        has_no_blendShape, blendshape_node = ui.has_no_blendShape(maya_mesh)
        if has_no_blendShape:
            print('\nError: Selected object has no blendShape node')
            return

        ## get all bones including root
        bones = cmds.listConnections(lbs_cluster, type='joint')

        ## Set all joints to 0 & pose blendShapes to 0 (get T-pose) 
        for bidx, currentBone in enumerate(bones):
            cmds.rotate(0, 0, 0, currentBone)
            if bidx < 23:
                for pidx in range(9):
                    cmds.setAttr('%s.Pose%03d' % (blendshape_node, (9 * bidx) + pidx), 0)

    def reRig(self):
        """
        Create a skeleton using the selected mesh and joint regressor
        Requires 'joints_mat_<MODEL_TYPE>.npz' file. 
        Please make sure the 'joints_mat_<MODEL_TYPE>.npz' file is in the same location as this plugin file.
        :return: None
        """

        ## Get selection
        selection = cmds.ls(selection=True, showType=True)

        ## Check if selected object is only one mesh & return if not
        if len(selection) != 2:
            print('\nError: select only the mesh')
            return
        if selection[1] != 'transform' and selection[1] != 'mesh':
            print("\nError: Please select a mesh object")
            return
        maya_mesh = selection[0] if selection[1] == 'mesh' else cmds.listRelatives(selection[0], type='mesh')[0]

        ## Get skinning node & return if missing
        is_not_skinned, lbs_cluster = ui.is_not_skinned(maya_mesh)
        if is_not_skinned:
            print('\nError: Selected object has no Skin Cluster node (skeleton is not attached)')
            return

        #has_no_blendShape, blendshape_node = ui.has_no_blendShape(maya_mesh)
        #if has_no_blendShape:
        #    print('\nError: Selected object has no blendShape node')
        #    return


        ## Get model-specific parameters: name, joint-names, blendshapes node
        # TODO:  seems:
        #  charID
        #  blendshape_node
        #  immediately below are unused:  remove???
        # charID = cmds.listRelatives(maya_mesh, parent=True)[0]
        # blendshape_node = self.get_associated_blendShape(maya_mesh, objset=objset)

        ## Get directory from where plugin is loaded
        plugin_dir = split(cmds.pluginInfo(SCRIPT_NAME, q=True, path=True))[0]

        # Find model_type and update bone setup
        bonePrefix, MODEL_TYPE = self.boneSetup(lbs_cluster)

        ## Find joints_mat_v*.npz file & return if missing
        joints_mat_path = '%s/joints_mat_%s.npz' % (plugin_dir, MODEL_TYPE)
        if not exists(joints_mat_path):
            current_err_str = '\nError: Missing \')joints_mat_%s.npz\' file.' % MODEL_TYPE
            print(current_err_str)
            current_err_str = ''
            current_err_str += 'Please make sure the \')joints_mat_%s.npz\' file ' % MODEL_TYPE
            current_err_str += 'is in the same location as the SMPL_maya_plugin.py file.'
            print(current_err_str)
            return

        ## Get new joint heirarchy
        joints_mat = np.load(joints_mat_path)

        ## Get mesh vertices
        mesh_verts = self.getVtxPos(maya_mesh)
        gender = 'male' if maya_mesh[0] == 'm' else 'female'

        ## Get new joints
        num_verts_to_use = len(joints_mat[gender][1])
        mesh_verts_to_dot = np.asarray(mesh_verts[:num_verts_to_use])
        subject_j = joints_mat[gender].dot(mesh_verts_to_dot)

        ## Lock skinning and set new joint locations
        cmds.skinCluster(maya_mesh, edit=True, moveJointsMode=True)
        for j_idx, j_name in self.j_names.items():
            currentBone = '%s_%s' % (bonePrefix, j_name)
            cmds.move(subject_j[j_idx][0], subject_j[j_idx][1], subject_j[j_idx][2], currentBone)
        cmds.skinCluster(maya_mesh, edit=True, moveJointsMode=False)

    def boneSetup(self, lbs_cluster):
        bones = cmds.listConnections(lbs_cluster, type='joint')

        if len(bones) <= 75:
            MODEL_TYPE = 'SMPL'
        elif len(bones) <= 156:
            MODEL_TYPE = 'SMPLH'
        elif len(bones) <= 165:
            MODEL_TYPE = 'SMPLX'
        else:
            raise TypeError("Model type is not supported")

        print('num_bones:', len(bones))
        print('MODEL_TYPE:', MODEL_TYPE)
        if MODEL_TYPE == 'SMPLH':
            self.j_names.update({
                22: 'lindex0', 23: 'lindex1', 24: 'lindex2',
                25: 'lmiddle0', 26: 'lmiddle1', 27: 'lmiddle2',
                28: 'lpinky0', 29: 'lpinky1', 30: 'lpinky2',
                31: 'lring0', 32: 'lring1', 33: 'lring2',
                34: 'lthumb0', 35: 'lthumb1', 36: 'lthumb2',
                37: 'rindex0', 38: 'rindex1', 39: 'rindex2',
                40: 'rmiddle0', 41: 'rmiddle1', 42: 'rmiddle2',
                43: 'rpinky0', 44: 'rpinky1', 45: 'rpinky2',
                46: 'rring0', 47: 'rring1', 48: 'rring2',
                49: 'rthumb0', 50: 'rthumb1', 51: 'rthumb2'})
        elif MODEL_TYPE == 'SMPLX':
            self.j_names.update({
                22: 'Jaw', 23: 'L_eye', 24: 'R_eye',
                25: 'lindex0', 26: 'lindex1', 27: 'lindex2',
                28: 'lmiddle0', 29: 'lmiddle1', 30: 'lmiddle2',
                31: 'lpinky0', 32: 'lpinky1', 33: 'lpinky2',
                34: 'lring0', 35: 'lring1', 36: 'lring2',
                37: 'lthumb0', 38: 'lthumb1', 39: 'lthumb2',
                40: 'rindex0', 41: 'rindex1', 42: 'rindex2',
                43: 'rmiddle0', 44: 'rmiddle1', 45: 'rmiddle2',
                46: 'rpinky0', 47: 'rpinky1', 48: 'rpinky2',
                49: 'rring0', 50: 'rring1', 51: 'rring2',
                52: 'rthumb0', 53: 'rthumb1', 54: 'rthumb2'
            })
        else:
            self.j_names.update({
                22: 'L_Hand', 23: 'R_Hand',
            })
        rootBone = [b for b in bones if 'root' in b]
        if not rootBone:
            rootBone = [b for b in bones if 'Pelvis' in b]
            bonePrefix = rootBone[0].replace('_Pelvis', '')
        else:
            bonePrefix = rootBone[0].replace('_root', '')
        return bonePrefix, MODEL_TYPE


inst = ui()
inst.create()
kPluginCmdName = "SMPL_maya_plugin"


# Command
class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    # Invoked when the command is run.
    def doIt(self, argList):
        print("..Loading: SMPL_maya_plugin")


# Creator
def cmdCreator():
    return OpenMayaMPx.asMPxPtr(scriptedCommand())


# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand(kPluginCmdName, cmdCreator)
    except:
        sys.stderr.write("Failed to register command: %s\n" % kPluginCmdName)
        raise


# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(kPluginCmdName)
    except:
        sys.stderr.write("Failed to unregister command: %s\n" % kPluginCmdName)
