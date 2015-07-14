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
  servo_mount = 14
  servo_move = 15
  boss = 16
  parting_line_calculated = 17
  camera = 18
  raspberry_pi = 19
  hole = 20

  @classmethod
  def no_offset(cls):
    return [cls.hinge,cls.knob,cls.handle,cls.hasp,
            cls.parting_line,cls.parting_line_calculated,
            cls.boss,cls.servo_mount]
  
  @classmethod
  def no_moving(cls): #for deformation
    return [cls.button,cls.joystick, cls.parting_line,
            cls.parting_line_calculated, cls.servo_move,
            cls.camera,cls.knob]


  @classmethod
  def part(cls, comptype):
    part_at = [cls.hinge,cls.parting_line,cls.parting_line_calculated]
    for partable in part_at:
      if comptype is partable:
        return True
    return False

  @classmethod
  def getCompType(cls, tinystr):
    match_dict = {
      'b':cls.button,
      'j':cls.joystick,
      's':cls.speaker,
      'm':cls.main_board,
      'gyro':cls.gyro,
      'd':cls.light_sensor,
      'h':cls.hinge,
      'l':cls.parting_line,
      'led':cls.LED_ring,
      'r':cls.parting_line,
      'knob':cls.knob,
      'screen':cls.screen,
      'smount':cls.servo_mount,
      'smove':cls.servo_move,
      'rpi':cls.raspberry_pi,
      'cam':cls.camera,
      'hole':cls.hole
      # jingyi, please update this as you add more!
    }
    return match_dict[tinystr]

  @classmethod
  def max_offset(cls, comptype):
    if Component.no_offset():
      return 0
    match_dict = {
        cls.button: 30,
        cls.joystick: 15,
        cls.speaker: 50,
        cls.main_board: 50,
        cls.gyro: 50,
        cls.light_sensor: 30,
        cls.LED_ring: 10,
        cls.knob: 10,
        cls.screen: 10,
        cls.servo_mount: 3,
        cls.servo_move: 3,
        cls.raspberry_pi: 50,
        cls.camera: 10,
        cls.hole: 30, #i totally guessed on these last 3 values
      # jingyi, please update this as you add more!
    }
    if not comptype in match_dict:
      return 10 # default to 1mm

  @classmethod
  def no_trim(cls, comptype):
    if comptype == cls.servo_move:
      return True
    return False

  @classmethod
  def toStr(cls, comptype):
    return comptype.name

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
      if val == 'NaN':
        val = '0'
      info[name] = eval(val)
  return info

def extractSIFTComponentInfo(location=SIFT_OUTPUT):
  centroid_locations = []
  cur_sticker = ''
  cur_list = []
  with open(location) as f:
    for l in f:
      name, val = l.split()
      if name == 'sticker':
        if val != cur_sticker:
          if cur_sticker != '':
            centroid_locations.append(cur_list)
          cur_sticker = val
          cur_list = []
        comp_type = val.split('.')[0].strip('0123456789')
        comp_type = Component.getCompType(comp_type)
        sticker_dict = {'type':comp_type}
      elif name == 'filename':
        sticker_dict[name] = val
      elif name == 'inliers':
        sticker_dict[name] = float(val)
      elif name == 'left' or name == 'center':
        sticker_dict[name] = eval(val)
      elif name == 'right':
        #this assumes right is the last thing we see
        sticker_dict[name] = eval(val)
        cur_list.append(sticker_dict.copy())
  centroid_locations.append(cur_list)
  return centroid_locations

def getAlignmentInfo(component):
  # in here we need threed_center, threed_top_right,
  # threed_top_left, and threed_normal
  callMatlab(FIND_ROTATION_SCRIPT, component)
  calculated = extractComponentInfo(location=TRANSFORM_OUTPUT)
  component.update(calculated)
  return component

