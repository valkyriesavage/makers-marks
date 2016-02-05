import os, subprocess
from component import Component
from config import OPENSCAD, OPENSCAD_OLD, CHECK_INTERSECT_SCRIPT, SUB_COMPONENT_SCRIPT, \
    PART_SCRIPT, BOSS_CHECK_COMPS_SCRIPT, BOSS_PUT_SCRIPT, SHELL_SCRIPT, DEFORM_SHELL_SCRIPT, \
    MINKOWSKI_TOP, MINKOWSKI_BOT, BUTTON_CAP_SCRIPT, SCRATCH

'''
We will give the following to this part of the pipeline:
  list of dictionaries of components with format above
  STL file of scanned object
We expect to receive the following from this part of the pipeline:
  1st time : model w/o intersecting components & w/ enough space for components
  2nd time : two files with subbed comps, bosses, and parting lines

'''

def callOpenSCAD(script, oname, otherargs='', allow_empty=False):
  '''
    This function calls an openSCAD script and writes its output STL to a file.
    If "allow_empty" is true, it permits an empty STL to be generated (and
    returns True if the output is empty. If the output is not empty, it
    returns False.
  '''
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
  '''
  This function generates openSCAD code for placing a component. This component
  must have associated translations and rotations. It places the component's
  particular geometry defined by geom (i.e., "add", "sub", "clearance").
  '''
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

def placeBoundingBoxOpenSCAD(component, geom):
  '''
  This creates openSCAD code to add space for some components, defined by
  their bounding box. That is, if a component doesn't quite fit, we pop
  out some extra space for it.
  '''
  output = '''
translate(%(coords)s) {
  rotate(%(rotations)s) {
    rotate(%(axis)s)rotate([180,0,0])translate([0,0,7.5]) {
      import("stls/'''+Component.toStr(component['type'])+'-'+geom+'''.stl");
    }
  }
}
'''
  return output % component

def placeBossOpenSCAD(boss, geom='add', topbot=''):
  '''
  This places a single boss. It can place either the top or bottom part of it.
  '''
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
  '''
  This is a small wrapper for placeCompOpenSCAD which returns openSCAD code for
  correctly orienting a parting line.
  '''
  pline_comp['axis'] = 0
  [x,y,z] = list(pline_comp['rotations'])
  print x,y,z
  pline_comp['rotations'] = [x+90,y+90,z]
  return placeCompOpenSCAD(pline_comp, geom='woo')

def internalOnly(geometry, body):
  '''
  This returns openSCAD code that will add only the intersecting parts of
  geometry and body.
  '''
  return '''
intersection() {
  '''+geometry+'\n'+'''
  import("'''+body+'''");
}
'''
def internalOnlyBoundingBox(geometry, body, component): #need to intersect the solid bb as well
  '''
  This returns OpenSCAD code that will add only the intersection of a
  component's bounding box and a body geometry.
  '''
  return '''
intersection() {
  '''+geometry+'\n'+'''
  union() { import("'''+body+'''");
    '''+placeBoundingBoxOpenSCAD(component, geom='bbsolid')+placeBoundingBoxOpenSCAD(component, geom='bbshell')+'''
  }
}
'''

