
def resize(
	arg_list,
	new_size
):
	# So:  I think there is not a resize for Python lists like there
	# is for C++ std::vector.
	# I'm trying to make the guts of this Python plugin match the guts
	# of the C++ one as much as possible, so that's one reason to write this.
	# The other is:  the memory for this won't change often.
	# That is:  on file open or file reference:  it will need to call
	# this to actually resize the arg_list.
	# ; however, most calls to this, once the file is open and the user
	# is interacting with the scene, will be to check that the length has not
	# changed from what is desired, and do nothing. 
	num_list = len(arg_list)
	
	if(num_list == new_size):
		return
	elif(num_list < new_size):
		for ii in range(num_list, new_size):
			arg_list.append(None)
	else:
		# num_list > new_size
		for ii in range(new_size, num_list):
			arg_list.pop()
		
