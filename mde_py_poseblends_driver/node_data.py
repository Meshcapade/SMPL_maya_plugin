import enum
import logging

import maya.OpenMaya as oM

import lib_mde_poseblends_driver as mlpbd
import mde_utilities as utils

# node_data:
# This is intended to encapsulate the compute() part of 
# mde_py_poseblends_driver Python MPxNode to keep it separated from
# all the input and output boilerplate code in the 
# mde_py_poseblends_driver.py source files.
# This is also where the mde_poseblends_driver node accesses 
# the non-maya-centric version of the solution to this problem:
# lib_mde_poseblends_driver.py
# Hopefully in the future:  lib_mde_poseblends_driver.py can be 
# replaced by a PyBind wrapper around 
# the existing C++ lib_mde_poseblends_driver.h
class from_Maya_to_Non_Maya(object):
    NON_MAYA_DATA_T = mlpbd.poseblends_driver_data
    NON_MAYA_JOINT_DATA_T = NON_MAYA_DATA_T.JOINT_IO_DATA_T
    XFORM_MATRIX_T = NON_MAYA_JOINT_DATA_T.XFORM_MATRIX_T 
    
    # Convert from Maya MMatrix to whatever is being used for Non-Maya representation
    # (currently:  the Non-Maya representation is also MMatrix, so the conversion is just assignment):
    # \param[in] source:  the Maya MMatrix(4x4 homogeneous transform matrix) to convert.
    # \param[out] dest:  the Maya MMatrix(4x4 homogeneous transform matrix) to convert.
    # \return an int:  0:  fail, 1:  success
    
    @staticmethod
    def do_it(
        source,
        dest
    ):
        stat = 1
        
        # assume dest is a list so the result can be passed back by reference:
        utils.resize(dest, 1)
        
        # they're(ie both Maya and Non-Maya) currently both MMatrix, so just use assignment:
        dest[0] = source
        
        return stat
        

class maya_per_joint_data(object):
    NON_MAYA_DATA_T = mlpbd.poseblends_driver_data
    JOINT_IO_DATA_T = NON_MAYA_DATA_T.JOINT_IO_DATA_T 
    JOINT_MATRIX_MODE_T = JOINT_IO_DATA_T.JOINT_MATRIX_MODE_T
    #XFORM_MATRIX_T = oM.MFloatMatrix
    XFORM_MATRIX_T = oM.MMatrix
    
    def __init__(self):
        THIS_T = maya_per_joint_data
        
        self.envelope = 1.0
        self.matrix_mode = THIS_T.JOINT_MATRIX_MODE_T.LOCAL
        
        MATRIX_T = THIS_T.XFORM_MATRIX_T
        self.matrix = MATRIX_T()
        self.world_matrix = MATRIX_T()
        self.world_parent_matrix = MATRIX_T()
        self.world_parent_inverse_matrix = MATRIX_T()
        
        self.matrix.setToIdentity()
        self.world_matrix.setToIdentity()
        self.world_parent_matrix.setToIdentity()
        self.world_parent_inverse_matrix.setToIdentity()


