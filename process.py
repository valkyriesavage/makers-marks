import os, subprocess, sys
from enum import Enum

class Component(Enum):
  button = 0
  joystick = 1
  speaker = 2
  main_board = 3
  hinge = 4
  parting_line = 5
  screen = 6
  LED_ring = 7
  potentiometer = 8
  light_sensor = 9
  gyro = 10
  knob = 11
  handle = 12
  hasp = 13

  no_offset = [hinge,knob,handle,hasp,parting_line]

  @classmethod
  def getCompType(cls, tinystr):
    match_dict = {
      'b':cls.button,
      'j':cls.joystick,
      's':cls.speaker,
      'm':cls.main_board,
      'h':cls.hinge,
      'l':cls.parting_line,
      'r':cls.parting_line,
      # jingyi, please update this as you add more!
    }
    return match_dict[tinystr]

  @classmethod
  def toStr(cls, comptype):
    strz = {
      cls.button: 'button',
      cls.joystick: 'joystick',
      cls.speaker: 'speaker',
      cls.main_board: 'main_board',
      cls.hinge: 'hinge',
      cls.parting_line: 'parting_line',
      cls.screen: 'screen',
      cls.LED_ring: 'LED_ring',
      cls.potentiometer: 'potentiometer',
      cls.light_sensor: 'light_sensor',
      cls.gyro: 'gyro',
      cls.knob: 'knob',
      cls.handle: 'handle',
      cls.hasp: 'hasp'
    }
    return strz[comptype]

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
    'type':Component.button,
    'subtract':'components/button_subtract.stl',
    'add':'components/button_add.stl',
    'check':'components/button_check.stl',
    'filename': 'texture_T1.jpg',
    'left': (u,v),
    'right': (u,v),
    'center': (u,v),    <- these three are for the C++ program
    'threed_center': (x,y,z),
    'threed_top_left': (x,y,z),
    'threed_top_right': (x,y,z),
    },
    ...
  ]
'''

def callMatlab(script, variables={}):
  script_path, script_name = os.path.split(script)
  script_name = script_name.split('.m')[0]
  matlab_calls = 'addpath(\'%s\'); ' % script_path
  for var, val in variables.iteritems():
    if var in ['type']:
      continue
    if isinstance(val, basestring):
      matlab_calls += '%s = \'%s\'; ' % (str(var),str(val))
    else:
      matlab_calls += '%s = %s; ' % (str(var),str(val))
  matlab_calls += '%s; exit();' % script_name
  call = [MATLAB, '-nodesktop', '-nodisplay', '-nosplash', '-nojvm',
          '-r', matlab_calls]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

def extractComponentInfo(location=TRANSFORM_OUTPUT):
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
        comp_type = val.split('.')[0].strip('0123456789')
        comp_type = Component.getCompType(comp_type)
        sticker_dict = {'type':comp_type}
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
  print ' '.join(args)
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
CHECK_INTERSECT_SCRIPT = os.path.join(os.getcwd(), 'checkintersect.scad')
SUB_COMPONENT_SCRIPT = os.path.join(os.getcwd(), 'subcomps.scad')
PART_SCRIPT = os.path.join(os.getcwd(), 'part.scad')
BOSS_SCRIPT = os.path.join(os.getcwd(), 'boss.scad')
SHELL_SCRIPT = os.path.join(os.getcwd(), 'shell.scad')
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
  call = [OPENSCAD, '-o', oname, script]
  if not otherargs == '':
    call = [OPENSCAD, '-o', oname, otherargs, script]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

def placeCompOpenSCAD(component, geom):
  output = '''
translate(%(coords)s) {
  rotate(%(rotations)s) {
    rotate(%(axis)s) {
      import("stls/'''+Component.toStr(component['type'])+'_'+geom+'''.stl");
    }
  }
}
'''
  return output % component

def writeOpenSCAD(script, components={}, object_body='', deflated='', debug=False):
  text = ''
  if script is CHECK_INTERSECT_SCRIPT:
    text = '''
