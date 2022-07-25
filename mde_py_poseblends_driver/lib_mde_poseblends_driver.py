import enum
import logging
import math
import maya.OpenMaya as oM

import mde_utilities as utils

@enum.unique
class joint_matrix_mode_t(enum.IntEnum):
    LOCAL = 0
    WORLD = 1
    WORLDwInv = 2

def set_cell_float(
    matrix, 
    value, 
    row, 
    column
):
    # for setting the [row][column] element of MMatrix
    # https:#groups.google.com/g/python_inside_maya/c/Gou02IHsYKA
    #oM.MScriptUtil.setDoubleArray( 
    oM.MScriptUtil.setFloatArray( 
        matrix[row], 
        column, 
        value 
    )

def set_all_cells_float(
    matrix, 
    value = 0.0
):
    # set all matrix cells to a single value:
    for ii in range(0, 4):
        for jj in range(0, 4):
            set_cell_float(matrix, value, ii, jj)
            
def set_cell(
    matrix, 
    value, 
    row, 
    column
):
    # for setting the [row][column] element of MMatrix
    # https:#groups.google.com/g/python_inside_maya/c/Gou02IHsYKA
    #oM.MScriptUtil.setDoubleArray( 
    oM.MScriptUtil.setDoubleArray( 
        matrix[row], 
        column, 
        value 
    )

def set_all_cells(
    matrix, 
    value = 0.0
):
    # set all matrix cells to a single value:
    for ii in range(0, 4):
        for jj in range(0, 4):
            set_cell(matrix, value, ii, jj)

def get_row(
    matrix,
    row_index
):
    result = [matrix(row_index, ii) for ii in range(0, 4)]
    return result

def from_matrix_to_quaternion(mat):
    # I'm having trouble getting the MMatrix -> MQuaternion
    # conversion to produce the same result as what's in the C++
    # version of the plugin(which uses MMatrix -> Eigen Matrix -> Eigen Quaternion).
    # Although this Python version of the plugin seems to work cursorily, 
    # it does not have the same range as the C++ version for similar
    # STAR joints being tested to compare C++ and Python versions.
    # So:  I lifted this conversion from Eigen's Quaternion header
    # to hopefully work better than the Maya version.
    #
    # This algorithm comes from  "Quaternion Calculus and Fast Animation",
    # Ken Shoemake, 1987 SIGGRAPH course notes
    QUAT_T = joint_io.QUAT_T
    
    #Scalar t = mat.trace();
    t = float(sum([mat(ii, ii) for ii in range(0, 3)]))
    
    q_list = [None for x in range(0, 4)]
    if (t > 0):
        t = math.sqrt(t + 1.0)
        q_list[3] = 0.5 * t
        t = 0.5 / t
        q_list[0] = (mat(2, 1) - mat(1, 2)) * t
        q_list[1] = (mat(0, 2) - mat(2, 0)) * t
        q_list[2] = (mat(1, 0) - mat(0, 1)) * t
        
    else:
        ii = 0
        if (mat(1, 1) > mat(0, 0)):
            ii = 1
        if (mat(2, 2) > mat(ii, ii)):
            ii = 2
        jj = (ii + 1) % 3
        kk = (jj + 1) % 3
        
        
        t = math.sqrt(mat(ii, ii) - mat(jj, jj) - mat(kk, kk) + 1.0)
        q_list[ii] = 0.5 * t
        t = 0.5 / t
        q_list[3] = (mat(kk, jj) - mat(jj, kk)) * t
        q_list[jj] = (mat(jj, ii) + mat(ii, jj)) * t
        q_list[kk] = (mat(kk, ii) + mat(ii, kk)) * t
        
    q = QUAT_T(
        q_list[0], 
        q_list[1], 
        q_list[2], 
        q_list[3]
    )
    
    
    """
    q_list = None
    if mat(2, 2) < 0:
        if mat(0, 0) > mat(1, 1):
            t = 1.0 + mat(0, 0) - mat(1, 1) - mat(2, 2)
            q_list = [t, mat(0, 1)+mat(1, 0), mat(2, 0)+mat(0, 2), mat(1, 2)-mat(2, 1)]
        else:
            t = 1.0 - mat(0, 0) + mat(1, 1) - mat(2, 2)
            q_list = [mat(0, 1)+mat(1, 0), t, mat(1, 2)+mat(2, 1), mat(2, 0)-mat(0, 2)]
    else:
        if (mat(0, 0) < -mat(1, 1)):
            t = 1.0 - mat(0, 0) - mat(1, 1) + mat(2, 2)
            q_list = [mat(2, 0)+mat(0, 2), mat(1, 2)+mat(2, 1), t, mat(0, 1)-mat(1, 0)]
        else:
            t = 1.0 + mat(0, 0) + mat(1, 1) + mat(2, 2)
            q_list = [mat(1, 2)-mat(2, 1), mat(2, 0)-mat(0, 2), mat(0, 1)-mat(1, 0), t]
    
    q = QUAT_T(
        q_list[0], 
        q_list[1], 
        q_list[2], 
        q_list[3]
    )
    q.scaleIt(0.5 / math.sqrt(t))
    """
    
    return q


