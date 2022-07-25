import maya.OpenMaya as oM
import maya.OpenMayaMPx as oMPx
import mde_py_maya_type_ids as mp_mtid
import node_data as nd
import read_multi_attribute as rma
import logging

import lib_mde_poseblends_driver as mlpbd

MAYA_TYPE_ID_T = mp_mtid.maya_type_id

class per_joint_data_extract(object):
    
    NODE_DATA_T = nd.node_data 
    MAYA_PER_JOINT_DATA_T = NODE_DATA_T.MAYA_PER_JOINT_DATA_T 
    JOINT_MATRIX_MODE_T = NODE_DATA_T.JOINT_MATRIX_MODE_T 
    
    def __init__(
        self
    ):
        self.tol = 1.0e-5
        
        self.input_joint_envelope_MObject = None
        self.input_joint_matrix_mode_MObject = None
        self.input_joint_matrix_MObject = None
        self.input_joint_world_matrix_MObject = None
        self.input_joint_world_parent_matrix_MObject = None
        self.input_joint_world_parent_inverse_matrix_MObject = None
    
    
    def __call__(
        self,
        per_joint_data_array,
        per_joint_data_index,
        data_handle
    ):
        logging.debug('per_joint_data_extract.__call__():  BEGIN!!!')
        stat = 1
        
        if per_joint_data_array[per_joint_data_index] is None:
            per_joint_data_array[per_joint_data_index] = nd.maya_per_joint_data()
            
        per_joint_data = per_joint_data_array[per_joint_data_index]
        
        #--------------------------------------------------------------
        # get envelope:
        input_envelope_handle = data_handle.child( self.input_joint_envelope_MObject )
        per_joint_data.envelope = input_envelope_handle.asDouble()
        #per_joint_data.envelope = input_envelope_handle.asFloat()
        envelope = per_joint_data.envelope
        logging.debug('per_joint_data_extract.__call__():  envelope:  {0}'.format(envelope))
        
        if abs(envelope) < self.tol:
            # the envelope is zero, so don't bother reading in any of the
            # matrix values:
            return stat
        
        # if the evaluation is here:  it means the envelope is non-zero.
        # Therefore:  read in some of the matrices, depending on 
        # matrix_mode's value:
        
        #--------------------------------------------------------------
        # get matrix_mode:
        input_matrix_mode_handle = data_handle.child( self.input_joint_matrix_mode_MObject )
        per_joint_data.matrix_mode = input_matrix_mode_handle.asShort()
        matrix_mode = per_joint_data.matrix_mode
        logging.debug('per_joint_data_extract.__call__():  matrix_mode:  {0}'.format(matrix_mode))
        
        #--------------------------------------------------------------
        # get matrices(based on matrix_mode):
        if matrix_mode == per_joint_data_extract.JOINT_MATRIX_MODE_T.LOCAL:
            logging.debug('per_joint_data_extract.__call__():  LOCAL read:  ')
            # read in the local matrix only:
            input_matrix_handle = data_handle.child( self.input_joint_matrix_MObject )
            per_joint_data.matrix = input_matrix_handle.asMatrix()
            #per_joint_data.matrix = input_matrix_handle.asFloatMatrix()
            
            logging.debug('per_joint_data_extract.__call__():  per_joint_data.matrix:  {0}'.format([per_joint_data.matrix(ii, jj) for ii in range(0, 4) for jj in range(0, 4)]))
        elif matrix_mode == per_joint_data_extract.JOINT_MATRIX_MODE_T.WORLD:
            logging.debug('per_joint_data_extract.__call__():  WORLD read:  ')
            # read in the world matrix and world parent matrix:
            input_world_matrix_handle = data_handle.child( self.input_joint_world_matrix_MObject )
            per_joint_data.world_matrix = input_world_matrix_handle.asMatrix()
            #per_joint_data.world_matrix = input_world_matrix_handle.asFloatMatrix()
            logging.debug('per_joint_data_extract.__call__():  per_joint_data.world_matrix:  {0}'.format([per_joint_data.world_matrix(ii, jj) for ii in range(0, 4) for jj in range(0, 4)]))
            
            input_world_parent_matrix_handle = data_handle.child( self.input_joint_world_parent_matrix_MObject )
            per_joint_data.world_parent_matrix = input_world_parent_matrix_handle.asMatrix()
            #per_joint_data.world_parent_matrix = input_world_parent_matrix_handle.asFloatMatrix()
            logging.debug('per_joint_data_extract.__call__():  per_joint_data.world_parent_matrix:  {0}'.format([per_joint_data.world_parent_matrix(ii, jj) for ii in range(0, 4) for jj in range(0, 4)]))
        else: # matrix_mode == per_joint_data_extract.JOINT_MATRIX_MODE_T.WORLDwInv:
            logging.debug('per_joint_data_extract.__call__():  WORLDwInv read:  ')
            # read in the world matrix and world parent inverse matrix:
            input_world_matrix_handle = data_handle.child( self.input_joint_world_matrix_MObject )
            per_joint_data.world_matrix = input_world_matrix_handle.asMatrix()
            #per_joint_data.world_matrix = input_world_matrix_handle.asFloatMatrix()
            logging.debug('per_joint_data_extract.__call__():  per_joint_data.world_matrix:  {0}'.format([per_joint_data.world_matrix(ii, jj) for ii in range(0, 4) for jj in range(0, 4)]))
            
            input_world_parent_inverse_matrix_handle = data_handle.child( self.input_joint_world_parent_inverse_matrix_MObject )
            per_joint_data.world_parent_inverse_matrix = input_world_parent_inverse_matrix_handle.asMatrix()
            #per_joint_data.world_parent_inverse_matrix = input_world_parent_inverse_matrix_handle.asFloatMatrix()
            logging.debug('per_joint_data_extract.__call__():  per_joint_data.world_parent_inverse_matrix:  {0}'.format([per_joint_data.world_parent_inverse_matrix(ii, jj) for ii in range(0, 4) for jj in range(0, 4)]))
            
        
        logging.debug('per_joint_data_extract.__call__():  END!!!')
        return stat

