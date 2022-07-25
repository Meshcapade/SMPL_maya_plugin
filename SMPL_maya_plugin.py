"""
Copyright 2021 Meshcapade GmbH and Max Planck Gesellschaft.  All rights reserved.

More information about the SMPL model research project is available here http://smpl.is.tue.mpg
For SMPL Model commercial use options, please visit https://meshcapade.com/infopages/licensing.html
For comments or questions, please email us at: support@meshcapade.com


Current versions supported:
---------------------------
Maya 2023+


About the Script:
----------------
The script displays a UI to apply the pose-corrective blendshapes for SMPL, SMPLH, SMPLX and STAR models in Maya. Load this plugin into Maya. It will create a window with 3 options:

1- Apply Pose Blend Shapes to Current Frame: 
    If you repose the model in Maya, then click this to 
    compute and apply the pose blend shapes in the current frame. 
    You can also choose whether or not to set the keyframes for the 
    pose blendshapes. Check the 'Reset Keyframes' checkbox if you 
    would like to lock blendShape values at given frame by setting 
    a keyframe. 

2- Apply Pose Blend Shapes to Frames in above Range: 
    Specify a range of frames in an animation and then compute/apply 
    the pose blendshapes for all the frames in range. Check the 
    'Reset Keyframes' checkbox if you would like to lock blendShape 
    values at given frame range by setting a keyframe at each frame in the 
    given range.
    
3- Make Pose Blend Shapes fire interactively: 
    Click this button to turn on automatic pose-correctives for any SMPL(-/H/X) or STAR rigged mesh. Once this is set to ON, then any time you repose the SMPL model, the pose-correctives will automatically be applied to the mesh.

Always make sure to click on the mesh in the 3D view to select it before 
using any of the functions in the plugin. Select only the mesh of the model 
you want to update and then click the appropriate button on the UI.

"""

import maya.cmds as cmds
import maya.OpenMaya as oM
import maya.OpenMayaMPx as OpenMayaMPx
from functools import partial
import sys
# import pickle
from os.path import exists, split
import logging

# try to load any necessary Maya plugins here:
plugins = [
    'mde_poseblends_driver',
    'mde_py_poseblends_driver'
]
for plugin in plugins:
    if cmds.pluginInfo(plugin, query=True, loaded=True):
        continue

    try:
        cmds.loadPlugin(plugin)
    except RuntimeError as e:
        print(e)
        continue

VERSION = '1.0.6'
SCRIPT_NAME = 'SMPL_maya_plugin'

# # TODO:
# # 1. Show error messages in plugin window instead of maya script editor
# try:
#     import numpy as np
# except:
#     python_version = sys.version_info
#     sys.path.append('/usr/local/lib/python%d.%d/site-packages/' % (python_version.major, python_version.minor))
#     import numpy as np

units = 'm'
if units == 'mm':
    scale_up = 1000.
elif units == 'cm':
    scale_up = 100.
else:
    scale_up = 1.