def postProcComps(comps):
  # basically, we need to do any calculations (e.g., for parting line)
  parting_lines_to_avg = []
  for comp in comps:
    if comp['type'] == Component.parting_line:
      parting_lines_to_avg.append(comp)
  if len(parting_lines_to_avg) > 1:
    varz = {}
    varz['pl1_threed_center'] = parting_lines_to_avg[0]['threed_center']
    varz['pl1_top_left'] = parting_lines_to_avg[0]['threed_top_left']
    varz['pl1_top_right'] = parting_lines_to_avg[0]['threed_top_right']
    varz['pl2_threed_center'] = parting_lines_to_avg[1]['threed_center']
    varz['pl2_top_left'] = parting_lines_to_avg[1]['threed_top_left']
    varz['pl2_top_right'] = parting_lines_to_avg[1]['threed_top_right']
    callMatlab('partingLine.m', variables=varz)
    calculated_pl = extractComponentInfo()
    calculated_pl['type'] = Component.parting_line_calculated
    comps.append(calculated_pl)
    #comps.remove([comp for comp in parting_lines_to_avg]) # don't need 'em
  elif len(parting_lines_to_avg) == 1:
    parting_lines_to_avg[0]['type'] = Component.parting_line_calculated
  return comps

def identifyComponents(obj):
  #callMatlab(SIFT_DETECT_SCRIPT)
  comp_list = extractSIFTComponentInfo(SIFT_OUTPUT)
  print "after matlab, COMP LIST IS "
  print comp_list
  final_list = []
  #now call c++...this code could be cleaner
  for list_of_tag_dics in comp_list:
    final_dict = {}
    final_dict['threed_center'] = [0,0,0]
    final_dict['threed_top_left'] = [0,0,0]
    final_dict['threed_top_right'] = [0,0,0]
    inlier_counts = [(td['inliers'],idx) for idx,td in enumerate(list_of_tag_dics)]
    inlier_counts = sorted(inlier_counts)
    inlier_counts.reverse()
    i = 0
    for tag_dictionary in list_of_tag_dics: #get dictionaries through list
      args = ["./triCheck", obj]
      dict_w_most_inliers = list_of_tag_dics[inlier_counts[i][1]]
      callCppIntermediate(dict_w_most_inliers, args)
      if dict_w_most_inliers['threed_center'] != [0,0,0] and final_dict['threed_center'] == [0,0,0]:
        final_dict['threed_center'] = dict_w_most_inliers['threed_center'];
        final_dict['threed_normal'] = dict_w_most_inliers['threed_normal'];
        final_dict['type'] = dict_w_most_inliers['type'];
      if dict_w_most_inliers['threed_top_left'] != [0,0,0] and final_dict['threed_top_left'] == [0,0,0]:
        final_dict['threed_top_left'] = dict_w_most_inliers['threed_top_left'];
      if dict_w_most_inliers['threed_top_right'] != [0,0,0] and final_dict['threed_top_right'] == [0,0,0]:
        final_dict['threed_top_right'] = dict_w_most_inliers['threed_top_right'];
      if final_dict['threed_center'] != [0,0,0] and final_dict['threed_top_left'] != [0,0,0] and final_dict['threed_top_right'] != [0,0,0]: #break as soon as this is done; faster
        break
      i += 1
    if final_dict['threed_center'] != [0,0,0]:
      final_list.append(final_dict)
  print final_list
  for idx, comp in enumerate(final_list):
    final_list[idx] = getAlignmentInfo(comp) #reassigning the value
  final_list = postProcComps(final_list)
  return final_list

def callCppIntermediate(tag_dictionary, args):
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
  callCpp(tag_dictionary, args) #modifies tag_dictionary w/ 3d


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
  print "DONE WITH C++ CALL!"

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
SCRATCH = os.path.join(os.getcwd(),'scratch.stl')
'''
We will give the following to this part of the pipeline:
  list of dictionaries of components with format above
  STL file of scanned object
We expect to receive the following from this part of the pipeline:
  1st time : model w/o intersecting components & w/ enough space for components
  2nd time : two files with subbed comps, bosses, and parting lines

'''

