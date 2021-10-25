Copyright 2021 Meshcapade GmbH and Max Planck Gesellschaft.  All rights reserved.

More information about the SMPL model research project is available here http://smpl.is.tue.mpg
For SMPL Model commercial use options, please visit https://meshcapade.com/infopages/licensing.html
For comments or questions, please email us at: support@meshcapade.com

Installation:
--------------------------
To load SMPL_maya_plugin directly into Maya:  follow these steps:
1.  Windows -> Settings/Preferences -> Plug-in Manager.  This starts the "Plug-in Manager UI".
2.  Click the "Browse" button in the bottom Lf corner of the "Plug-in Manager" UI.
3.  In the resulting "Load Plugin" window, in the field labelled "Look in:":  type the path to the directory where SMPL_maya_plugin resides(ie where it was downloaded, or where it was moved after downloading).  After pressing the Enter key:  the contents of the directory should show up in the directory listing widget immediately below the "Look in:" field.  "SMPL_maya_plugin.py" should be among the listed files.
4.  Double-click on "SMPL_maya_plugin.py" in the directory listing in the "Load Plugin" UI.  
    This will:  a.  load the plugin, and b.  launch the plugin's UI.

Instructions to edit environment variables so Maya can find the plugin upon starting:
https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2022/ENU/Maya-Customizing/files/GUID-FA51BD26-86F3-4F41-9486-2C3CF52B9E17-htm.html
    

Sample FBX files for use with this script:
--------------------------
This script allows you to manually edit SMPL Model animations inside Maya. You can download some FBX files for SMPL, SMPLH and SMPLX to use with this script at: [SMPL FBX Samples](https://app.box.com/s/2yn9znx56icf3t77s4h9b4qxa3b25rdb)


Current versions supported:
--------------------------
Windows: Maya 2022


Dependencies:
------------
Numpy is required for running this script. Numpy is a python module that
can be installed following the instructions given here:
http://docs.scipy.org/doc/numpy/user/install.html


About the Script:
-----------------
The script displays a UI to apply SMPL's shape and pose blendshapes and to adjust the skeleton to new body shapes.
Load this plugin into Maya. It will create a window with 3 options:

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
    
3- Set Mesh to Bind-Pose & Recompute Skeleton: 
	When you edit the shape blend shapes to change body shape the 
	skeleton will no longer be correct.  Click first button to set the 
    mesh into the bind-pose. Next, click this to 'Recompute Skeleton' 
    to recompute the skeleton rig to match the new body shape.

Always make sure to click on the mesh in the 3D view to select it before 
using any of the functions in the plugin. Select only the mesh of the model 
you want to update and then click the appropriate button on the UI.

