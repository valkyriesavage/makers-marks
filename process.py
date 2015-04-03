import os, subprocess, sys

''' Matlab location and scripts '''
MATLAB = '/Applications/MATLAB_R2014a.app/bin/matlab'
SIFT_DETECT_SCRIPT = os.path.join(os.getcwd(), 'siftdetect.m')
FIND_ROTATION_SCRIPT = os.path.join(os.getcwd(), 'findrot.m')
TRANSFORM_OUTPUT = os.path.join(os.getcwd(), 'transform.txt')

'''
We will give the following to this part of the pipeline:
  obj - a pointer to the scanned obj file (where all textures and geometry are)
We expect to receive the following from this part of the pipeline:
  list of dictionaries with format
  [{
    'coords':(x,y,z),
    'align_rot_vect':(x,y,z),
    'align_rot_angle':theta,
    'normal':(x,y,z),
    'normal_rotation':r_n,
    'fileloc':'components/button.stl'
    },
    ...
  ]
'''

def callMatlab(script, variables={}):
  script_path, script_name = os.path.split(script)
  script_name = script_name.split('.m')[0]
  matlab_calls = 'addpath(\'%s\'); ' % script_path
  for var, val in variables.iteritems():
    matlab_calls += '%s = %s; ' % (str(var),str(val))
  matlab_calls += '%s; exit();' % script_name
  call = [MATLAB, '-nodesktop', '-nodisplay', '-nosplash', '-nojvm',
          '-r', matlab_calls]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

def extractComponentInfo(location=TRANSFORM_OUTPUT):
  with open(location) as f:
    for line in f:
      print line

def identifyComponents():
  callMatlab(SIFT_DETECT_SCRIPT)
  return extractComponentInfo(SIFT_OUTPUT)


''' C++ locations and scripts '''
FIND_3D_COORDS_SCRIPT = os.path.join(os.getcwd(), 'sth.out')

def callCpp(script, args=''):
  call = [script, args]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

''' OpenSCAD location and scripts '''
OPENSCAD = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
CHECK_SIZE_SCRIPT = os.path.join(os.getcwd(), 'checksize.scad')
CHECK_INTERSECT_SCRIPT = os.path.join(os.getcwd(), 'checkintersect.scad')
SUB_COMPONENT_SCRIPT = os.path.join(os.getcwd(), 'subcomps.scad')
PART_SCRIPT = os.path.join(os.getcwd(), 'part.scad')
BOSS_SCRIPT = os.path.join(os.getcwd(), 'boss.scad')
SCRATCH = os.path.join(os.getcwd(),'scratch.stl')

'''
We will give the following to this part of the pipeline:
  list of dictionaries of components with format above
  STL file of scanned object
We expect to receive the following from this part of the pipeline:
  1st time : model w/o intersecting components & w/ enough space for components
  2nd time : two files with subbed comps, bosses, and parting lines

'''

def callOpenSCAD(script, oname, otherargs=''):
  call = [OPENSCAD, '-o', oname, otherargs, script]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

def placeCompOpenSCAD(component, geom_key='file_loc'):
  output = '''translate(%(coords)s) {
  rotate(a=%(align_rot_angle)s ,v=%(align_rot_vect)s ) {
    rotate(a=%(normal_rotation)s ,v=%(normal)s ) {
      import(%('''+geom_key+''')s );
    }
  }
}
'''
  return output % component

def writeOpenSCAD(script, components, body='', debug=False):
  text = ''
  if script is CHECK_SIZE_SCRIPT:
    comps = ''
    for component in components:
      comps += placeCompOpenSCAD(component, geom_key='interior_geom')
    text = '''
union() {
\timport("%(body)s");
%(comps)s}
''' % {
    'body':body,
    'comps':comps,
  }
  if script is CHECK_INTERSECT_SCRIPT:
    text = '''
intersection() {
  %(comp_0)
  %(comp_1)
}
''' % {
    'comp_0':placeCompOpenSCAD(components[0], geom_key='intersect_geom'),
    'comp_1':placeCompOpenSCAD(components[1], geom_key='intersect_geom'),
  }
  if script is SUB_COMPONENT_SCRIPT:
    text = "# Sean, fill me in!"
  if script is PART_SCRIPT:
    text = "# Sean, fill me in!"
  if script is BOSS_SCRIPT:
    text = "# Sean, fill me in!"
  if debug:
    print text
  else:
    f = open(script)
    f.write(text)
    f.close()

def isEmptySTL(fname=SCRATCH):
  with open(fname) as f:
    for line in f:
      if 'vertex' in line:
        return False
  return True

def checkIntersections(components):
  # check if any component intersects any other component
  intersection_script = CHECK_INTERSECT_SCRIPT
  intersection_file = SCRATCH
  for c1 in components:
    for c2 in components:
      if c1 == c2:
        continue
      writeOpenSCAD(intersection_script, [c1,c2])
      callOpenSCAD(intersection_script, intersection_script)
      if not isEmptySTL(intersection_file):
        raise Exception('%(c1)s (%(c1l)s) and %(c2)s (%(c2l)s) intersect!' %
                          {
                            'c1':c1['file_loc'],
                            'c1l':string(c1['coords']),
                            'c2':c2['file_loc'],
                            'c2l':string(c2['coords']),
                            }
                       )

''' Meshlab location and scripts '''
MESHLAB = '/Applications/meshlab.app/Contents/MacOS/meshlabserver'
SHELL_SCRIPT = os.path.join(os.getcwd(), 'shell.mlx')

'''
We will give the following to this part of the pipeline:
  STL file of scanned object
We expect to receive the following from this part of the pipeline:
  shelled STL file of scanned object

'''

def callMeshlab(fname, oname, script=SHELL_SCRIPT, otherargs=''):
  call = [MESHLAB, '-i', fname, '-o', oname, '-s', script]
  if otherargs:
    call.append(otherargs)
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)


''' imbue the data structures with our knowledge about them '''
def addPathsToDict(components):
  for component in components:
    component['geom'] = component['file_loc']
    component['interior_geom'] = component['file_loc']
    component['intersect_geom'] = component['file_loc']

''' main function '''

def main(obj):
  print obj
  #components = identifyComponents(body)
  #checkSize(components, body)
  #checkIntersections(components)
  #shell(body)
  #substitute_components(body,components)
  #bosses(body)
  #partingLine(components, body)
  print 'done!'

if __name__ == '__main__':
  main(sys.argv[1])