class joint_io_data(object):
    #XFORM_MATRIX_T = oM.MFloatMatrix
    XFORM_MATRIX_T = oM.MMatrix
    JOINT_MATRIX_MODE_T = joint_matrix_mode_t
    
    def __init__(
        self, 
        matrix_mode = joint_matrix_mode_t.LOCAL
    ):
        THIS_T = joint_io_data
        
        # INPUTS:
        self.scale = 1.0
        self.envelope = 1.0
        self.tol = 1.0e-5
        self.matrix_mode = matrix_mode
        
        MATRIX_T = THIS_T.XFORM_MATRIX_T
        self.matrix = MATRIX_T()
        self.world_matrix = MATRIX_T()
        self.world_parent_matrix = MATRIX_T()
        self.world_parent_inverse_matrix = MATRIX_T()
        
        self.matrix.setToIdentity()
        self.world_matrix.setToIdentity()
        self.world_parent_matrix.setToIdentity()
        self.world_parent_inverse_matrix.setToIdentity()
        
        
        
        # OUTPUTS:
        self.blendshape_weights = list()
        
    def resize_weights(self, new_size):
        utils.resize(
            self.blendshape_weights, 
            new_size
        )
        
    def set_local_matrix_based_on_matrix_mode(
        self
    ):
        stat = 1
        
        THIS_T = joint_io_data
        MATRIX_MODE_T = THIS_T.JOINT_MATRIX_MODE_T
        
        if(self.matrix_mode == MATRIX_MODE_T.LOCAL):
            # no op:  we assume the user has set LOCAL to the value
            # they want.
            pass
        else:
            # we are going to calculate local matrix based on world
            # matrix inputs:
            if(self.matrix_mode == MATRIX_MODE_T.WORLD):
                self.world_parent_inverse_matrix = self.world_parent_matrix.inverse()
            
            # if the evaluation is here, it means:
            # *self.matrix_mode == WORLD, and we've just calculated the
            #         value of self.world_parent_inverse_matrix immediately above, or:
            # *self.matrix_mode == WORLDwInv, which means we will assume
            #         self.world_parent_inverse_matrix was set by the user to an
            #         appropriate value before calling this procedure.
            # Either way:  we need to calculate the local matrix given the
            # world matrix and it's parent's inverse matrix in world space:
            self.matrix = self.world_matrix * self.world_parent_inverse_matrix
            
        return stat
    
    def scale_envelope(
        self,
        scale
    ):
        self.envelope *= scale
        