class convert_per_joint_from_maya_to_non_maya(object):
    # convert_per_joint_from_maya_to_non_maya:  what does this mean?
    # This class contains procedure that have to do with operations
    # that involve Maya-centric and non-Maya-centric versions
    # of per-joint storage.  For example:  converting from one 
    # format to the other.
    NODE_T = mlpbd.poseblends_driver
    JOINT_IO_DATA_T = NODE_T.JOINT_IO_DATA_T
    NON_MAYA_JOINT_DATA_T = JOINT_IO_DATA_T 
    # ^ NON_MAYA_JOINT_DATA_T because it is (potentially) non-Maya-centric
    
    MAYA_JOINT_DATA_T = maya_per_joint_data
    # ^ MAYA_JOINT_DATA because it is Maya-centric
    
    DATA_T = MAYA_JOINT_DATA_T 
    # ^ DATA_T because it is the data associated with this operations class.
    
    JOINT_MATRIX_MODE_T = MAYA_JOINT_DATA_T.JOINT_MATRIX_MODE_T 
    
    # Depending on the value of source.matrix_mode:
    # convert only the matrices of source that need to be converted
    # to fill the appropriate, matching matrices of dest.
    # \param[in] source:  MAYA_JOINT_DATA_T, the Maya MMatrix-storing version as read in from the mde_poseblends_driver node's input attributes.
    # \param[out] dest:  NON_MAYA_JOINT_DATA_T:  the non-Maya-centric JOINT_IO_DATA_T defined in mlpbd.
    # \return an int:  0:  fail, 1:  success
    
    @staticmethod
    def __call__(
        source,
        dest
    ):
        logging.debug('convert_per_joint_from_maya_to_non_maya.__call__():  source:  {0}'.format(source))
        logging.debug('convert_per_joint_from_maya_to_non_maya.__call__():  dest:  {0}'.format(dest))
        stat = 1
        
        source_members_exhaustive = dir(source)
        dest_members_exhaustive = dir(dest)
        source_members = [attr for attr in source_members_exhaustive if not callable(getattr(source, attr)) and not attr.startswith("__")]
        dest_members = [attr for attr in dest_members_exhaustive if not callable(getattr(dest, attr)) and not attr.startswith("__")]
        
        logging.debug('convert_per_joint_from_maya_to_non_maya.__call__():  source_members_exhaustive:  {0}'.format(source_members_exhaustive))
        logging.debug('convert_per_joint_from_maya_to_non_maya.__call__():  dest_members_exhaustive:  {0}'.format(dest_members_exhaustive))
        logging.debug('convert_per_joint_from_maya_to_non_maya.__call__():  source_members:  {0}'.format(source_members))
        logging.debug('convert_per_joint_from_maya_to_non_maya.__call__():  dest_members:  {0}'.format(dest_members))
        
        # envelope:
        dest.envelope = source.envelope
        
        # matrix_mode:
        matrix_mode_value = source.matrix_mode
        dest.matrix_mode = matrix_mode_value
        
        m2nm_convert = lambda x, y:  from_Maya_to_Non_Maya.do_it(x, y)
        
        MATRIX_MODE_T = convert_per_joint_from_maya_to_non_maya.JOINT_MATRIX_MODE_T
        # only convert the data that will be used in the actual calculation
        # based on the matrix_mode_value:
        conversion_result = [None]
        if(matrix_mode_value == MATRIX_MODE_T.LOCAL):
            # only convert the LOCAL-space:
            # source.matrix -> dest.matrix
            # because we assume by the choice of matrix_mode_value
            # that the user has set this to exactly what they want.
            m2nm_convert(
                source.matrix,
                conversion_result
            )
            dest.matrix = conversion_result[0]
        elif (matrix_mode_value == MATRIX_MODE_T.WORLD):
            # This will create a LOCAL matrix internally by
            # taking the inverse of world_parent_matrix and multiplying
            # with world_matrix.
            # So:  those are the two matrices to convert.
            m2nm_convert(
                source.world_matrix,
                conversion_result
            )
            dest.world_matrix = conversion_result[0]
            
            m2nm_convert(
                source.world_parent_matrix, 
                conversion_result
            )
            dest.world_parent_matrix = conversion_result[0]
            
        else: # (matrix_mode_value == MATRIX_MODE_T.WORLDwInv)
            # This will create a LOCAL matrix internally by
            # multiplying world_parent_inverse_matrix
            # with world_matrix.
            # So:  those are the two matrices to convert.
            m2nm_convert(
                source.world_matrix, 
                conversion_result
            )
            dest.world_matrix = conversion_result[0]
            
            m2nm_convert(
                source.world_parent_inverse_matrix, 
                conversion_result
            )
            dest.world_parent_inverse_matrix = conversion_result[0]
        
        return stat