def callOpenSCAD(script, oname, otherargs='', allow_empty=False):
  call = [OPENSCAD, '-o', oname, script]
  if not otherargs == '':
    call = [OPENSCAD, '-o', oname, otherargs, script]
  # this will throw an exception if the call fails for some reason
  if allow_empty:
    proc = subprocess.Popen(' '.join(call),shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=True)
    line = proc.stdout.readline()
    if "Current top level object is empty." in line:
      return True
    if line == '':
      return False
    proc.terminate()
    raise Exception(' '.join(['call failed : ', ' '.join(call), ", message", line]))
  else:
    subprocess.check_call(call)
  return False

def createsEmptySTL(script, oname, otherargs=''):
  return callOpenSCAD(script, oname, otherargs, allow_empty=True)

def placeCompOpenSCAD(component, geom):
  output = '''
translate(%(coords)s) {
  rotate(%(rotations)s) {
    rotate(%(axis)s) {
      import("stls/'''+Component.toStr(component['type'])+'-'+geom+'''.stl");
    }
  }
}
'''
  return output % component

def placeBossOpenSCAD(boss, geom='add', topbot=''):
  boss['geom'] = geom
  boss['topbot'] = topbot
  text = '''
translate(%(coords)s) {
  rotate(%(rotations)s) {
    translate(%(offset)s) {
      import("stls/boss-%(geom)s%(topbot)s.stl");
    }
  }
}
''' % boss
  return text

def placePLineOpenSCAD(pline_comp):
  pline_comp['axis'] = 0
  [x,y,z] = list(pline_comp['rotations'])
  print x,y,z
  pline_comp['rotations'] = [x+90,y+90,z]
  return placeCompOpenSCAD(pline_comp, geom='woo')

def internalOnly(geometry, body):
  return '''
intersection() {
  '''+geometry+'\n'+'''
  import("'''+body+'''");
}
'''