class joint_io(object):
    DATA_T = joint_io_data
    
    # XFORM_MATRIX_T:  
    # the following is using MMatrix for the bs_weights_source
    # matrix.  MMatrix is 4x4, while bs_weights_matrix only needs 3x3.
    # Maybe this can be corrected in future; however, the current 
    # criteria is not to use Numpy or any Python which would require
    # end user action to obtain/setup to work with Maya.
    XFORM_MATRIX_T = DATA_T.XFORM_MATRIX_T
    QUAT_T = oM.MQuaternion
    
    @staticmethod
    def get_bs_weights_source (
        arg_data,
        result,
        do_transpose = True,
        subtract_identity = True,
    ):
        stat = 1
        
        # this to indicate that we're clearing result for use as
        # a return by value for the bs_weights_source
        utils.resize(result, 1)
        
        MATRIX_T = joint_io.XFORM_MATRIX_T
        bs_weights_source = MATRIX_T() 
        
        scale = arg_data.scale
        envelope = arg_data.envelope
        
        combined_scale = scale * envelope
        
        if(abs(combined_scale) < arg_data.tol):
            # set all the values in bs_weights_source to 0.0:
            #set_all_cells_float(
            #    bs_weights_source,
            #    0.0
            #)
            set_all_cells(
                bs_weights_source,
                0.0
            )
        else:
            # assuming matrix_mode and all the *matrix* members have been
            # set as desired by the user:  matrix will be a useful
            # local-space matrix after 
            # set_local_matrix_based_on_matrix_mode() is called below:
            arg_data.set_local_matrix_based_on_matrix_mode()
            
            local_matrix = arg_data.matrix
            
            # the source of the blendshape weights is the 3x3 block 
            # of the 4x4 local homogeneous transformation(which represents
            # the rotation values) - the identity matrix:
            bs_weights_source = local_matrix
            if do_transpose:
                bs_weights_source = bs_weights_source.transpose()
            
            if(subtract_identity):
                identity = MATRIX_T()
                identity.setToIdentity()
                bs_weights_source = bs_weights_source - identity
        
        logging.debug('joint_io.get_bs_weights_source():  bs_weights_source(at the end):  {0}'.format(bs_weights_source))
        result[0] = bs_weights_source
        
        return stat
    
    @staticmethod
    def calculate_SMPL (
        arg_data
    ):
        stat = 1
        
        # In this Python version:  it would seem like:
        # since both the Maya and non-Maya matrices are represented by
        # MMatrix:  transpose is not necessary.  If the calculation was
        # being done using Eigen or Numpy or some other library:  
        # might be necessary.
        # So:  it turns out the do_transpose _DOES_ need to be on for
        # calculate SMPL, but not for STAR for the Python version of
        # mde_py_poseblends_driver because MMatrix(MFloatMatrix) is used
        # for both reading from the node attributes AND doing the calculations.
        # In the mde_poseblends_driver node(C++):  do_transpose is on for
        # both SMPL and STAR:  ???
        do_transpose = True
        subtract_identity = True
        gbws_result = []
        stat = joint_io.get_bs_weights_source(
            arg_data,
            gbws_result,
            do_transpose,
            subtract_identity
        )
        
        if(stat != 1):
            return stat
            
        bs_weights_source = gbws_result[0]
        logging.debug('joint_io.calculate_SMPL():  bs_weights_source:  {0}'.format([bs_weights_source(ii, jj) for ii in range(0, 4) for jj in range(0, 4)]))
        scale = arg_data.scale
        envelope = arg_data.envelope
        
        combined_scale = scale * envelope
        
        logging.debug('joint_io.calculate_SMPL():  combined_scale:  {0}'.format(combined_scale))
        num_bs_weights_rows = 3
        num_bs_weights_cols = 3
        num_bs_weights = num_bs_weights_rows * num_bs_weights_cols # should be 9
        
        arg_data.resize_weights(
            num_bs_weights
        )
        result = arg_data.blendshape_weights
        
        bs_weights_index = 0
        for ii in range(0, num_bs_weights_rows):
            current_source_row = get_row(
                bs_weights_source,
                ii
            )
            
            logging.debug('joint_io.calculate_SMPL():  current_source_row:  {0}'.format(current_source_row))
            for jj in range(0, num_bs_weights_cols):
                result[bs_weights_index] = combined_scale * current_source_row[jj]
                logging.debug('joint_io.calculate_SMPL():  result[bs_weights_index({0})]:  {1}'.format(bs_weights_index, result[bs_weights_index]))
                bs_weights_index += 1
        
        return stat
    
    @staticmethod
    def calculate_STAR (
        arg_data
    ):
        
        stat = 1
        QUAT_T = joint_io.QUAT_T
        
        # since both the Maya and non-Maya matrices are represented by
        # MMatrix:  transpose is not necessary.  If the calculation was
        # being done using Eigen or Numpy or some other library:  
        # might be necessary.
        do_transpose = True
        subtract_identity = False
        gbws_result = []
        stat = joint_io.get_bs_weights_source(
            arg_data,
            gbws_result,
            do_transpose,
            subtract_identity
        )
        
        if(stat != 1):
            return stat
            
        bs_weights_source = gbws_result[0]
        
        scale = arg_data.scale
        envelope = arg_data.envelope
        
        combined_scale = scale * envelope
        
        # set quaternion from matrix:
        # ^convert matrix bs_weights_source to quaternion bs_quat.
        bs_quat = from_matrix_to_quaternion(bs_weights_source)
        
        bs_quat.normalizeIt()
        
        if bs_quat.w < 0.0:
            # make sure w is always positive:
            # (Slim advises:  for unit quaternions:  -q and q are the same rotation):
            bs_quat = -1.0 * bs_quat
        
        logging.debug('joint_io.calculate_STAR():  bs_weights_source:  {0}'.format([bs_weights_source(ii, jj) for ii in range(0, 4) for jj in range(0, 4)]))
        logging.debug('joint_io.calculate_STAR():  bs_quat:  {0}'.format([bs_quat[ii] for ii in range(0, 4)]))
        
        num_bs_weights = 4 # same as number of quaternion elements(ie x, y, z, w)
        
        arg_data.resize_weights(
            num_bs_weights
        )
        result = arg_data.blendshape_weights
        
        result[0] = combined_scale * bs_quat.x
        result[1] = combined_scale * bs_quat.y
        result[2] = combined_scale * bs_quat.z
        result[3] = combined_scale * (bs_quat.w - 1.0)
        
        return stat
        
        