class node_data(object):
    NON_MAYA_DATA_T = mlpbd.poseblends_driver_data 
    JOINT_IO_DATA_T = NON_MAYA_DATA_T.JOINT_IO_DATA_T 
    JOINT_MATRIX_MODE_T = JOINT_IO_DATA_T.JOINT_MATRIX_MODE_T 
    NON_MAYA_OPS_T = mlpbd.poseblends_driver 
    MAYA_PER_JOINT_DATA_T = maya_per_joint_data 
    CONVERTOR_T = convert_per_joint_from_maya_to_non_maya 
    MODEL_T = NON_MAYA_DATA_T.MODEL_T 
    
    def __init__(
        self, 
    ):
        # INPUTS:
        self.envelope = 1.0
        self.model_type = node_data.MODEL_T.kSMPL
        
        # read-in info from input attributes:
        self.maya_joint_data = list()
        self.joint_logical_indices = list()
        
        # WIP Data:  This data should be completely independent of 
        # Maya-centric types:
        self.non_maya_data = node_data.NON_MAYA_DATA_T()
    
    def resize_inputs(
        self,
        num_joints
    ):
        stat = 1
        
        utils.resize(self.maya_joint_data, num_joints)
        utils.resize(self.joint_logical_indices, num_joints)
        
        return stat
    
    def set_per_joint_data_from_Maya_to_non_Maya(
        self,
        joint_index
    ):
        # this->maya_joint_data is filled from mde_poseblends_driver's input attributes.
        # maya_joint_data contains Maya centric storage(ie MMatrix, for example).
        # 
        # This method fills this->non_maya_data from the values 
        # stored in this->maya_joint_data.
        # 
        # This method is the version that just operates on a particular
        # joint, the one at joint_index.
        stat = 1
        
        logging.debug('len(self.maya_joint_data):  {0}'.format(len(self.maya_joint_data)))
        logging.debug('len(self.non_maya_data.joints_data):  {0}'.format(len(self.non_maya_data.joints_data)))
        logging.debug('self.maya_joint_data:  {0}'.format(self.maya_joint_data))
        logging.debug('self.non_maya_data.joints_data:  {0}'.format(self.non_maya_data.joints_data))
        maya_source = self.maya_joint_data[joint_index]
        
        if(self.non_maya_data.joints_data[joint_index] is None):
            self.non_maya_data.joints_data[joint_index] = node_data.JOINT_IO_DATA_T()
        
        non_maya_dest = self.non_maya_data.joints_data[joint_index]
        
        logging.debug('maya_source:  {0}'.format(maya_source))
        logging.debug('non_maya_dest:  {0}'.format(non_maya_dest))
        
        convert = node_data.CONVERTOR_T()
        convert(
            maya_source, 
            non_maya_dest
        )
        
        return stat
    
    
    def set_data_from_maya_to_non_maya(
        self
    ):
        # this->maya_joint_data is filled from mde_poseblends_driver's input attributes.
        # maya_joint_data contains Maya centric storage(ie MMatrix, for example).
        # 
        # This method fills this->non_maya_data from the values 
        # stored in this->maya_joint_data:
        stat = 1
        
        self.non_maya_data.envelope = self.envelope
        self.non_maya_data.model_type = self.model_type
        
        num_joints = len(self.maya_joint_data)
        logging.debug('num_joints:  {0}'.format(num_joints))
        
        self.non_maya_data.init_joints_data(
            num_joints
        )
        
        for ii in range(0, num_joints):
            self.set_per_joint_data_from_Maya_to_non_Maya(
                ii
            )
        
        return stat
    
    
    def calculate(
        self
    ):
        
        stat = 0
        
        # put the data:
        # -from:  maya_joint_data(Maya-centric, MMatrix) 
        # -> 
        # -to:  non_maya_data(Maya-independent, also MMatrix):
        self.set_data_from_maya_to_non_maya()
        
        # calculate the blendShape weights for all the input joints:
        non_maya_ops = node_data.NON_MAYA_OPS_T
        
        non_maya_ops.calculate(
            self.non_maya_data
        )
        
        return stat
        