class SMPL_generic_ops:
    @staticmethod
    def get_base_common_joint_names():
        """
        These are joint names common to the SMPL flavors:
        -SMPL
        -SMPLH
        -SMPLX
        It is not a complete list of joints for any of those flavors,
        though.
        """
        
        # Initialize result with the SMPL default values
        result = {
            0: 'Pelvis',
            1: 'L_Hip', 4: 'L_Knee', 7: 'L_Ankle', 10: 'L_Foot',
            2: 'R_Hip', 5: 'R_Knee', 8: 'R_Ankle', 11: 'R_Foot',
            3: 'Spine1', 6: 'Spine2', 9: 'Spine3', 12: 'Neck', 15: 'Head',
            13: 'L_Collar', 16: 'L_Shoulder', 18: 'L_Elbow', 20: 'L_Wrist',
            14: 'R_Collar', 17: 'R_Shoulder', 19: 'R_Elbow', 21: 'R_Wrist',
        }
        
        return result
        
        
    @staticmethod
    def get_joint_names(
        MODEL_TYPE="SMPL"
    ):
        """
        Given a SMPL MODEL_TYPE:  return the SMPL:
        -joint_names
        :param MODEL_TYPE: a string, the result of get_MODEL_TYPE.  Defaults to 'SMPL'.
        :return: a dictionary keyed on integers with string elements representing the names of joints in the SMPL model.
        """
        # Initialize result with the SMPL default values
        result = SMPL_generic_ops.get_base_common_joint_names()
        
        if(MODEL_TYPE == 'STAR'):
            # read the joint names as if for SMPL:
            result = SMPL_generic_ops.get_joint_names('SMPL')
            
            return result
            
        # Modify/augment result based on MODEL_TYPE:
        if MODEL_TYPE == 'SMPLH':
            result.update({
                22: 'lindex0', 23: 'lindex1', 24: 'lindex2',
                25: 'lmiddle0', 26: 'lmiddle1', 27: 'lmiddle2',
                28: 'lpinky0', 29: 'lpinky1', 30: 'lpinky2',
                31: 'lring0', 32: 'lring1', 33: 'lring2',
                34: 'lthumb0', 35: 'lthumb1', 36: 'lthumb2',
                37: 'rindex0', 38: 'rindex1', 39: 'rindex2',
                40: 'rmiddle0', 41: 'rmiddle1', 42: 'rmiddle2',
                43: 'rpinky0', 44: 'rpinky1', 45: 'rpinky2',
                46: 'rring0', 47: 'rring1', 48: 'rring2',
                49: 'rthumb0', 50: 'rthumb1', 51: 'rthumb2'
            })
        elif MODEL_TYPE == 'SMPLX':
            # read the joint names as if for SMPLH:
            result_SMPLH = SMPL_generic_ops.get_joint_names('SMPLH')
            
            result.update({
                22: 'Jaw', 23: 'L_eye', 24: 'R_eye'
            })
            
            # use the same values as in SMPLH from 22 -> 52(ie the finger joints),
            # but with key incremented by 3(ie to make room for the Jaw and
            # L|R_eye joints added immediately above):
            [result.update({ii + 3:result_SMPLH[ii]}) for ii in range(22, max(result_SMPLH.keys()) + 1)]
        else:
            result.update({
                22: 'L_Hand', 23: 'R_Hand',
            })
            
        return result

    @staticmethod
    def get_MODEL_TYPE(
        joints, 
        num_blend_shapes
    ):
        """
        Given a list of SMPL joint names:  return the SMPL:
        -MODEL_TYPE
        :param joints: a list of joint names of joints in the scene.  This should be a list of unique(ie non-repeating) names.
        :return: string representing the SMPL MODEL_TYPE
        """
        num_joints = len(set(joints))
        logging.debug('num_joints:', num_joints)

        num_blend_shapes_per_joint = float(num_blend_shapes) / float(num_joints)
        logging.debug('num_blend_shapes:', num_blend_shapes)
        logging.debug('num_blend_shapes_per_joint:', num_blend_shapes_per_joint)
        
        if num_joints <= 24:
            if(num_blend_shapes_per_joint < 6):
                # for STAR:  should be 4 blendShape targets per joint, but no 
                # blendShape targets are defined for the root joint.
                # for any SMPL-related models:  should be 9 blendShape targets
                # per joint, but no blendShape targets are defined for 
                # the root joint.
                # So:  if it's less than 6 targets/joint:  STAR.
                MODEL_TYPE = 'STAR'
            else:
                MODEL_TYPE = 'SMPL'
        elif num_joints <= 52:
            MODEL_TYPE = 'SMPLH'
        elif num_joints <= 55:
            MODEL_TYPE = 'SMPLX'
        else:
            raise TypeError("Model type is not supported")
        
        return MODEL_TYPE

    @staticmethod
    def get_root_joint_prefix(joints):
        """
        Given a list of SMPL joint names:  return the SMPL:
        -root joint_prefix
        :param joints: a list of joint names.
        :return: string representing the SMPL root joint_prefix
        """
        joint_prefix = None
        rootJoint = [b for b in joints if 'root' in b]
        if not rootJoint:
            rootJoint = [b for b in joints if 'Pelvis' in b]
            joint_prefix = rootJoint[0].replace('_Pelvis', '')
        else:
            joint_prefix = rootJoint[0].replace('_root', '')

        return joint_prefix

    @staticmethod
    def get_joint_info(
            joints,
            num_blend_shape_targets
    ):
        """
        Given a list of joint names:  return the SMPL:
        -MODEL_TYPE
        -joint_names
        -root_joint_prefix
        :param joints: a list of joint names.
        :return: a dictionary containing the joint info.
        """
        
        MODEL_TYPE = SMPL_generic_ops.get_MODEL_TYPE(
            joints,
            num_blend_shape_targets
        )
        logging.debug('MODEL_TYPE:', MODEL_TYPE)

        joint_names = SMPL_generic_ops.get_joint_names(
            MODEL_TYPE
        )

        root_joint_prefix = SMPL_generic_ops.get_root_joint_prefix(joints)

        result = {}
        result.update({'root_joint_prefix':root_joint_prefix})
        result.update({'MODEL_TYPE':MODEL_TYPE})
        result.update({'joint_names':joint_names})
        
        return result