def writeOpenSCAD(script, components={}, object_body='', deflated='',
                  full_body='', top='', boss=None, bosses=[], topbot='',
                  debug=False):
  text = 'union() {\n'

  if script == DEFORM_SHELL_SCRIPT:
    text += '''
  difference() {
    import("%(obj_body)s");
    %(solid_bb_clearance)s
  }
    ''' % {
    'obj_body':object_body,
    'solid_bb_clearance':placeCompOpenSCAD(components, geom='bbsolid') #is components supposed to be a dictionary of a single comp?
  } #subtracts translated solid bounding box from body

    text += '''
    difference() {
     %(shelled_bb)s
      import("%(solid_obj_body)s");
       }
    ''' % {
    'shelled_bb':placeCompOpenSCAD(components, geom='bbshell'),
    'solid_obj_body':full_body
  } #subtracts solid body from hollow bounding box


  if script == CHECK_INTERSECT_SCRIPT and object_body == '':
    text += '''
intersection() {
  %(comp_0)s
  %(comp_1)s
}
''' % {
    'comp_0':placeCompOpenSCAD(components[0], geom='clearance'),
    'comp_1':placeCompOpenSCAD(components[1], geom='clearance'),
  }
  if script == CHECK_INTERSECT_SCRIPT and not object_body == '':
    text += '''
intersection() {
  %(comp_0)s
  import("%(obj)s");
}
''' % {
    'comp_0':placeCompOpenSCAD(components[0], geom='clearance'),
    'obj':object_body,
  }

  if script == SUB_COMPONENT_SCRIPT:
    comps_sub = ''
    comps_add = ''
    for component in components:
      if component['type'] == Component.parting_line:
        # these will be dealt with in a special step later
        continue
      comps_sub += placeCompOpenSCAD(component, geom='sub')
      if Component.no_trim(component['type']):
        comps_add += placeCompOpenSCAD(component, geom='add')
      else:
        comps_add += internalOnly(placeCompOpenSCAD(component, geom='add'),
                                  full_body)
    text += '''
difference() {
\timport("%(obj)s");
// first we need to subtract everything
\t%(comps_sub)s
}
// now we add mounting points back in (they are cut to size of the body)
%(comps_add)s
''' % {
    'obj':object_body,
    'comps_sub':comps_sub,
    'comps_add':comps_add,
  }

  if script == PART_SCRIPT:
    pline = 'cube(1);'
    for comp in components:
      if comp['type'] is Component.parting_line_calculated:
        pline = placePLineOpenSCAD(comp)
        break
    if pline == '':
      print 'wtf? no parting line?'
    if top == True:
      text += '''
difference(){
\timport("%(obj)s");
\t%(pline)s
}
''' % {
    'obj':object_body,
    'pline':pline,
    }
    if top == False:
      text += '''
intersection(){
\timport("%(obj)s");
\t%(pline)s
}
''' % {
    'obj':object_body,
    'pline':pline,
    }

  if script == BOSS_CHECK_COMPS_SCRIPT:
    all_comp_union = 'union(){'
    for comp in components:
      placecomp = placeCompOpenSCAD(comp, geom='clearance')
      all_comp_union += (placecomp)
    all_comp_union += '}'
    text += '''
intersection() {
\t%(boss)s
\t%(comps)s
}
''' % {
      'boss':placeBossOpenSCAD(boss,'add'),
      'comps':all_comp_union,
    }

  if script == BOSS_PUT_SCRIPT:
    bosses_add = ''
    bosses_sub = ''
    for boss in bosses:
      bosses_add += placeBossOpenSCAD(boss,'add',topbot)
      bosses_sub += placeBossOpenSCAD(boss,'sub',topbot)
    text += '''
difference() {
  // add together bosses and hollowed body
  union() {
    // make sure we only take boss parts inside the body
    intersection() {
      union() {
        %(bosses_add)s
      }
      import("%(full)s");
    }
    // ok, here is the hollowed body
    import("%(obj)s");
  }

  // now here is the part we subtract: all the boss middles
  union() {
    %(bosses_sub)s
  }
}
''' % {
      'bosses_add':bosses_add,
      'bosses_sub':bosses_sub,
      'full':full_body,
      'obj':object_body,
    }

  if script == SHELL_SCRIPT:
    text += '''
difference() {
  import("%(obj)s");
  import("%(deflated)s");
}
''' % {
      'obj':object_body,
      'deflated':deflated
    }

  if script == MINKOWSKI_TOP or script == MINKOWSKI_BOT:
    for comp in components:
      if comp['type'] is Component.parting_line_calculated:
        parting_line = comp
        break
    topbot = 'top'
    diffint = 'difference'
    orig = '''
        linear_extrude(height = 4) { // so we translate -2 and extrude 4
            difference() { // we are just going to take the area between the two profiles
                offset(r=-2.25) { // we can offset from the full body part by -2.25 and -3.
                    projection(cut=true) {
                        position_original();
                    }
                }
                offset(r=-3.25) {
                    projection(cut=true) {
                        position_original();
                    }
                }
            }
        }
'''
    if script != MINKOWSKI_TOP:
      topbot = 'bot'
      diffint = 'intersection'
      orig = '''
        linear_extrude(height = 4) { // just need a little lip on the bottom piece
            difference() { // we are just going to take the area between the two profiles
                projection(cut=true) {
                    position_original();
                }
                offset(r=-2) {
                    projection(cut=true) {
                        position_original();
                    }
                }
            }
        }
'''
    text = '''
module position_original() {
    rotate([-90,0,0]) { // need this
      rotate(%(axis)s) { // negate these, too
        rotate(%(z_rotation)s) { // negate and do Z first
          rotate(%(xy_rotation)s) { // negate and do Z first
            translate(%(translation)s) { // negate numbers
                import("%(full_body)s");
            }
        }
      }
    }
}

module position_%(topbot)s() {
    rotate([-90,0,0]) { // need this
      rotate(%(axis)s) { // negate these, too
        rotate(%(z_rotation)s) { // negate and do Z first
          rotate(%(xy_rotation)s) { // negate and do Z first
            translate(%(translation)s) { // negate numbers
                import("%(object_body)s");
            }
        }
      }
    }
}

module xy_cutbox() {
    translate([-1000,-1000,0]) {
        cube(2000);
    }
}

union() {
    translate([0,0,1]) { // move back into place after cut happens
        %(diffint)s() { // we need to cut off a bit of the base model to make this work
            translate([0,0,-1]) {
                position_%(topbot)s();
            }
            xy_cutbox();
        }
    }
    translate([0,0,-2]) {// we want to go down 2 and up 2
        %(orig)s
    }
    ''' % {
      'topbot' : topbot,
      'diffint' : diffint,
      'translation' : str([-t for t in parting_line['coords']]),
      'z_rotation' : str([0,0,-parting_line['rotations'][-1]]),
      'xy_rotation' : str([0,-parting_line['rotations'][1],0]),
      'axis' : str([-r for r in parting_line['axis']]),
      'orig' : orig,
      'object_body' : object_body,
      'full_body' : full_body,
    }

  text += '\n} // close union'
  if debug:
    print text
  else:
    #print 'writing this: ', text, '\n for this: ', script
    f = open(script, 'w+')
    f.write(text)
    f.close()

