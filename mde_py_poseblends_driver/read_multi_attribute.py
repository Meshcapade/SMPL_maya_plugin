import maya.OpenMaya as oM
import logging
import mde_utilities as utils
from builtins import next

# Wrapper to handle exception when MArrayDataHandle hits the end of the array.
def advance(array_handle):
    # got this from the Maya devkit examples:  ???
    # Don't know why it diverges so much from the C++ formulation.
    try:
        next(array_handle)
    except:
        return False
    
    return True
    
"""
    Given an array_plug on a node:  read the data from the elements
    of the array into a CONT_T<ELEMENT_T> element_array
    (This is the version that takes an MArrayDataHandle as an input,
     it is the generic guts used by the other versions(ie the MDataBlock
     and MDataHandle versions)):
    \param[in] input_array_handle:  the MArrayDataHandle of the multi attr from which to read.
    \param[in] element_read:  an implementation of FUNCTOR_T, called like:  element_read(CONT<ELEMENT_T> &dest, const unsigned &dest_element_index, const MDataHandle &source)
    \param[out] element_array:  the CONT_T<ELEMENT_T> result of values read from data.array_plug's elements.
    \param[out] logical_index_array:  for each element read:  the logical index of array_plug it was connected to.  This is useful for writing to corresponding output connections at node output time.
    \param[out] arg_num_input_elements:  the size of the element_array result, returned by reference as a list element
    \return the Maya status(kFailure or kSuccess)
"""
class MArrayDataHandle_ops(object):
    @staticmethod
    def read_multi_attribute(
        input_array_handle,
        element_read,
        element_array,
        logical_index_array,
        arg_num_input_elements
    ):
        logging.debug("read_multi_attribute(MArrayDataHandle version) BEGIN!!!:  ")
        stat = 1
        
        utils.resize(arg_num_input_elements, 1)
        
        #--------------------------------------------------------------------------------------
        # how many elements are currently on the input_array_handle?:
        num_input_elements = input_array_handle.elementCount()
        logging.debug("read_multi_attribute(MArrayDataHandle version) input_array_handle.elementCount():  {0}".format(num_input_elements))
    
        arg_num_input_elements[0] = num_input_elements
        
        if num_input_elements <= 0:
            # return early if input_array_handle is empty, clearing
            # all the result objects to indicate that is the case:
            num_input_elements = 0
            arg_num_input_elements[0] = num_input_elements
            utils.resize(element_array, num_input_elements)
            utils.resize(logical_index_array, num_input_elements)
            
            stat = 0
            return stat
        
        # resize the storage...
        utils.resize(element_array, num_input_elements)
        utils.resize(logical_index_array, num_input_elements)
        
        #--------------------------------------------------------------------------------------
        #for array_plug elements:
        if num_input_elements > 0:
            logging.debug("read_multi_attribute(MArrayDataHandle version):  in if num_input_elements > 0:")
            
            # get logical indices:
            array_index = 0
            for ii in range(input_array_handle.elementCount()):
                element_logical_index = None
                try:
                    element_logical_index = input_array_handle.elementIndex()
                except:
                    advance(input_array_handle)
                    continue
                    
                # preserve the logical index element_logical_index:
                logical_index_array[array_index] = element_logical_index
                
                logging.debug("read_multi_attribute(MArrayDataHandle version):  input_array_handle:  " + str(input_array_handle))
                input_handle = input_array_handle.inputValue()
                logging.debug("read_multi_attribute(MArrayDataHandle version):  input_handle:  " + str(input_handle))
                
                # read the value of the input_array_handle element:
                logging.debug("read_multi_attribute(MArrayDataHandle version):  in while loop before element_read:  ")
                # read the input_array_handle[element_logical_index] into element_array[element_logical_index]:
                element_read(
                    element_array, 
                    array_index, 
                    input_handle
                )
                logging.debug("read_multi_attribute(MArrayDataHandle version):  in while loop after element_read:  ")

                array_index += 1
                advance(input_array_handle)
                continue

        logging.debug("read_multi_attribute(MArrayDataHandle version) END!!!:  ")
        return stat

"""
    Given an array_plug on a node:  read the data from the elements
    of the array into a CONT_T<ELEMENT_T> element_array
    (This is the version that takes an MDataBlock as an input, like
     if array_plug is defined at the root-level of attributes on
     the node in question):
    \param[in] data:  the datablock of the node
    \param[in] array_plug:  the plug of the array attribute from which we are trying to read elements.
    \param[in] element_read:  an implementation of FUNCTOR_T, called like:  element_read(CONT<ELEMENT_T> &dest, const unsigned &dest_element_index, const MDataHandle &source)
    \param[out] element_array:  the CONT_T<ELEMENT_T> result of values read from data.array_plug's elements.
    \param[out] logical_index_array:  for each element read:  the logical index of array_plug it was connected to.  This is useful for writing to corresponding output connections at node output time.
    \param[out] arg_num_input_elements:  the size of the element_array result, returned by reference as a list element
    \return the Maya status(kFailure or kSuccess)
"""
class MDataBlock_ops:
    @staticmethod
    def read_multi_attribute(
        data,
        array_plug,
        element_read,
        element_array,
        logical_index_array,
        arg_num_input_elements
    ):
            
        logging.debug("read_multi_attribute(MDataBlock version) BEGIN!!!:  ")
        
        stat = 1
        
        #--------------------------------------------------------------------------------------
        # get array_plug:
    
        #for array_plug:
        input_array_handle = None
        try:
            input_array_handle = data.inputArrayValue( array_plug )
        except:
            logging.error("read_multi_attribute(MDataBlock version) getting array_plug input_array_handle data")
            stat = 0
            return stat
            
        MADH_ops = MArrayDataHandle_ops 
        
        stat = MArrayDataHandle_ops.read_multi_attribute(
            input_array_handle,
            element_read,
            element_array,
            logical_index_array,
            arg_num_input_elements
        )
        
        logging.debug("read_multi_attribute(MDataBlock version) END!!!:  ")
        
        return stat


