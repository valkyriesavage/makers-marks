import os

''' Matlab location and scripts '''
MATLAB = ''
if os.path.exists('/Applications/MATLAB_R2014a.app/bin/matlab'):
  MATLAB = '/Applications/MATLAB_R2014a.app/bin/matlab'
if os.path.exists('/Applications/MATLAB_R2014b.app/bin/matlab'):
  MATLAB = '/Applications/MATLAB_R2014b.app/bin/matlab'
SIFT_DETECT_SCRIPT = os.path.join(os.getcwd(), 'siftdetect.m')
FIND_ROTATION_SCRIPT = os.path.join(os.getcwd(), 'findrot.m')
TRANSFORM_OUTPUT = os.path.join(os.getcwd(), 'transform.txt')
SIFT_OUTPUT = os.path.join(os.getcwd(), 'sift.txt')


''' OpenSCAD location and scripts '''
OPENSCAD = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
OPENSCAD_OLD = '/Applications/OpenSCAD-old.app/Contents/MacOS/OpenSCAD'
CHECK_INTERSECT_SCRIPT = os.path.join(os.getcwd(), 'checkintersect.scad')
SUB_COMPONENT_SCRIPT = os.path.join(os.getcwd(), 'subcomps.scad')
PART_SCRIPT = os.path.join(os.getcwd(), 'part.scad')
BOSS_CHECK_COMPS_SCRIPT = os.path.join(os.getcwd(), 'bosscheckcomps.scad')
BOSS_PUT_SCRIPT = os.path.join(os.getcwd(), 'bossput.scad')
SHELL_SCRIPT = os.path.join(os.getcwd(), 'shell.scad')
DEFORM_SHELL_SCRIPT = os.path.join(os.getcwd(),'deformshell.scad')
MINKOWSKI_TOP = os.path.join(os.getcwd(), 'minkowski-top.scad')
MINKOWSKI_BOT = os.path.join(os.getcwd(), 'minkowski-bot.scad')
BUTTON_CAP_SCRIPT =  os.path.join(os.getcwd(), 'button-caps.scad')
SCRATCH = os.path.join(os.getcwd(),'scratch.stl')