def isEmptySTL(fname=SCRATCH):
  with open(fname) as f:
    for line in f:
      if 'vertex' in line:
        return False
  return True

def shell(stl, deflated):
  oname = stl.replace('.stl','-shelled.stl')
  writeOpenSCAD(SHELL_SCRIPT, object_body=stl, deflated=deflated)
  callOpenSCAD(SHELL_SCRIPT, oname)
  return oname

def determineFitOffset(components, full, shelled):
  # figure out how far back we need to set each component to make it
  # not intersect the body of the object.
  for comp in components:
    if comp['type'] in Component.no_offset():
      continue
    loc = comp['coords']
    normal = comp['threed_normal']
    ct = 0
    print 'original:', loc
    while True:
      mod_comp = dict(comp)
      mod_comp['coords'] = [c_i - n_i for c_i, n_i in zip(loc, normal)]
      writeOpenSCAD(CHECK_INTERSECT_SCRIPT, [mod_comp], object_body=shelled)
      empty = createsEmptySTL(CHECK_INTERSECT_SCRIPT, SCRATCH)
      ct += 1
      if empty:
        break
      if ct > Component.max_offset(mod_comp['type']):
        raise Exception(''.join(["can't fit component",str(mod_comp),"into body"]))
      loc = mod_comp['coords']
    comp['coords'] = loc
    comp['offset'] = ct # note that this is in units of mm
    print 'new:', loc
  return components

def deformShell(components, full, shelled):
  oname = shelled
  print 'your components intersect. now deforming shell...'
  warn_user = False
  # figure out how far FORWARD we need to set each component to make it
  # not intersect with each other.
  no_skipped_comps = 0
  for comp in components:
    curr_type = comp['type']
    print "CURR COMP IS ", curr_type
    if comp['type'] in Component.no_moving():
      no_skipped_comps += 1
      continue
    if no_skipped_comps == len(components):
      warn_user = True
      print 'we skipped all the components!'
      break
    loc = comp['coords']
    normal = comp['threed_normal']
    ct = 0
    while True:
      mod_comp = dict(comp)
      mod_comp['coords'] = [c_i + n_i for c_i, n_i in zip(loc, normal)]
      print "new coords checking is ", mod_comp['coords']
      print "currently we are on ", curr_type
      mod_comp_list = [comp for comp in components if not (curr_type == comp.get('type'))]
      #create a new list w/ the modified coordinates
      mod_comp_list.append(mod_comp)
      print "checking intersections!"
      if not checkIntersections(mod_comp_list): #if there are no intersections
        print "sweet, no intersections"
        break
      if ct > 30:
        warn_user = True
        break
      loc = mod_comp['coords']
      ct += 1
    comp['coords'] = loc
    print 'new:', loc, ' for ', comp['type']
    if warn_user:
      raise Exception("Components intersect beyond an aesthetically pleasing fix. Try a redesign?")

    #just for the mainboard
    for comp in components:
      #add more objects here
      if comp['type'] == Component.main_board:
        print 'adding a bounding box to the main board...'
        writeOpenSCAD(DEFORM_SHELL_SCRIPT, comp, object_body=shelled, full_body=full)
        oname = shelled.replace('.stl','-deformed.stl')
        callOpenSCAD(DEFORM_SHELL_SCRIPT, oname)
        print 'done!'
        return oname
  return oname