"""
    Given an array_plug on a node:  read the data from the elements
    of the array into a CONT_T<ELEMENT_T> element_array
    (This is the version that takes an MDataHandle as an input, as
     if the array_plug is defined as part of a compound multi attribute):
    \param[in] array_data_handle:  the data handle of the multi attr from which to read.
    \param[in] element_read:  an implementation of FUNCTOR_T, called like:  element_read(CONT<ELEMENT_T> &dest, const unsigned &dest_element_index, const MDataHandle &source)
    \param[out] element_array:  the CONT_T<ELEMENT_T> result of values read from data.array_plug's elements.
    \param[out] logical_index_array:  for each element read:  the logical index of array_plug it was connected to.  This is useful for writing to corresponding output connections at node output time.
    \param[out] arg_num_input_elements:  the size of the element_array result, returned by reference as a list element
    \return the Maya status(kFailure or kSuccess)
"""
class MDataHandle_ops:
    def read_multi_attribute(
        array_data_handle,
        element_read,
        element_array,
        logical_index_array,
        num_input_elements
    ):
            
        logging.debug("read_multi_attribute(MDataHandle version) BEGIN!!!:  ")
        
        stat = 1
        
        #--------------------------------------------------------------------------------------
        # get array_data_handle:
    
        #for array_data_handle:
        input_array_handle = None
        try:
            input_array_handle = oM.MArrayDataHandle( array_data_handle )
        except:
            logging.error("read_multi_attribute(MDataHandle version) getting array_data_handle input_array_handle data")
            stat = 0
            return stat
        
        MADH_ops = MArrayDataHandle_ops 
        
        stat = MArrayDataHandle_ops.read_multi_attribute(
            input_array_handle,
            element_read,
            element_array,
            logical_index_array,
            arg_num_input_elements
        )
        
        logging.debug("read_multi_attribute(MDataHandle version) END!!!:  ")
        return stat
        

"""
    Let's say the user is inputting multiple multi(ie array) attributes
    from the same node.  For example:  maybe several lists of matrices
    that are supposed to be the exact same length however, for some 
    reason(maybe it's even just a momentary fluke at file-read time, or
    some similar temporary early evaluation before all the attributes are
    connected to the node properly):  the numbers of elements in the
    multi-attrs don't match.  This procedure is meant to fill any of
    the element_arrays read in using read_multi_attribute() procedures
    (defined earlier/elsewhere in this same header file) with default
    values until they _do_ match a num_desired_elements.  So:  in the
    multiple matrices array examples:  you might find the length of
    the longest of the arrays, then use this procedure to fill any 
    arrays that aren't that length with the identity matrix until all
    the arrays _are_ that length.
    \param[in] num_desired_elements:  number of elements desired to exist on array.
    \param[in] num_input_elements:  the number of elements that _do_ currently exist on array.
    \param[in] use_single_default_value:  if true:  use default_value for all new elements.  if false:  draw from the elements of default_value_array in order for all new elements.  It is assumed default_value_array is at least of length num_desired_elements.
    \param[in] default_value:  if use_single_default_value is true:  this is the value to use.
    \param[in] default_value_array:  if use_single_default_value is false:  these are the values to use.  It is assumed default_value_array is at least of length num_desired_elements, so that array[ii] = default_value_array[ii] will not be an out-of-bounds access.
    \param[out] array:  the array that will be filled with default values until it is of size num_desired_elements.
    \param[out] logical_index_array:  for each element read:  the logical index of the element in the attribute array.  This is useful for writing to corresponding output connections at node output time.  It needs to be augmented by this procedure since elements are being added to array.
    \return void
"""
def fill_missing_array_elements(
    num_desired_elements,
    num_input_elements,
    use_single_default_value,
    default_value,
    default_value_array,
    array,
    logical_index_array
):
    logging.debug("fill_missing_array_elements begin:  ")
    num_existing_elements = len(array)

    if(num_input_elements >= num_desired_elements):
        return
    
    # resize storage if necessary:
    if(
        (num_existing_elements < num_desired_elements) or
        (num_existing_elements < num_input_elements)
    ):
        utils.resize(array, num_desired_elements)
        utils.resize(logical_index_array, num_desired_elements)
    
    for ii in range(num_input_elements, num_desired_elements):
        # fill array new elements with default values:
        current_default_value = None
        if use_single_default_value == True:
            current_default_value = default_value
        else:
            current_default_value = default_value_array[ii]
        array[ii] = current_default_value
        
    for ii in range(num_input_elements, num_desired_elements):
        # fill logical_index_array new elements:
        current_logical_index = None
        if(ii == 0):
            current_logical_index = 0
        else:
            current_logical_index = logical_index_array[ii - 1] + 1 
        logical_index_array[ii] = current_logical_index
        
    logging.debug("fill_missing_array_elements end:  ")
    
    