def writeOpenSCAD(script, components={}, object_body='', deflated='',
                  full_body='', top='', boss=None, bosses=[], topbot='',
                  debug=False):
  '''
  This horrifying function actually puts together the scripts necessary to do
  the openSCAD operations that Makers' Marks relies on. It can write scripts
  for deforming shells, checking intersections, and more, based on the
  script name passed in. It's bad, though.
  '''
  text = 'union() {\n'

  if script == DEFORM_SHELL_SCRIPT:
    text += '''
  difference() {
    import("%(obj_body)s");
    %(solid_bb_clearance)s
  }
    ''' % {
    'obj_body':object_body,
    'solid_bb_clearance':placeBoundingBoxSCAD(components, geom='bbsolid')
  } #subtracts translated solid bounding box from body

    text += '''
    difference() {
     rotate([180,0,0])translate([0,0,7.5])%(shelled_bb)s
      import("%(solid_obj_body)s");
       }
    ''' % {
    'shelled_bb':placeBoundingBoxSCAD(components, geom='bbshell'),
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
      if component['type'] == Component.parting_line or component['type'] == Component.parting_line_calculated:
        # these will be dealt with in a special step later
        continue
      comps_sub += placeCompOpenSCAD(component, geom='sub')
      if Component.no_trim(component['type']):
        comps_add += placeCompOpenSCAD(component, geom='add')
      elif component['type'] in pushed_comp:
        comps_add += internalOnlyBoundingBox(placeCompOpenSCAD(component, geom='add'),
                                  full_body, component)
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

  if script == BUTTON_CAP_SCRIPT:
    print "cutting button caps by ", components['offset']
    text += '''
difference() {
import("stls/button-cap.stl");
translate([0,0,-%(z)s])import("stls/button-cap-sub.stl");
}
''' % {
    'z':components['offset'],
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
  '''
  This function determines if an STL is empty. Note that with newer versions of
  openSCAD, empty STLs are not written, and instead a message is printed
  on the command line indicating that the STL would be empty.
  '''
  with open(fname) as f:
    for line in f:
      if 'vertex' in line:
        return False
  return True

def shell(stl, deflated):
  '''
  Given a full-size STL and a deflated STL, this function creates a shell.
  '''
  oname = stl.replace('.stl','-shelled.stl')
  writeOpenSCAD(SHELL_SCRIPT, object_body=stl, deflated=deflated)
  callOpenSCAD(SHELL_SCRIPT, oname)
  return oname

def determineFitOffset(components, full, shelled):
  '''
  This function will take a list of components and an object body,
  and will then determine how far components must be set back from the surface
  to prevent intersection with it.
  '''
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
    comp['offset'] = ct # note that this is in units of mm, for button caps
    print 'new:', loc
  return components

def deformShell(components, full, shelled):
  '''
  If certain types of components intersect each other (e.g., non-input
  components like processing boards), we can deform an object's shell
  to make space for them. This function pushes the objects out along
  their normals and creates a bounding box addition.
  '''
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
        global pushed_comp
        pushed_comp.append(comp['type'])
        print 'adding a bounding box to the main board...'
        writeOpenSCAD(DEFORM_SHELL_SCRIPT, comp, object_body=shelled, full_body=full)
        oname = shelled.replace('.stl','-deformed.stl')
        callOpenSCAD(DEFORM_SHELL_SCRIPT, oname)
        print 'done!'
        return oname
  return oname


def checkIntersections(components):
  '''
  This function checks if any component intersects any other component. It also
  has a series of exceptions; if a parting line intersects a component, it's
  not a big deal.
  '''
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

def substituteComponents(components, stl, full):
  '''
  Once final component locations are calculated, this will add and remove the
  correct geometry for the final print.
  '''
  writeOpenSCAD(SUB_COMPONENT_SCRIPT, components, object_body=stl, full_body=full)
  oname = stl.replace('.stl','-compsubbed.stl')
  callOpenSCAD(SUB_COMPONENT_SCRIPT, oname)
  return oname

import math
def calcBosses(components):
  '''
  To generate bosses, we create a uniform field of bosses, then remove any that
  intersect with our components' bounding boxes. Finally, we'll prune to just
  the bosses that actually touch our object.
  '''
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

def addBosses(stl, full, topbot, bosses):
  '''
  This actually adds bosses in after they have been calculated, and puts
  appropriate geometry depending whether this is the top of the object or
  its bottom.
  '''
  bossed_stl = stl.replace('.stl','-bossed.stl')
  writeOpenSCAD(BOSS_PUT_SCRIPT,topbot=topbot,bosses=bosses,object_body=stl,full_body=full)
  callOpenSCAD(BOSS_PUT_SCRIPT,bossed_stl)
  return bossed_stl

def partingLine(components, stl):
  '''
  This adds a parting line to an object, and cuts it into a top STL
  and a bottom STL.
  '''
  o_top = stl.replace('.stl', '-top.stl')
  o_bot = stl.replace('.stl', '-bot.stl')
  writeOpenSCAD(PART_SCRIPT, components, object_body=stl, top=True)
  print 'calling top...'
  callOpenSCAD(PART_SCRIPT, o_top)
  writeOpenSCAD(PART_SCRIPT, components, object_body=stl, top=False)
  print 'calling bottom...'
  callOpenSCAD(PART_SCRIPT, o_bot)
  return (o_top,o_bot)

def addLip(components, side1, side2, full):
  '''
  This adds a lip to an object's parting line, using a Minkowski
  sum on the top and bottom slices.
  '''
  o_top = side1.replace('.stl', '-minkowski.stl')
  o_bot = side2.replace('.stl', '-minkowski.stl')
  writeOpenSCAD(MINKOWSKI_TOP, components, object_body=side1, full_body=full)
  callOpenSCAD(MINKOWSKI_TOP, o_top)
  writeOpenSCAD(MINKOWSKI_TOP, components, object_body=side2, full_body=full)
  callOpenSCAD(MINKOWSKI_TOP, o_bot)
  return (o_top, o_bot)

def createButtonCap(button, i):
  '''
  When buttons are pushed too far in, they are hard for a user to activate.
  This automatically generates caps that can be inserted post-print.
  '''
  writeOpenSCAD(BUTTON_CAP_SCRIPT, button)
  button_stl = 'button-cap-%s.stl' % i
  callOpenSCAD(BUTTON_CAP_SCRIPT, button_stl)

def createButtonCaps(components):
  for comp in components:
    #print "running BC"
    i = 1
    if (Component.button == comp.get('type')): #if there's a button
      #print "button %s detected!" % i
      createButtonCaps(comp, i) #pass the button
      i += 1