class mde_py_poseblends_driver(oMPx.MPxNode):
    kPluginNodeId = oM.MTypeId(
        MAYA_TYPE_ID_T.PREFIX1.value, 
        MAYA_TYPE_ID_T.MDE_PY_POSEBLENDS_DRIVER.value 
    )
    
    plugin_path = None
    
    input_envelope_ = oM.MObject()
    input_model_type_ = oM.MObject()
    input_joint_ = oM.MObject()
    input_joint_matrix_mode_ = oM.MObject()
    input_joint_envelope_ = oM.MObject()
    input_joint_matrix_ = oM.MObject()
    input_joint_world_matrix_ = oM.MObject()
    input_joint_world_parent_matrix_ = oM.MObject()
    input_joint_world_parent_inverse_matrix_ = oM.MObject()
    
    output_joint_ = oM.MObject()
    output_joint_blendshape_weights_ = oM.MObject()
    
    input_attrs = list()
    output_attrs = list()
    input_attr_long_names = list()
    output_attr_long_names = list()
    
    def __init__(self):
        oMPx.MPxNode.__init__(self)
        self.internal_node_data = nd.node_data()
        
    @staticmethod
    def is_output_plug(
        plug
    ):
        THIS_T = mde_py_poseblends_driver
        is_output_plug = False    
        
        # is the plug itself one of the output plugs?:
        if(
            (plug == THIS_T.output_joint_blendshape_weights_) or
            (plug == THIS_T.output_joint_)
        ):
            is_output_plug = True    
            return is_output_plug 
        
        # if the evaluation is here:  it means:
        # -the plug itself is _NOT_ one of the output plugs.
        # So:  if the plug is a child:  is its compound parent one of
        # the output plugs?:
        if (plug.isChild()):
            parent_plug = plug.parent()    
            
            if(
                (parent_plug == THIS_T.output_joint_blendshape_weights_) or
                (parent_plug == THIS_T.output_joint_)
            ):
                is_output_plug = True    
                return is_output_plug  
        
        # if the evaluation is here:  it means:
        # -the plug itself is _NOT_ one of the output plugs.
        # -if the plug is a compound child:  its parent is _NOT_ one of 
        # the output plugs.
        # So:  if the plug is a element:  is its array owner one of
        # the output plugs?:
        if (plug.isElement()):
            array_plug = plug.array()    
            if(
                (array_plug == THIS_T.output_joint_blendshape_weights_) or
                (array_plug == THIS_T.output_joint_)
            ):
                is_output_plug = True    
                return is_output_plug 
        
        # if the evaluation is here:  it means:
        # -plug is not any output plug.
        # -if plug is an array element:  its array is not any output plug.
        # -if plug is a compound child:  its parent is not any output plug.
        # So:  return false now:
        is_output_plug = False 
           
        return is_output_plug    
    
    def input_to_node_data(
        self,
        block
    ):
        logging.debug("mde_poseblends_driver.input_to_node_data:  BEGIN!!!")
    
        THIS_T = mde_py_poseblends_driver
        stat = 1
        
        #--------------------------------------------------input_envelope_:
        # Envelope data from the base class.
        # The envelope is simply a scale factor.
        #
        env_data_handle = None
        try:
            env_data_handle = block.inputValue(THIS_T.input_envelope_)
        except:
            logging.error("Error reading envelope")
            stat = 0
            return stat  
        
        self.internal_node_data.envelope = env_data_handle.asDouble() 
        #self.internal_node_data.envelope = env_data_handle.asFloat()    
        logging.debug('self.internal_node_data.envelope:  {0}'.format(self.internal_node_data.envelope))
        
        #--------------------------------------------------input_model_type_:
        #
        # SMPL or STAR?:
        model_type_data_handle = None
        try:
            model_type_data_handle = block.inputValue(THIS_T.input_model_type_)
        except:
            logging.error("Error reading model_type")  
            stat = 0
            return stat
                
        MODEL_T = mlpbd.poseblends_driver_data.MODEL_T
        self.internal_node_data.model_type = MODEL_T(model_type_data_handle.asShort())
        logging.debug('self.internal_node_data.model_type:  {0}'.format(self.internal_node_data.model_type))  
        
        #-----------------------------------------------------input_joint_:
        input_joint_extractor = per_joint_data_extract()
        
        # load input_joint_extractor with the input_joint_ child element 
        # attributes for it to extract:
        # 
        input_joint_extractor.input_joint_envelope_MObject = THIS_T.input_joint_envelope_    
        input_joint_extractor.input_joint_matrix_mode_MObject = THIS_T.input_joint_matrix_mode_    
        input_joint_extractor.input_joint_matrix_MObject = THIS_T.input_joint_matrix_    
        input_joint_extractor.input_joint_world_matrix_MObject = THIS_T.input_joint_world_matrix_    
        input_joint_extractor.input_joint_world_parent_matrix_MObject = THIS_T.input_joint_world_parent_matrix_    
        input_joint_extractor.input_joint_world_parent_inverse_matrix_MObject = THIS_T.input_joint_world_parent_inverse_matrix_    
        
        logging.debug('self.internal_node_data.maya_joint_data(before rma call):  {0}'.format(self.internal_node_data.maya_joint_data))  
        logging.debug('self.internal_node_data.joint_logical_indices(before rma call):  {0}'.format(self.internal_node_data.joint_logical_indices))  
        arg_num_input_joint_elements = []  
        rma.MDataBlock_ops.read_multi_attribute (
            block,
            THIS_T.input_joint_,
            input_joint_extractor,
            self.internal_node_data.maya_joint_data,
            self.internal_node_data.joint_logical_indices,
            arg_num_input_joint_elements
        )
        logging.debug('self.internal_node_data.maya_joint_data(after rma call):  {0}'.format(self.internal_node_data.maya_joint_data))  
        logging.debug('self.internal_node_data.joint_logical_indices(after rma call):  {0}'.format(self.internal_node_data.joint_logical_indices))  
        
        logging.debug("mde_poseblends_driver.input_to_node_data:  END!!!")
        return stat    
        
    def output_from_node_data(
        self,
        block
    ):
        # internal_node_data will have the outputs stored as:
        # data.joints_data[0...num_joints].blendshape_weights
        # Only the first 9 elements of blendshape_weights should
        # be used(ie one for each element of 3x3 rotation matrix):
    
        logging.debug("mde_py.poseblends_driver.output_from_node_data:  BEGIN!!!")
        
        THIS_T = mde_py_poseblends_driver
        
        stat = 1
        
        logging.debug("mde_py.poseblends_driver.output_from_node_data output results:  ")
        
        #-------------------------------------------------------------------
        #    output results... 
        out_handle = oM.MDataHandle()
    
        node = self.internal_node_data
        data = node.non_maya_data
        joint_data = data.joints_data
        joint_logical_indices = node.joint_logical_indices
        num_joints = len(joint_data)
    
        #--------------------------------------------------------------------------------
        output_joint_array_handle = None
        try:
            output_joint_array_handle = block.outputArrayValue( THIS_T.output_joint_ )
        except:
            logging.error("mde_py.poseblends_driver.output_from_node_data getting output_joint_array_handle")
            stat = 0
            return stat
    
        output_joint_builder = None
        try:
            output_joint_builder = oM.MArrayDataBuilder(block, THIS_T.output_joint_, num_joints)
        except:
            logging.error("mde_py.poseblends_driver.output_from_node_data creating output_joint_builder")
            stat = 0
            return stat
    
        for ii in range(0, num_joints):
            logging.debug("mde_py.poseblends_driver.output_from_node_data output boneExtend loop ii:  {0}".format(ii) )
            current_logical_index = joint_logical_indices[ii]
            out_joint_handle = output_joint_builder.addElement(current_logical_index)
        
            
            out_joint_blendshape_weights_handle = out_joint_handle.child( THIS_T.output_joint_blendshape_weights_ )
            
            out_joint_blendshape_weights_array_handle = None
            try:
                out_joint_blendshape_weights_array_handle = oM.MArrayDataHandle( out_joint_blendshape_weights_handle )
            except:
                logging.error("mde_py.poseblends_driver.output_from_node_data getting out_joint_blendshape_weights_array_handle")
                stat = 0
                return stat
            
            out_joint_blendshape_weights_array_builder = None
            try:
                out_joint_blendshape_weights_array_builder = out_joint_blendshape_weights_array_handle.builder()
            except:
                logging.error("mde_py.poseblends_driver.output_from_node_data creating out_joint_blendshape_weights_array_builder")
                stat = 0
                return stat
            
            current_blendshape_weights = joint_data[ii].blendshape_weights
            # num_blendshape_weights immediately below should only ever be 9 for SMPL and its flavors,
            # but we'll just use the size of the array to keep from hardcoding it
            # in case in changes in the future:
            # (which it did, to 4, when support for STAR was added)
            num_blendshape_weights = len(current_blendshape_weights)
            
            for jj in range(0, num_blendshape_weights):
                out_joint_blendshape_weight_handle = out_joint_blendshape_weights_array_builder.addElement(jj)
                
                current_value = current_blendshape_weights[jj]
                
                logging.debug("mde_py.poseblends_driver.output_from_node_data current_blendshape_weights[jj]:  {0}".format(current_value))
                out_joint_blendshape_weight_handle.setDouble(current_value)
                #out_joint_blendshape_weight_handle.setFloat(current_value)
        
    
                logging.debug("mde_py.poseblends_driver.output_from_node_data out_joint_blendshape_weight_handle.asDouble():  {0}".format(out_joint_blendshape_weight_handle.asDouble()))
                #logging.debug("mde_py.poseblends_driver.output_from_node_data out_joint_blendshape_weight_handle.asFloat():  {0}".format(out_joint_blendshape_weight_handle.asFloat()))
                
                out_joint_blendshape_weight_handle.setClean()
            #---------------------------------------------------------------------------------------
            try:
                out_joint_blendshape_weights_array_handle.set(out_joint_blendshape_weights_array_builder)
            except:
                logging.error("mde_py.poseblends_driver.output_from_node_data setting the out_joint_blendshape_weights_array_builder")
                stat = 0
                return stat
            
            try:    
                out_joint_blendshape_weights_array_handle.setAllClean()
            except:
                logging.error("mde_py.poseblends_driver.output_from_node_data cleaning out_joint_blendshape_weights_array_handle")
                stat = 0
                return stat
            
            out_joint_handle.setClean()
            
        #---------------------------------------------------------------------------------------
        try:
            output_joint_array_handle.set(output_joint_builder)
        except:
            logging.error("mde_py.poseblends_driver.output_from_node_data setting the output_joint_builder")
            stat = 0
            return stat
            
        try:
            output_joint_array_handle.setAllClean()
        except:
            logging.error("mde_py.poseblends_driver.output_from_node_data cleaning output_joint_array_handle")
            stat = 0
            return stat
            
        logging.debug("mde_py.poseblends_driver.output_from_node_data:  END!!!")
    
        return stat
        

    def compute(
        self, 
        plug, 
        block
    ):
        logging.debug("mde_poseblends_driver.compute:  BEGIN!!!")

        THIS_T = mde_py_poseblends_driver
        
        logging.debug('mde_poseblends_driver.compute:  before is_output_plug:  ')
        stat = 1
        if not THIS_T.is_output_plug(plug):
            return oM.kUnknownParameter
    
        
        logging.debug('mde_poseblends_driver.compute:  before input_to_node_data:  ')
        # STEP 1:  Get data off the Maya node(ie from the MDataBlock block)
        # and put it in internal_node_data:
        self.input_to_node_data(
            block
        )
        
        logging.debug('mde_poseblends_driver.compute:  before self.internal_node_data.calculate():  ')
        # STEP 2:  use internal_node_data to calculate the results:
        self.internal_node_data.calculate()
        
        logging.debug('mde_poseblends_driver.compute:  before output_from_node_data():  ')
        # STEP 3:  output calculation results from internal_node_data 
        # to MDataBlock block:
        self.output_from_node_data(
            block
        )

        logging.debug("mde_poseblends_driver.deform:  END!!!")
        return stat
 