class poseblends_driver_data(object):
    JOINT_IO_DATA_T = joint_io_data
    
    @enum.unique
    class MODEL_T(enum.IntEnum):
        kSMPL = 0
        kSTAR = 1

    def __init__(
        self
    ):
        THIS_T = poseblends_driver_data
        
        self.scale = 1.0
        self.envelope = 1.0
        self.tol = 1.0e-5
        self.model_type = THIS_T.MODEL_T.kSMPL
        self.joints_data = list()
        
    def init_joints_data(
        self,
        num_joints
    ):
        stat = 1
        
        utils.resize(
            self.joints_data, 
            num_joints
        )
        
        return stat
    
    def is_SMPL(
        self
    ):
        THIS_T = poseblends_driver_data
        
        logging.debug('poseblends_driver_data.is_SMPL:  self.model_type:  {0}'.format(self.model_type))
        logging.debug('poseblends_driver_data.is_SMPL:   THIS_T.MODEL_T.kSMPL:  {0}'.format( THIS_T.MODEL_T.kSMPL))
        result = (self.model_type == THIS_T.MODEL_T.kSMPL)
        
        return result
    
    def is_STAR(
        self
    ):
        THIS_T = poseblends_driver_data
        
        logging.debug('poseblends_driver_data.is_SMPL:  self.model_type:  {0}'.format(self.model_type))
        logging.debug('poseblends_driver_data.is_SMPL:   THIS_T.MODEL_T.kSTAR:  {0}'.format( THIS_T.MODEL_T.kSTAR))
        result = (self.model_type == THIS_T.MODEL_T.kSTAR)
        
        return result
        
        
class poseblends_driver(object):
    DATA_T = poseblends_driver_data
    JOINT_IO_OPS_T = joint_io
    JOINT_IO_DATA_T = DATA_T.JOINT_IO_DATA_T
    
    @staticmethod
    def calculate_single(
        arg_data,
        joint_index
    ):
        stat = 1
        
        THIS_T = poseblends_driver
        ops = poseblends_driver.JOINT_IO_OPS_T 
        
        current_joint_data = arg_data.joints_data[joint_index]
        
        logging.debug('poseblends_driver.calculate_single:  arg_data.is_SMPL():  {0}'.format(arg_data.is_SMPL()))
        logging.debug('poseblends_driver.calculate_single:  arg_data.is_STAR():  {0}'.format(arg_data.is_STAR()))
        if(arg_data.is_SMPL()):
            # use SMPL:
            ops.calculate_SMPL(
                current_joint_data
            )
        else:
            # use STAR:
            ops.calculate_STAR(
                current_joint_data
            )
        
        return stat
    
    @staticmethod
    def calculate(
        arg_data
    ):
        stat = 1
        
        joints_data = arg_data.joints_data
        num_joints = len(joints_data)
        scale = arg_data.scale
        envelope = arg_data.envelope
        
        # attenuate the per-joint envelopes by the:
        # *global envelope and 
        # *global scale:
        combined_scale = scale * envelope
        for ii in range(0, num_joints):
            current_joint_data = arg_data.joints_data[ii]
            current_joint_data.scale_envelope(combined_scale)
            
        # serial:
        for ii in range(0, num_joints):
            current_stat = poseblends_driver.calculate_single(
                arg_data,
                ii
            )
        
        return stat
        