def checkIntersections(components):
  # check if any component intersects any other component
  for c1 in components:
    for c2 in components:
      if c1 == c2 or c1['type'] is Component.parting_line or c2['type'] is Component.parting_line or c1['type'] is Component.parting_line_calculated or c2['type'] is Component.parting_line_calculated:
        continue
      writeOpenSCAD(CHECK_INTERSECT_SCRIPT, [c1,c2])
      empty = createsEmptySTL(CHECK_INTERSECT_SCRIPT, SCRATCH)
      if not empty:
        print('%(c1)s (%(c1l)s) and %(c2)s (%(c2l)s) intersect!' %
                          {
                            'c1':c1['type'],
                            'c1l':str(c1['coords']),
                            'c2':c2['type'],
                            'c2l':str(c2['coords']),
                            }
                       )
        return True
  return False

def substitute_components(components, stl, full):
  writeOpenSCAD(SUB_COMPONENT_SCRIPT, components, object_body=stl, full_body=full)
  oname = stl.replace('.stl','-compsubbed.stl')
  callOpenSCAD(SUB_COMPONENT_SCRIPT, oname)
  return oname

import math
def calc_bosses(components):
  # some things that will be important:
  boss_rotations = []
  boss_base = []
  for component in components:
    if Component.part(component['type']):
      boss_rotations = list(component['rotations'])
      boss_base = list(component['coords'])
      break
  if len(boss_rotations) == 0:
    # no parting line => no bosses
    return stl
  # first order of business, which bosses are good?
  good_bosses = []
  grid_spacing = 30
  min_coords = -150
  max_coords = -min_coords
  field_x = range(min_coords,max_coords,grid_spacing)
  field_z = range(min_coords,max_coords,grid_spacing)
  for x in field_x:
    for z in field_z:
      potential_boss = {
        'type':Component.boss,
        'coords':boss_base,
        'axis':0,
        'rotations':boss_rotations,
        'offset':[x,0,z],
      }
      writeOpenSCAD(BOSS_CHECK_COMPS_SCRIPT, components, boss=potential_boss)
      empty = createsEmptySTL(BOSS_CHECK_COMPS_SCRIPT, SCRATCH)
      if empty:
        good_bosses.append(potential_boss)
  return good_bosses

def boss_addin(stl, full, topbot, bosses):
  bossed_stl = stl.replace('.stl','-bossed.stl')
  writeOpenSCAD(BOSS_PUT_SCRIPT,topbot=topbot,bosses=bosses,object_body=stl,full_body=full)
  callOpenSCAD(BOSS_PUT_SCRIPT,bossed_stl)
  return bossed_stl

def partingLine(components, stl):
  o_top = stl.replace('.stl', '-top.stl')
  o_bot = stl.replace('.stl', '-bot.stl')
  writeOpenSCAD(PART_SCRIPT, components, object_body=stl, top=True)
  callOpenSCAD(PART_SCRIPT, o_top)
  writeOpenSCAD(PART_SCRIPT, components, object_body=stl, top=False)
  callOpenSCAD(PART_SCRIPT, o_bot)
  return (o_top,o_bot)

def add_lip(components, side1, side2, full):
  o_top = side1.replace('.stl', '-minkowski.stl')
  o_bot = side2.replace('.stl', '-minkowski.stl')
  writeOpenSCAD(MINKOWSKI_TOP, components, object_body=side1, full_body=full)
  callOpenSCAD(MINKOWSKI_TOP, o_top)
  writeOpenSCAD(MINKOWSKI_TOP, components, object_body=side2, full_body=full)
  callOpenSCAD(MINKOWSKI_TOP, o_bot)
  return (o_top, o_bot)

''' main function '''

