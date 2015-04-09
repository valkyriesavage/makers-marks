import os, subprocess, sys

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


'''
We will give the following to this part of the pipeline:
  obj - a pointer to the scanned obj file (where all textures and geometry are)
We expect to receive the following from this part of the pipeline:
  list of dictionaries with format
  [{
    'coords':(x,y,z),
    'rotations':(0,y,z),
    'axis_rot':theta,
    'normal':(x,y,z),
    'fileloc':'components/button.stl',
    'filename': 'texture_T1.jpg',
    'left': (u,v),
    'right': (u,v),
    'center': (u,v),    <- these three are for the C++ program
    'threed_center': (x,y,z),
    ...
    },
    ...
  ]
'''

def callMatlab(script, variables={}):
  script_path, script_name = os.path.split(script)
  script_name = script_name.split('.m')[0]
  matlab_calls = 'addpath(\'%s\'); ' % script_path
  for var, val in variables.iteritems():
    if isinstance(val, basestring):
      matlab_calls += '%s = \'%s\'; ' % (str(var),str(val))
    else:
      matlab_calls += '%s = %s; ' % (str(var),str(val))
  matlab_calls += '%s; exit();' % script_name
  call = [MATLAB, '-nodesktop', '-nodisplay', '-nosplash', '-nojvm',
          '-r', matlab_calls]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

def extractComponentInfo(location=TRANSFORM_OUTPUT): #currently not in use - delete at end
  info = {}
  with open(location) as f:
    for line in f:
      name,val = line.split()
      # a totally unsafe practice.  but... eh.
      info[name] = eval(val)
  return info

def extractSIFTComponentInfo(location=SIFT_OUTPUT):
  centroid_locations = []
  with open(location) as f:
    for l in f:
      name, val = l.split()
      if name == 'sticker':
        sticker_dict = {}
      elif name == 'filename':
        sticker_dict[name] = val
      elif name == 'left' or name == 'center':
        sticker_dict[name] = eval(val)
      elif name == 'right':
        #this assumes right is the last thing we see
        sticker_dict[name] = eval(val)
        centroid_locations.append(sticker_dict.copy())
  return centroid_locations

def getAlignmentInfo(component):
  # in here we need threed_center, threed_top_right,
  # threed_top_left, and threed_normal
  callMatlab(FIND_ROTATION_SCRIPT, component)
  calculated = extractComponentInfo(location=TRANSFORM_OUTPUT)
  component.update(calculated)
  return component

def identifyComponents(obj):
  callMatlab(SIFT_DETECT_SCRIPT)
  comp_list = extractSIFTComponentInfo(SIFT_OUTPUT)
  # now call c++...
  for tag_dictionary in comp_list: #get dictionaries through list
    args = ["./triCheck", obj]
    #local declaration...this code is so bad? i'm sorry
    correct_jpg, left_u, left_v, center_u, center_v, right_u, right_v = '', '', '', '', '', '', ''
    for tag in tag_dictionary.keys():
      if tag == 'filename':
        correct_jpg = tag_dictionary[tag]
      elif tag == 'left':
        left_u, left_v = repr(tag_dictionary[tag][0]), repr(tag_dictionary[tag][1])
      elif tag == 'center':
        center_u, center_v = repr(tag_dictionary[tag][0]), repr(tag_dictionary[tag][1])
      elif tag == 'right':
        right_u, right_v = repr(tag_dictionary[tag][0]), repr(tag_dictionary[tag][1])
    args.extend((correct_jpg, left_u, left_v, center_u, center_v, right_u, right_v))
    callCpp(tag_dictionary, args)
  #now dictionary modified with threed_etc additions
  for idx, comp in enumerate(comp_list):
    comp_list[idx] = getAlignmentInfo(comp) #reassigning the value
  return comp_list

def callCpp(tag_dictionary, args):
  #args = ['./triCheck', 'filename', 'lu', 'lv', 'cu', 'cv', 'ru', 'rv']
  print args
  proc = subprocess.Popen(args, stdout=subprocess.PIPE)
  for line in proc.stdout:
    if len(line.split()) == 2:
      name, value = line.split()
      if name == 'Left':
        tag_dictionary['threed_top_left'] = eval(value)
      elif name == 'Center':
        tag_dictionary['threed_center'] = eval(value)
      elif name == 'Right':
        tag_dictionary['threed_top_right'] = eval(value)
      elif name == 'Normal':
        tag_dictionary['threed_normal'] = eval(value)
    else:
      print line.split(), ' --  something wrong here'

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
  output = '''
translate(%(coords)s) {
  rotate(%(rotations)s) {
    rotate([0,0,%(axis_rot)s) {
      import("%('''+geom_key+''')s");
    }
  }
}
'''
  return output % component

def writeOpenSCAD(script, components, object_body='', debug=False):
  text = ''
  if script is CHECK_SIZE_SCRIPT:
    comps = ''
    for component in components:
      comps += placeCompOpenSCAD(component, geom_key='interior_geom')
    text = '''
union() {
\timport("%(obj)s");
%(comps)s}
''' % {
    'obj':object_body,
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

def checkSize(components):
  # ensure that the components all will fit in the body
  union_script = CHECK_SIZE_SCRIPT
  unioned_file = SCRATCH
  writeOpenSCAD(union_script, components, object_body='obj/controller.stl') #TODO FIXME HFS
  callOpenSCAD(union_script, unioned_file)

def checkIntersections(components):
  # check if any component intersects any other component
  intersection_script = CHECK_INTERSECT_SCRIPT
  intersection_file = SCRATCH
  for c1 in components:
    for c2 in components:
      if c1 == c2:
        continue
      writeOpenSCAD(intersection_script, [c1,c2])
      callOpenSCAD(intersection_script, intersection_file)
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
SHELL_SCRIPT = os.path.join(os.getcwd(), 'deflate.mlx')

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
  components = identifyComponents(obj)
  print components
  #checkSize(components, obj)
  #checkIntersections(components)
  #shell(obj)
  #substitute_components(obj,components)
  #bosses(obj)
  #partingLine(components, obj)
  print 'done!'

if __name__ == '__main__':
  main(sys.argv[1])