class maya_ops:
    
    @staticmethod
    def set_MMatrix_cell(
        matrix, 
        value, 
        row, 
        column
    ):
        oM.MScriptUtil.setDoubleArray(
            matrix[row], 
            column,
            value
        )
        
    @staticmethod
    def from_1x16_list_to_4x4_MMatrix(
        list_1x16,
        transpose = False
    ):
        result = oM.MMatrix()
        
        index1D = 0
        for ii in range(0, 4):
            for jj in range(0, 4):
                row_index = ii
                column_index = jj
                if(transpose):
                    row_index = jj
                    column_index = ii
                    
                maya_ops.set_MMatrix_cell(
                    result,
                    list_1x16[index1D],
                    row_index,
                    column_index
                )
                index1D += 1
                
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
    def get_LUT_geo_to_deformer(
            deformer_type='blendShape',
            deformer_LUT=None
    ):
        if not deformer_LUT:
            deformer_LUT = maya_ops.get_LUT_deformer_to_geo(
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
        deformer_reverse_LUT = maya_ops.get_LUT_geo_to_deformer(
            deformer_type=deformer_type
        )

        geo_info = maya_ops.get_info_geo(
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

        candidate = maya_ops.get_associated_deformer(
            maya_geo,
            deformer_type=deformer_type
        )

        result = True
        if candidate and cmds.objExists(candidate) and cmds.nodeType(candidate) == deformer_type:
            result = False

        return result, candidate

    @staticmethod
    def is_not_skinned(maya_mesh):
        result = maya_ops.has_no_deformer_of_type(
            maya_mesh,
            deformer_type='skinCluster'
        )

        return result

    @staticmethod
    def has_no_blendShape(maya_mesh):
        result = maya_ops.has_no_deformer_of_type(
            maya_mesh,
            deformer_type='blendShape'
        )

        return result

    @staticmethod
    def get_LUT_blendShape_to_geo():
        result = maya_ops.get_LUT_deformer_to_geo(
            deformer_type='blendShape'
        )

        return result

    @staticmethod
    def get_LUT_skinCluster_to_geo():
        result = maya_ops.get_LUT_deformer_to_geo(
            deformer_type='skinCluster'
        )

        return result

    @staticmethod
    def get_LUT_geo_to_blendShape(
            blendShape_LUT=None
    ):
        result = maya_ops.get_LUT_geo_to_deformer(
            deformer_type='blendShape',
            deformer_LUT=blendShape_LUT
        )

        return result

    @staticmethod
    def get_LUT_geo_to_skinCluster(
            skinCluster_LUT=None
    ):
        result = maya_ops.get_LUT_geo_to_deformer(
            deformer_type='skinCluster',
            deformer_LUT=skinCluster_LUT
        )

        return result

    @staticmethod
    def get_info_mesh(
            maya_mesh
    ):
        """
        :param maya_mesh:
        :return: a dictionary of information about maya_mesh(transform parent, mesh shapes)
        """
        result = maya_ops.get_info_geo(
            maya_mesh
        )

        if result['shape_type'] != 'mesh':
            logging.error('No mesh shapes found for geo:  "%s"', maya_mesh)
            result = None

        return result

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


def get_SMPL_blendShape_weight_attr_alias(
    start_weight_index,
    offset_index,
    pattern = 'Pose%03d'
):
    """
    Any time this library needs the name of a blendShape's weight attr:  it should get it here.

    The default looks like:
    Pose(start_weight_index + offset_index)

    :param start_weight_index:  the 0-based index from which to start the current weights.
    :param offset_index:  integer offset from start_weight_index
    :param pattern:  a string with an integer conversion somewhere which will be replaced by the sum of start_weight_index and offset_index.
    :return: A string representing the aliased name of an element of blendShape_node.weights[<some index>].
    """
    result = pattern % (start_weight_index + offset_index)

    return result


class mde_poseblends_driver_ops:

    @staticmethod
    def connect_input_attrs_joint_single(
            mde_poseblends_driver_node,
            joint,
            joint_index,
            MODEL_TYPE = 'SMPL'
    ):
        """
        Maya joint matrices -> mde_poseblends_driver_node.inputJoint[joint_index]

        Connect joint(a Maya transform) to the joint_indexth entry of the inputJoint attribute of
        mde_poseblends_driver_node
        :param joint:  the name of a transform node in the Maya scene.
        :param joint_index:  the index into the input attribute:   mde_poseblends_driver_node + '.' + 'inputJoint'
        :param mde_poseblends_driver_node:  the node into whose inputs to connect joint's matrix(ces) outputs.
        :return: None
        """
        
        obj_attr = mde_poseblends_driver_node + '.' + 'inputModelType'
        possible_types = set(mde_poseblends_driver_ops.possible_node_types())
        
        has_model_type_attr = True
        has_model_type_attr = has_model_type_attr and cmds.objExists(mde_poseblends_driver_node)
        has_model_type_attr = has_model_type_attr and (cmds.nodeType(mde_poseblends_driver_node) in possible_types)
        has_model_type_attr = has_model_type_attr and cmds.objExists(obj_attr)
        
        # if(has_model_type_attr == False and MODEL_TYPE == 'STAR'):
        #     error_string = ""
        #     error_string += "It seems like you are trying to make "
        #     error_string += "poseblends drivers for a STAR model, but "
        #     error_string += "you are using an older version of "
        #     error_string += "mde_poseblends_driver which does not "
        #     error_string += "support STAR."
        #     logging.error(error_string)
        #     return
            
        if(has_model_type_attr):
            model_type_value = None
            if(MODEL_TYPE == 'STAR'):
                model_type_value = 1
            else:
                # SMPL:
                model_type_value = 0
            
            cmds.setAttr(
                obj_attr, 
                model_type_value
            )
        
        base_dest_obj_attr = mde_poseblends_driver_node + '.' + 'inputJoint' + '[' + str(joint_index) + ']'

        # fill source/dest attrs:
        source_dest_attr_pairs = [
            {'source':'matrix',              'dest':'inputJointMatrix'},
            {'source':'worldMatrix',         'dest':'inputJointWorldMatrix'},
            {'source':'parentMatrix',        'dest':'inputJointWorldParentMatrix'},
            {'source':'parentInverseMatrix', 'dest':'inputJointWorldParentInverseMatrix'}
        ]

        # connectAttrs:
        num_attr_pairs = len(source_dest_attr_pairs)

        for ii in range(0, num_attr_pairs):
            source_attr = source_dest_attr_pairs[ii]['source']
            dest_attr = source_dest_attr_pairs[ii]['dest']

            source_obj_attr = joint + '.' + source_attr
            dest_obj_attr =  base_dest_obj_attr + '.' + dest_attr
            cmds.connectAttr(
                source_obj_attr,
                dest_obj_attr,
                force = True
            )

    @staticmethod
    def connect_output_attrs_joint_single(
            mde_poseblends_driver_node,
            joint_index,
            blendShape_node,
            blendShape_joint_weight_start_index,
            MODEL_TYPE = 'SMPL'
    ):
        """
        mde_poseblends_driver_node.outputJoint[joint_index] -> Maya blendShape_node's weights

        Connect mde_poseblends_driver_node's joint_indexth outputJoint to drive the blendShape_node's
        weights starting at blendShape_joint_weight_start_index.

        :param mde_poseblends_driver_node:  the node whose outputs to drive blendShape_node's weights inputs.
        :param joint_index:  the index into the output attribute:   mde_poseblends_driver_node + '.' + 'outputJoint'
        :param blendShape_node:  the blendShape node whose input weights to drive with mde_poseblends_driver_node's outputs.
        :param blendShape_joint_weight_start_index:  the index of blendShape_node's weights to start connecting to.
        :return: None

        :return: None
        """
        base_source_obj_attr = mde_poseblends_driver_node + '.' + 'outputJoint' + '[' + str(joint_index) + ']'
        
        weights_per_joint = None
        
        if('SMPL' in MODEL_TYPE):
            weights_per_joint = 9
        else:
            # STAR:
            weights_per_joint = 4

        source_dest_attr_pairs = []

        # fill source/dest attrs:
        for ii in range(0, weights_per_joint):
            source_attr = 'outputJointBlendShapeWeights' + '[' + str(ii) + ']'
            blendShape_weight_attr = get_SMPL_blendShape_weight_attr_alias(
                blendShape_joint_weight_start_index,
                ii
            )
            dest_attr = blendShape_weight_attr

            current_value = {}
            current_value.update({'source':source_attr})
            current_value.update({'dest':dest_attr})
            source_dest_attr_pairs.append(current_value)

        # connectAttrs:
        num_attr_pairs = len(source_dest_attr_pairs)

        for ii in range(0, num_attr_pairs):
            source_attr = source_dest_attr_pairs[ii]['source']
            dest_attr = source_dest_attr_pairs[ii]['dest']

            source_obj_attr = base_source_obj_attr + '.' + source_attr
            dest_obj_attr = blendShape_node + '.' + dest_attr

            existing_source_obj_attr = cmds.listConnections(dest_obj_attr, p = True, source = True, destination = False)

            if(existing_source_obj_attr and len(existing_source_obj_attr) > 0):
                existing_source_obj_attr = existing_source_obj_attr[0]
                cmds.disconnectAttr(
                    existing_source_obj_attr,
                    dest_obj_attr
                )

            cmds.connectAttr(
                source_obj_attr,
                dest_obj_attr,
                force=True
            )

    @staticmethod
    def connect_input_and_output_attrs_joint_single(
            mde_poseblends_driver_node,
            joint,
            joint_index,
            blendShape_node,
            blendShape_joint_weight_start_index,
            MODEL_TYPE = 'SMPL'
    ):
        """
        Maya joint matrices -> mde_poseblends_driver_node.inputJoint[joint_index],
        mde_poseblends_driver_node.outputJoint[joint_index] -> blendShape_node's weights

        :param joint:  the name of a transform node in the Maya scene.
        :param joint_index:
            the index into the input attribute:   mde_poseblends_driver_node + '.' + 'inputJoint'
            the index into the output attribute:   mde_poseblends_driver_node + '.' + 'outputJoint'
        :param mde_poseblends_driver_node:
            the node into whose inputs to connect joint's matrix(ces) outputs.
            the node whose outputs to drive blendShape_node's weights inputs.
        :param blendShape_node:  the blendShape node whose input weights to drive with mde_poseblends_driver_node's outputs.
        :param blendShape_joint_weight_start_index:  the index of blendShape_node's weights to start connecting to.
        :return: None
        """
        # connect:
        # -joint's matrices
        # to
        # -mde_poseblends_driver_node's inputJoint[joint_index]:
        mde_poseblends_driver_ops.connect_input_attrs_joint_single(
            mde_poseblends_driver_node,
            joint,
            joint_index,
            MODEL_TYPE = MODEL_TYPE
        )

        # connect:
        # -mde_poseblends_driver_node's outputJoint[joint_index]
        # to
        # -blendShape_node's weights:
        mde_poseblends_driver_ops.connect_output_attrs_joint_single(
            mde_poseblends_driver_node,
            joint_index,
            blendShape_node,
            blendShape_joint_weight_start_index,
            MODEL_TYPE = MODEL_TYPE
        )

    @staticmethod
    def possible_node_types():
        
        mpbd_candidates = [
            # C++ version:
            'mde_poseblends_driver',
            # Python version:
            'mde_py_poseblends_driver'
        ]
        
        return mpbd_candidates

    @staticmethod
    def get_node_type_to_use():
        """
        # So:  there's two implementations of mde_poseblends_driver:
        # 1.  mde_poseblends_driver(C++)
        # 2.  mde_py_poseblends_driver(Python)
        #
        # prefer the C++ one if it is loaded, but use the Python one otherwise:
        #
        """
        mpbd_candidates = mde_poseblends_driver_ops.possible_node_types()
        
        result = None
        for candidate in mpbd_candidates:
            candidate_loaded = cmds.pluginInfo(candidate, q = True, loaded = True)
            if(candidate_loaded == False):
                continue
                
            # if the evaluation is here:  it means the candidate is loaded.
            # So:  use it:
            result = candidate
            break
            
        return result

    @staticmethod
    def create_and_connect(
        joints,
        joint_indices,
        blendShape_node,
        mode = 1,
        MODEL_TYPE = 'SMPL'
    ):
        """
        Create mde_poseblends_driver nodes to drive blendShape_node weights based on the rotations of the joints.

        :param joints:  the name of a transform nodes in the Maya scene.
        :param blendShape_node:  the blendShape node whose input weights to drive with the (one or more) mde_poseblends_driver_node's outputs.
        :param mode:
            0:  create a single mde_poseblends_driver node, and drive all the blendShape weights with it.
                This may not be the best option for performance because I think the whole mde_poseblends_driver node
                will have to re-evaluate even if only one of the input joints changes.
            1:  create a mde_poseblends_driver's node for each joint.  I think this will be the preferable
                mode, because it leaves the parallel-ization to the Maya evaluation graph, and that will make it
                where if only one joint changes, only that related mde_poseblends_driver node will be re-evaluated.
                The rest will just return whatever value is cached on their outputs.
        :return: None
        """
        mpbd_node_type = mde_poseblends_driver_ops.get_node_type_to_use()
        
        if not mpbd_node_type:
            logging.error('there is no mde_poseblends_driver plugin loaded.  Returning now without doing anything.')
            return
        
        num_joints = len(joints)

        num_nodes_to_create = 0
        mde_poseblends_driver = []
        if(mode == 0):
            num_nodes_to_create = 1
        else:
            num_nodes_to_create = num_joints

        for ii in range(0, num_nodes_to_create):
            current_node = cmds.createNode(mpbd_node_type, name = mpbd_node_type + "#")
            mde_poseblends_driver.append(current_node)

        logging.debug('mde_poseblends_driver:  ' + str(mde_poseblends_driver))

        weights_per_joint = None
        if('SMPL' in MODEL_TYPE):
            # SMPL family(SMPL, SMPLX, SMPLH):
            # use rotation part of matrix(3x3) 
            # to generate blendShape weight drivers:
            weights_per_joint = 9
        else:
            # STAR:
            # use quaternion rotation representation(x, y, z, w) 
            # to generate blendShape weight drivers:
            weights_per_joint = 4
            
        if(mode == 0):
            logging.debug(':  in if(mode == 0) block:  ')
            # connect all the joints to a single mde_poseblends_driver node:
            current_node = mde_poseblends_driver[0]
            for ii in range(0, num_joints):
                current_joint_index = joint_indices[ii]
                current_joint = joints[ii]
                current_blendShape_joint_weight_start_index = (weights_per_joint * current_joint_index)
                mde_poseblends_driver_ops.connect_input_and_output_attrs_joint_single(
                    current_node,
                    current_joint,
                    current_joint_index,
                    blendShape_node,
                    current_blendShape_joint_weight_start_index,
                    MODEL_TYPE = MODEL_TYPE
                )
        else:
            logging.debug(':  in if(mode == 1) block:  ')
            # connect all the joints to their own mde_poseblends_driver node(ie one mde_poseblends_driver node per joint):
            for ii in range(0, num_joints):
                current_joint_index = joint_indices[ii]
                current_node = mde_poseblends_driver[ii]
                current_joint = joints[ii]
                current_blendShape_joint_weight_start_index = (weights_per_joint * current_joint_index)
                mde_poseblends_driver_ops.connect_input_and_output_attrs_joint_single(
                    current_node,
                    current_joint,
                    current_joint_index,
                    blendShape_node,
                    current_blendShape_joint_weight_start_index,
                    MODEL_TYPE
                )


class ui:
    def __init__(self, winName='SMPL_model_maya_script'):
        self.winTitle = 'SMPL - Rigging & Pose Corrections Toolbox for Maya'
        self.winName = winName

        self.j_names = SMPL_generic_ops.get_base_common_joint_names()

    @staticmethod
    def get_maya_mesh_from_selection():
        ## Get selection
        selection = cmds.ls(
            selection=True,
            showType=True
        )

        ## Check if selected object is only one mesh & return if not
        if len(selection) != 2:
            print('\nError: select only the mesh')
            return
        if selection[1] != 'transform' and selection[1] != 'mesh':
            print("\nError: Please select a mesh object")
            return
        maya_mesh = selection[0] if selection[1] == 'mesh' else cmds.listRelatives(selection[0], type='mesh')[0]

        return maya_mesh

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

        ## MDE_poseblends_driver:
        cmds.rowLayout(numberOfColumns=1, columnAttach=[(1, 'both', 70)])
        create_driver_func = lambda *args: self.create_mde_poseblends_driver(mode=1)
        self.bttn_mde_poseblends_driver = cmds.button(label='Make Pose Blend Shapes fire\n interactively ',
            c=create_driver_func, width=170, height=50)
        cmds.setParent('..')
        cmds.separator(height=10, style='in')

        # ## RECOMPUTE SKELETON
        # cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 35), (2, 'both', 10)])
        # Tpose_func = lambda *args: ui.getTpose()
        # self.bttn_Tpose = cmds.button(label='Set Mesh to \n Bind-Pose', c=Tpose_func, width=120, height=50)
        # rerig_func = lambda *args: self.reRig()
        # self.bttn_rerig = cmds.button(label='Recompute \n Skeleton', c=rerig_func, width=120, height=50)
        # cmds.setParent('..')
        # cmds.separator(height=5, style='none')

        cmds.showWindow(self.winName)

#    @staticmethod
#    def getTpose():
#        """
#        Set the Mesh & pose blendshapes to 0
#        :return: None
#        """
#        maya_mesh = ui.get_maya_mesh_from_selection()
#
#        if(not maya_mesh or cmds.objExists(maya_mesh) == False):
#            print('\nError: Please select a SMPL mesh.')
#            return
#
#        is_not_skinned, lbs_cluster = maya_ops.is_not_skinned(maya_mesh)
#        if is_not_skinned:
#            print('\nError: Selected object has no Skin Cluster node (skeleton is not attached)')
#            return
#
#        has_no_blendShape, blendShape_node = maya_ops.has_no_blendShape(maya_mesh)
#        if has_no_blendShape:
#            print('\nError: Selected object has no blendShape node')
#            return
#
#        ## get all bones including root
#        bones = cmds.listConnections(lbs_cluster, type='joint')
#
#        weights_per_joint = 9
#        ## Set all joints to 0...:
#        for currentBone in enumerate(bones):
#            cmds.rotate(0.0, 0.0, 0.0, currentBone)
#
#        ## ...& pose blendShapes to 0(get T - pose)
#        for bidx, currentBone in enumerate(bones):
#            if bidx >= 23:
#                continue
#
#            # if the evaluation is here:  it means bidx < 23:
#            start_weight_index = (weights_per_joint * bidx)
#            for pidx in range(weights_per_joint):
#                blendShape_weight_attr = get_SMPL_blendShape_weight_attr_alias(
#                    start_weight_index,
#                    pidx
#                )
#                blendShape_weight_obj_attr = '%s.%s' % (blendShape_node, blendShape_weight_attr)
#                cmds.setAttr(blendShape_weight_obj_attr, 0.0)

    def create_mde_poseblends_driver(
            self,
            mode = 1
    ):
        maya_mesh = ui.get_maya_mesh_from_selection()

        if(not maya_mesh or cmds.objExists(maya_mesh) == False):
            print('\nError: Please select a SMPL or STAR mesh.')
            return

        ## Get skinning node & return if missing
        is_not_skinned, lbs_cluster = maya_ops.is_not_skinned(maya_mesh)
        if is_not_skinned:
            print('\nError: Selected object has no Skin Cluster node (skeleton is not attached)')
            return

        has_no_blendShape, blendShape_node = maya_ops.has_no_blendShape(maya_mesh)
        if has_no_blendShape:
            print('\nError: Selected object has no blendShape node')
            return

        # Backward compatibility with v1.0.3
        jointPrefix, MODEL_TYPE = self.joint_setup(
            lbs_cluster,
            blendShape_node
        )

        joints = []
        joint_indices = []
        ## Set poseblends for all joints excluding pelvis (there are no blendshapes for pelvis)
        for jidx, j_name in self.j_names.items():
            if jidx < 1:
                # don't do pelvis:
                continue

            if jidx > 21:
                # ignore joints past 21.  I guess those don't have blendshapes, either:
                continue

            # if the evaluation is here:  it means this joint has a blendShape associated with it:
            # Also:  1 <= jidx <= 21
            joint = '%s_%s' % (jointPrefix, j_name)
            joints.append(joint)
            joint_indices.append(jidx - 1)

        logging.debug(':  joints:  ' + str(joints))

        logging.debug('):  mode(before create_and_connect() call):  ' + str(mode))
        mde_poseblends_driver_ops.create_and_connect(
            joints,
            joint_indices,
            blendShape_node,
            mode = mode,
            MODEL_TYPE = MODEL_TYPE
        )


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

        maya_mesh = ui.get_maya_mesh_from_selection()

        if(not maya_mesh or cmds.objExists(maya_mesh) == False):
            print('\nError: Please select a SMPL mesh.')
            return

        is_not_skinned, lbs_cluster = maya_ops.is_not_skinned(maya_mesh)
        if is_not_skinned:
            print('\nError: Selected object has no skinCluster node (skeleton is not attached)')
            return

        has_no_blendShape, blendShape_node = maya_ops.has_no_blendShape(maya_mesh)
        if has_no_blendShape:
            print('\nError: Selected object has no blendShape node')
            return

        # TODO:  charID immediately below seems unused:  remove?
        # charID = cmds.listRelatives(maya_mesh, parent=True)[0]

        # Backward compatibility with v1.0.3
        bonePrefix, MODEL_TYPE = self.joint_setup(
            lbs_cluster,
            blendShape_node
        )

        if use_timeline:
            f1 = int(cmds.intFieldGrp(self.framesField, query=True, value1=True))
            f2 = int(cmds.intFieldGrp(self.framesField, query=True, value2=True))
            frame_range = [f1, f2 + 1]
            cmds.playbackOptions(min=frame_range[0], max=frame_range[-1], maxPlaybackSpeed=0)
        else:
            currentTime = int(cmds.currentTime(query=True))
            frame_range = [currentTime, currentTime + 1]
        print('frame_range: ', frame_range)

        weights_per_joint = 9
        ## get all bones attached to skin (that excludes root)
        # TODO:  maya_jnt_tree immediately below is unused:  remove?:
        # maya_jnt_tree = cmds.skinCluster(lbs_cluster, query=True, wi=True)
        for frame in range(frame_range[0], frame_range[-1]):
            cmds.currentTime(frame)

            ## Set poseblends for all joints excluding pelvis (there are no blendshapes for pelvis)
            for jidx, j_name in self.j_names.items():
                if jidx > 0 and (frame_range[-1] - frame_range[0]) > 0:
                    bone = '%s_%s' % (bonePrefix, j_name)
                    logging.debug("ui::applyBlendshapes():  bone:  " + str(bone))
                    start_weight_index = (weights_per_joint * (jidx - 1))

                    ## Get original 4x4 maya rotation matrix from bone
                    #cmds.select(bone, replace=True)
                    #real_m = np.array(cmds.xform(query=True, matrix=True)).reshape((4, 4)).T
                    bone_m = cmds.xform(bone, query=True, matrix=True)
                    logging.debug("ui::applyBlendshapes():  bone_m:  " + str(bone_m))
                    real_m = maya_ops.from_1x16_list_to_4x4_MMatrix(
                        bone_m,
                        transpose = True
                    )
                    
                    real_m = real_m - oM.MMatrix.identity
                    # in the real_m_1D assignment immediately below:
                    # range(0, 3) instead of range(0, 4) in order to drop the translation values:
                    real_m_1D = [real_m(ii, jj) for ii in range(0, 3) for jj in range(0, 3)]
                    for mi, rot_element in enumerate(real_m_1D):
                        blendShape_weight_attr = get_SMPL_blendShape_weight_attr_alias(
                            start_weight_index,
                            mi
                        )
                        blendShape_weight_obj_attr = '%s.%s' % (blendShape_node, blendShape_weight_attr)
                        logging.debug("ui::applyBlendshapes():  blendShape_weight_obj_attr:  " + str(blendShape_weight_obj_attr))

                        blendShape_weight_value = rot_element * scale_up
                        cmds.setAttr(
                            blendShape_weight_obj_attr,
                            blendShape_weight_value
                        )
                        # cmds.blendShape(blendShape_node, edit=True, w=[(bidx, rot_element * scale_up)])
                        if rekey:
                            cmds.setKeyframe(
                                blendShape_weight_obj_attr,
                                breakdown=False,
                                controlPoints=False,
                                shape=False
                            )
                # Ignoring extraneous blendshapes for FBX
                if jidx == 21:
                    break

            ## clear selection
            # cmds.select( clear=True )
            cmds.select(maya_mesh, replace=True)

#    def reRig(self):
#        """
#        Create a skeleton using the selected mesh and joint regressor
#        Requires 'joints_mat_<MODEL_TYPE>.npz' file.
#        Please make sure the 'joints_mat_<MODEL_TYPE>.npz' file is in the same location as this plugin file.
#        :return: None
#        """
#
#        maya_mesh = ui.get_maya_mesh_from_selection()
#
#        if(not maya_mesh or cmds.objExists(maya_mesh) == False):
#            print('\nError: Please select a SMPL mesh.')
#            return
#
#        ## Get skinning node & return if missing
#        is_not_skinned, lbs_cluster = maya_ops.is_not_skinned(maya_mesh)
#        if is_not_skinned:
#            print('\nError: Selected object has no Skin Cluster node (skeleton is not attached)')
#            return
#
#        has_no_blendShape, blendShape_node = maya_ops.has_no_blendShape(maya_mesh)
#        if has_no_blendShape:
#            print('\nError: Selected object has no blendShape node')
#            return
#
#
#        ## Get model-specific parameters: name, joint-names, blendshapes node
#        # TODO:  seems:
#        #  charID
#        #  blendShape_node
#        #  immediately below are unused:  remove???
#        # charID = cmds.listRelatives(maya_mesh, parent=True)[0]
#        # blendShape_node = self.get_associated_blendShape(maya_mesh, objset=objset)
#
#        ## Get directory from where plugin is loaded
#        plugin_dir = split(cmds.pluginInfo(SCRIPT_NAME, q=True, path=True))[0]
#
#        # Find model_type and update bone setup
#        bonePrefix, MODEL_TYPE = self.joint_setup(
#            lbs_cluster,
#            blendShape_node
#        )
#
#        ## Find joints_mat_v*.npz file & return if missing
#        joints_mat_path = '%s/joints_mat_%s.npz' % (plugin_dir, MODEL_TYPE)
#        if not exists(joints_mat_path):
#            current_err_str = '\nError: Missing \')joints_mat_%s.npz\' file.' % MODEL_TYPE
#            print(current_err_str)
#            current_err_str = ''
#            current_err_str += 'Please make sure the \')joints_mat_%s.npz\' file ' % MODEL_TYPE
#            current_err_str += 'is in the same location as the SMPL_maya_plugin.py file.'
#            print(current_err_str)
#            return
#
#        ## Get new joint hierarchy
#        joints_mat = np.load(joints_mat_path)
#
#        ## Get mesh vertices
#        mesh_verts = maya_ops.getVtxPos(maya_mesh)
#        gender = 'male' if maya_mesh[0] == 'm' else 'female'
#
#        ## Get new joints
#        num_verts_to_use = len(joints_mat[gender][1])
#        mesh_verts_to_dot = np.asarray(mesh_verts[:num_verts_to_use])
#        subject_j = joints_mat[gender].dot(mesh_verts_to_dot)
#
#        ## Lock skinning and set new joint locations
#        cmds.skinCluster(maya_mesh, edit=True, moveJointsMode=True)
#        for j_idx, j_name in self.j_names.items():
#            currentBone = '%s_%s' % (bonePrefix, j_name)
#            cmds.move(subject_j[j_idx][0], subject_j[j_idx][1], subject_j[j_idx][2], currentBone)
#        cmds.skinCluster(maya_mesh, edit=True, moveJointsMode=False)

    def joint_setup(
        self,
        lbs_cluster,
        blendShape_node
    ):
        joints = cmds.listConnections(
            lbs_cluster,
            type='joint'
        )
        unique_joints = set(joints)
        joints = unique_joints

        obj_attr = blendShape_node + '.' + 'weight'
        num_blendShape_node_targets = cmds.getAttr(
            obj_attr, 
            size = True
        )
        
        result = SMPL_generic_ops.get_joint_info(
            joints,
            num_blendShape_node_targets
        )
        
        self.j_names = result['joint_names']
        joint_prefix = result['root_joint_prefix']
        MODEL_TYPE = result['MODEL_TYPE']
        
        return joint_prefix, MODEL_TYPE


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
