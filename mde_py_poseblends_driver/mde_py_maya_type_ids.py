# Maya type ids.
# Any Maya Python API object that requires an id must use these numbers.  
# If more ids are required, request them from Autodesk
# (at the time of writing this: it's several pages deep in 
#  Autodesk's Maya website).
#
# Use the MTypeId::MTypeId (unsigned prefix, unsigned id).  Where the prefix
# is shown below and the id is within the range 0-63.  (The two appear to
# be or'd together to make the actual id.)
#
# Meshcapade's prefix number:  0x00138740
# From the email Autodesk sent to Naureen:
# """
# Your Node ID Block is: 0x0013b2c0 - 0x0013b2ff
# In case of any problems, or questions regarding Maya Node IDs, please contact adn.sparks@autodesk.com
# """
# So:  64(0->63) unique IDs in that range.
import enum
	
@enum.unique
class maya_type_id(enum.IntEnum):
	
	PREFIX1								= 0x0013b2c0,
	
	# MDE_POSEBLENDS_DRIVER:  MPxNode to drive poseBlends corrective blendShape weights based on SMPL joints' rotations: 
	MDE_PY_POSEBLENDS_DRIVER		= 0,

	# End if type ids--contact Autodesk Maya for more if necessary
	# Do not use '64', as that's out-of-bounds:
	PREFIX1_END          				= 64,