def main(obj, do_boss, do_lip):
  #lol string -> bool
  bosses = False
  lips = False
  if do_boss == "True":
    bosses = True
  if do_lip == "True":
    lips = True

  print obj
  stl = 'obj/'+obj.replace('.obj','.stl')
  full = stl
  print "bossses? ", bosses, "lip? ", lips
  components = identifyComponents(obj)
  #this was the data for the original controller.
  # components = [{'threed_top_left': [30.5812, -129.655, 59.6193], 
  #               'rotations': [0.0, 12.0416, 96.79], 'threed_center': 
  #               [22.3764, -140.621, 64.1149], 'coords': [26.024393000000007, 
  #               -145.36394799999997, 58.24692400000002], 'threed_normal': 
  #               [-0.0246655, 0.207158, 0.977996], 'axis': [0, 0, -95.692], 
  #               'type':  Component.button, 'threed_top_right': [48.4134, 
  #               -129.319, 59.1823]}, {'threed_top_left': [0.119901, -131.238, 
  #               57.4489], 'rotations': [0.0, 4.0543, 133.4089], 'threed_center': 
  #               [7.1497, -141.453, 63.4532], 'coords': [0.299243000000001,
  #                -146.69679799999994, 56.87762399999999], 'threed_normal':
  #                [-0.235649, 0.249114, 0.939368], 'axis': [0, 0, -129.9031],
  #                'type':  Component.button, 'threed_top_right': [28.8909,
  #                 -129.633, 59.8662]}, {'threed_top_left': [0, 0, 0], 'rotations':
  #                  [0.0, 5.3241, 107.9094], 'threed_center': [-37.2577, -172.617,
  #                   69.1782], 'coords': [-37.44382930000003, -174.08821859999986,
  #                    58.22565399999998], 'threed_normal': [-0.0285337, 0.0882926,
  #                    0.995686], 'axis': [0, 0, 152.8863], 'type':
  #                     Component.joystick, 'threed_top_right':
  #                    [-19.0821, -155.235, 66.3307]}, {'threed_top_left':
  #                    [45.1078, -155.669, 66.055], 'rotations': [0.0, 5.1047, 98.3725],
  #                    'threed_center': [62.5238, -173.009, 67.3152], 'coords':
  #                    [62.16631159999998, -174.4773002999999, 56.35882600000001],
  #                    'threed_normal': [-0.0129556, 0.0880273, 0.996034], 'axis':
  #                    [0, 0, -96.4875], 'type':  Component.joystick,
  #                    'threed_top_right': [73.0373, -154.752, 65.5618]},
  #                    {'threed_top_left': [54.8185, -129.418, 37.9397], 'rotations':
  #                    [0.0, 175.6475, -110.8791], 'threed_center': [24.2125, -157.541,
  #                    31.2391], 'coords': [24.2125, -157.541,
  #                    31.2391], 'threed_normal': [-0.0270477, -0.0709084,
  #                     -0.997116], 'axis': [0, 0, -20.4817], 'type':
  #                      Component.main_board, 'threed_top_right': [-5.38373,
  #                     -131.955, 30.474]}, {'axis': -19.4488, 'coords': [15.7206, -185.0390,
  #                     48.3318], 'rotations': [0, 85.5722, -166.7193], 'type':
  #                      Component.parting_line_calculated}]

  print 'your components are originally at'
  print components
  stl = stl.replace('.stl','-shelled.stl')#shell(stl, deflated)
  shelled = stl
  print 'determining fit offsets...'
  components = determineFitOffset(components, full, shelled)
  print 'after determining fit offsets, your components are at'
  print components
  print 'checking intersections'
  need_to_deform = checkIntersections(components)
  if need_to_deform:
    print "shelling"
    shelled = deformShell(components, full, shelled)
  if bosses:
    bosses = calc_bosses(components)
  stl = substitute_components(components, shelled, full)
  side1, side2 = partingLine(components, stl)
  if bosses:
    side1 = boss_addin(side1,full,'top',bosses)
    side2 = boss_addin(side2,full,'bot',bosses)
  if lips:
    side1, side2 = add_lip(components, side1, side2, full)

if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2], sys.argv[3])