intersection() {
  %(comp_0)
  %(comp_1)
}
''' % {
    'comp_0':placeCompOpenSCAD(components[0], geom_key='clearance'),
    'comp_1':placeCompOpenSCAD(components[1], geom_key='clearance'),
  }
  if script is SUB_COMPONENT_SCRIPT:
    comps_sub = ''
    comps_add = ''
    for component in components:
      if component['type'] == Component.parting_line:
        # these will be dealt with in a special step later
        continue
      comps_sub += placeCompOpenSCAD(component, geom_key='sub')
      comps_add += placeCompOpenSCAD(component, geom_key='add')
    text = '''
difference() {
\timport("%(obj)s");
// first we need to subtract everything
\t%(comps_sub)s
}
// now we add mounting points back in
%(comps_add)s
''' % {
    'obj':object_body,
    'comps_sub':comps_sub,
    'comps_add':comps_add,
  }
  if script is PART_SCRIPT:
    text = "# Sean, fill me in!"
  if script is BOSS_SCRIPT:
    text = "# Sean, fill me in!"
  if script is SHELL_SCRIPT:
    text = '''
difference() {
  import("%(obj)s");
  import("%(deflated)s");
}
''' % {
      'obj':object_body,
      'deflated':deflated
    }
  if debug:
    print text
  else:
    f = open(script, 'w+')
    f.write(text)
    f.close()

def isEmptySTL(fname=SCRATCH):
  with open(fname) as f:
    for line in f:
      if 'vertex' in line:
        return False
  return True

def shell(stl):
  deflated = stl.replace('.stl','-deflated.stl')
  oname = stl.replace('.stl','-shelled.stl')
  writeOpenSCAD(SHELL_SCRIPT, object_body=stl, deflated=deflated)
  callOpenSCAD(SHELL_SCRIPT, oname)

def determineFitOffset(components, obj):
  # figure out how far back we need to set each component to make it
  # not intersect the body of the object.
  for comp in components:
    #if comp['type'] in Component.no_offset:
    #  continue
    loc = comp['coords']
    normal = comp['threed_normal']
    ct = 0
    while True:
      mod_comp = dict(comp)
      mod_comp[coords] = [c_i - n_i for c_i, n_i in zip(loc, normal)]
      print mod_comp[coords]
      writeOpenSCAD(CHECK_INTERSECT_SCRIPT, [mod_comp,obj])
      callOpenSCAD(CHECK_INTERSECT_SCRIPT, SCRATCH)
      if isEmptySTL(SCRATCH) or ct > 3:
        break
      loc = mod_comp[coords]
      ct += 1
    comp['coords'] = loc
  return components

def checkIntersections(components):
  # check if any component intersects any other component
  for c1 in components:
    for c2 in components:
      if c1 == c2:
        continue
      writeOpenSCAD(CHECK_INTERSECT_SCRIPT, [c1,c2])
      callOpenSCAD(CHECK_INTERSECT_SCRIPT, SCRATCH)
      if not isEmptySTL(SCRATCH):
        raise Exception('%(c1)s (%(c1l)s) and %(c2)s (%(c2l)s) intersect!' %
                          {
                            'c1':c1['type'],
                            'c1l':string(c1['coords']),
                            'c2':c2['type'],
                            'c2l':string(c2['coords']),
                            }
                       )

def substitute_components(components, stl):
  writeOpenSCAD(SUB_COMPONENT_SCRIPT, components, object_body=stl)
  oname = stl.replace('.stl','-compsubbed.stl')
  callOpenSCAD(SUB_COMPONENT_SCRIPT, oname)
  return oname

def bosses(components, stl):
  return stl

def partingLine(components, stl):
  # TODO valkyrie: need to actually make two scripts: gotta get parts
  #                A and B out of this thing.  sigh.
  writeOpenSCAD(PART_SCRIPT, components, object_body=stl)
  return (0,0)

''' main function '''

def main(obj):
  print obj
  stl = 'obj/'+obj.replace('.obj','.stl')
  components = identifyComponents(obj)
  print components
  stl = shell(stl)
  components = determineFitOffset(components)
  checkIntersections(components)
  stl = substitute_components(components, stl)
  stl = bosses(stl)
  side1, side2 = partingLine(components, stl)
  print 'done!'

if __name__ == '__main__':
  main(sys.argv[1])