def creator():
    return oMPx.asMPxPtr(mde_py_poseblends_driver())
 
def initialize():
    logging.debug("mde_poseblends_driver.initialize:  BEGIN!!!")
    
    THIS_T = mde_py_poseblends_driver
    # local attribute initialization
    stat = 1
    
    nAttr = oM.MFnNumericAttribute()
    eAttr = oM.MFnEnumAttribute()
    mAttr = oM.MFnMatrixAttribute()
    cAttr = oM.MFnCompoundAttribute()
    
    # input_attrs:
    #----------------------------------------------------inputEnvelope:
    attrLong = "inputEnvelope"
    attrShort = "inEnvelope"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    
    # I have commented out all calls to:
    # MFnAttribute::setDefault()
    # below because it seems like the Maya Python API 1.0 can't 
    # get them to work, or ???.  Like:  when I try to set them
    # using an external variable:
    #    nAttr.setDefault(input_envelope_default_value)
    # it fails like:  
    #    '(kInvalidParameter): The data is not of that type'
    # If I instead use MScriptUtil like:
    #    nAttr.setDefault(util.asDouble())
    # it fails the same way.
    # So:  I supply the defaults to the MFnAttribute::create()
    #    commands, and hope that those stick.
    # It sets my spider-senses tingling, though, because I think I 
    # remember circumstances in the past using the C++ API where the
    # default values did not stick unless you explcitly called
    # the setDefault() method, or maybe both the setDefault() method
    # AND supplying the default to the create() method:  ???
    

    input_envelope_default_value = 1.0
    #util = oM.MScriptUtil()
    #util.createFromDouble(input_envelope_default_value)
    THIS_T.input_envelope_ = nAttr.create( 
        attrLong, 
        attrShort,
        oM.MFnNumericData.kDouble, 
        #oM.MFnNumericData.kFloat, 
        input_envelope_default_value
    )
    nAttr.setMin(0.0)
    nAttr.setMax(1.0)
    #nAttr.setDefault(input_envelope_default_value)
    #nAttr.setDefault(util.asDouble())
    nAttr.setStorable(True)
    
    #---------------------------------------------------inputModelType:
    attrLong = "inputModelType"
    attrShort = "inModelType"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    
    input_model_type_default_value = 0
    THIS_T.input_model_type_ = eAttr.create( 
        attrLong, 
        attrShort,
        input_model_type_default_value
    )
    eAttr.addField("kSMPL", 0)
    eAttr.addField("kSTAR", 1)
    #eAttr.setDefault(input_model_type_default_value)
    eAttr.setStorable(True)
    eAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)
    
    #-----------------------------------------------inputJointEnvelope:
    attrLong = "inputJointEnvelope"
    attrShort = "inJointEnvelope"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    

    input_joint_envelope_default_value = 1.0
    THIS_T.input_joint_envelope_ = nAttr.create( 
        attrLong, 
        attrShort,
        oM.MFnNumericData.kDouble, 
        #oM.MFnNumericData.kFloat, 
        input_joint_envelope_default_value 
    )
    nAttr.setMin(0.0)
    nAttr.setMax(1.0)
    #nAttr.setDefault(input_joint_envelope_default_value)
    nAttr.setStorable(True)
    nAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)
    
    #---------------------------------------------inputJointMatrixMode:
    attrLong = "inputJointMatrixMode"
    attrShort = "inJointMatrixMode"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    
    input_joint_matrix_mode_default_value = 0
    THIS_T.input_joint_matrix_mode_ = eAttr.create( 
        attrLong, 
        attrShort, 
        input_joint_matrix_mode_default_value
    )
    eAttr.addField("LOCAL", 0)
    eAttr.addField("WORLD", 1)
    eAttr.addField("WORLDwInv", 2)
    #eAttr.setDefault(input_joint_matrix_mode_default_value)
    eAttr.setStorable(True)
    eAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)

    #-------------------------------------------------inputJointMatrix:
    attrLong = "inputJointMatrix"
    attrShort = "inJointMatrix"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    

    THIS_T.input_joint_matrix_ = mAttr.create( 
        attrLong, 
        attrShort,
        oM.MFnMatrixAttribute.kDouble,
        #oM.MFnMatrixAttribute.kFloat
    )
    mAttr.setStorable(True)
    mAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)
    
    #--------------------------------------------inputJointWorldMatrix:
    attrLong = "inputJointWorldMatrix"
    attrShort = "inJointWorldMatrix"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    

    THIS_T.input_joint_world_matrix_ = mAttr.create( 
        attrLong, 
        attrShort,
        oM.MFnMatrixAttribute.kDouble,
        #oM.MFnMatrixAttribute.kFloat
    )
    mAttr.setStorable(True)
    mAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)
    
    #--------------------------------------inputJointWorldParentMatrix:
    attrLong = "inputJointWorldParentMatrix"
    attrShort = "inJointWorldParentMatrix"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    

    THIS_T.input_joint_world_parent_matrix_ = mAttr.create( 
        attrLong, 
        attrShort,
        oM.MFnMatrixAttribute.kDouble,
        #oM.MFnMatrixAttribute.kFloat
    )
    mAttr.setStorable(True)
    mAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)
    
    #-------------------------------inputJointWorldParentInverseMatrix:
    attrLong = "inputJointWorldParentInverseMatrix"
    attrShort = "inJointWorldParentInverseMatrix"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    

    THIS_T.input_joint_world_parent_inverse_matrix_ = mAttr.create( 
        attrLong, 
        attrShort,
        oM.MFnMatrixAttribute.kDouble,
        #oM.MFnMatrixAttribute.kFloat
    )
    mAttr.setStorable(True)
    mAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)

    #-------------------------------------------------------inputJoint:
    #input_joint:  a compound array.  Each element contains:
    attrLong = "inputJoint"
    attrShort = "inJoint"
    
    # collect the attrLong name for error reporting:
    THIS_T.input_attr_long_names.append(attrLong)
    
    THIS_T.input_joint_ = cAttr.create( 
        attrLong, 
        attrShort
    )
    cAttr.addChild(THIS_T.input_joint_envelope_)
    cAttr.addChild(THIS_T.input_joint_matrix_mode_)
    cAttr.addChild(THIS_T.input_joint_matrix_)
    cAttr.addChild(THIS_T.input_joint_world_matrix_)
    cAttr.addChild(THIS_T.input_joint_world_parent_matrix_)
    cAttr.addChild(THIS_T.input_joint_world_parent_inverse_matrix_)
    cAttr.setStorable(True)
    cAttr.setArray(True)
    cAttr.setDisconnectBehavior(oM.MFnAttribute.kDelete)

    # output_attrs:
    #-------------------------------------outputJointBlendShapeWeights:
    #output_joint_blendshape_weights:  an array of doubles.  
    #  Only the first nine elements(ie based on 3x3 rotation matrix part of input matrix(ces) should be used.
    attrLong = "outputJointBlendShapeWeights"
    attrShort = "outJointBlendShapeWeights"
    
    # collect the attrLong name for error reporting:
    THIS_T.output_attr_long_names.append(attrLong)
    

    output_joint_blendshape_weights_default_value = 0.0
    THIS_T.output_joint_blendshape_weights_ = nAttr.create( 
        attrLong, 
        attrShort, 
        oM.MFnNumericData.kDouble, 
        #oM.MFnNumericData.kFloat, 
        output_joint_blendshape_weights_default_value 
    )
    nAttr.setMin(0.0)
    nAttr.setMax(1.0)
    #nAttr.setDefault(output_joint_blendshape_weights_default_value)
    nAttr.setArray(True)
    nAttr.setStorable(False)
    nAttr.setReadable(True)
    nAttr.setWritable(False)
    nAttr.setUsesArrayDataBuilder(True)
    
    #------------------------------------------------------outputJoint:
    #output_joint:  a compound array.  Each element contains:
    attrLong = "outputJoint"
    attrShort = "outJoint"
    
    # collect the attrLong name for error reporting:
    THIS_T.output_attr_long_names.append(attrLong)
    
    THIS_T.output_joint_ = cAttr.create( 
        attrLong, 
        attrShort
    )
    cAttr.addChild(THIS_T.output_joint_blendshape_weights_)
    cAttr.setStorable(False)
    cAttr.setReadable(True)
    cAttr.setWritable(False)
    cAttr.setArray(True)
    cAttr.setUsesArrayDataBuilder(True)
    
    #----------------------------------------------------addAttributes:
    # addAttributes:
    THIS_T.addAttribute( THIS_T.input_envelope_)
    THIS_T.addAttribute( THIS_T.input_model_type_)
    THIS_T.addAttribute( THIS_T.input_joint_)
    THIS_T.addAttribute( THIS_T.output_joint_)
    
    #-------------------------------------------------attributeAffects:
    # attributeAffects:
    # Make this exhaustive attributeAffects below with an inner and 
    # outer loop.  It makes it easier to add more attributes in the 
    # future, and is way better than the explosion of boilerplate code
    # that results by writing out every attributeAffects by hand:
    THIS_T.input_attrs.append( THIS_T.input_envelope_ )
    THIS_T.input_attrs.append( THIS_T.input_model_type_ )
    THIS_T.input_attrs.append( THIS_T.input_joint_ )
    THIS_T.input_attrs.append( THIS_T.input_joint_envelope_ )
    THIS_T.input_attrs.append( THIS_T.input_joint_matrix_mode_ )
    THIS_T.input_attrs.append( THIS_T.input_joint_matrix_ )
    THIS_T.input_attrs.append( THIS_T.input_joint_world_matrix_ )
    THIS_T.input_attrs.append( THIS_T.input_joint_world_parent_matrix_ )
    THIS_T.input_attrs.append( THIS_T.input_joint_world_parent_inverse_matrix_ )
    
    THIS_T.output_attrs.append( THIS_T.output_joint_ )
    THIS_T.output_attrs.append( THIS_T.output_joint_blendshape_weights_ )
  
    num_input_attrs = len(THIS_T.input_attrs)
    num_output_attrs = len(THIS_T.output_attrs)
    for ii in range(0, num_input_attrs): 
        current_input_attr = THIS_T.input_attrs[ii]
        for jj in range(0, num_output_attrs): 
            current_output_attr = THIS_T.output_attrs[jj]
            
            try:
                THIS_T.attributeAffects( 
                    current_input_attr, 
                    current_output_attr 
                )
            except:
                logging.error(":  attributeAffects failed on (input, output):  ({0}, {1})".format(THIS_T.input_attr_long_names[ii], THIS_T.output_attr_long_names[ii]) )
                stat = 0
                return stat
                
    logging.debug("mde_poseblends_driver.initialize:  END!!!")

    return stat
    
    
def initializePlugin(obj):
    plugin = oMPx.MFnPlugin(obj, 'Meshcapade', '1.0', 'Any')
    try:
        plugin.registerNode(
            'mde_py_poseblends_driver', 
            mde_py_poseblends_driver.kPluginNodeId, 
            creator, 
            initialize
        )
    except:
        raise RuntimeError('Failed to register node')
 
    mde_py_poseblends_driver.plugin_path = plugin.loadPath()
    
def uninitializePlugin(obj):
    plugin = oMPx.MFnPlugin(obj)
    try:
        plugin.deregisterNode(
            mde_py_poseblends_driver.kPluginNodeId
        )
    except:
        raise RuntimeError('Failed to register node')
