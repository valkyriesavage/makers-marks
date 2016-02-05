import sys
from matlab import identifyComponents
from openscad import determineFitOffset, checkIntersections, deformShell, calcBosses, \
    substituteComponents, createButtonCaps, partingLine, addBosses

def usage():
  print '''
usage:

python process.py object.obj boss_q lip_q

this script currently expects object.obj to be located in a subdirectory of the same folder
called "obj/".
boss_q and lip_q are "true" or "false" and specify if the object is to have bosses or
lips generated.
  '''

def main(obj, do_boss, do_lip):
  try:
    #lol string -> bool
    bosses = False
    lips = False
    bosses = (do_boss == 'True' or do_boss == 'true')
    lips = (do_lip == 'True' or do_boss == 'true')
  except:
    usage()
    exit(1)

  stl = 'obj/'+obj.replace('.obj','.stl')
  full = stl

  components = identifyComponents(obj)

  #print 'your components are originally at'
  #print components
  stl = stl.replace('.stl','-shelled.stl')#shell(stl, deflated)
  shelled = stl
  #print 'determining fit offsets...'
  components = determineFitOffset(components, full, shelled)
  #print 'after determining fit offsets, your components are at'
  #print components
  #print 'checking intersections'
  need_to_deform = checkIntersections(components)
  if need_to_deform:
    #print "shelling"
    shelled = deformShell(components, full, shelled)
  if bosses:
    bosses = calcBosses(components)
  #print 'RUNNING SUB COMP'
  stl = substituteComponents(components, shelled, full)
  #print 'creating button caps'
  createButtonCaps(components)
  #print 'NOW RUNNING PARTING LINE'
  side1, side2 = partingLine(components, stl)
  if bosses:
    side1 = addBosses(side1,full,'top',bosses)
    side2 = addBosses(side2,full,'bot',bosses)
  #print 'NOW RUNNING LIP!'
  if lips:
    side1, side2 = addLip(components, side1, side2, full)

if __name__ == '__main__':
  if len(sys.argv) < 2 or sys.argv[1] in ['-h','--help']:
    usage()
    exit(0)
  main(sys.argv[1], sys.argv[2], sys.argv[3])
