import os, subprocess

''' Matlab location and scripts '''
MATLAB = '/Applications/MATLAB_R2014a.app/Contents/MacOSX/MATLAB_maci64'
SIFT_DETECT_SCRIPT = 'siftdetect.m'
SIFT_OUTPUT = 'sift.txt'

def callMatlab(script):
  call = [MATLAB, '-nodesktop', '-nodisplay', '-nosplash', '-nojvm',
          '-r', script]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

def extractComponentInfo(location=SIFT_OUTPUT):
  with open(SIFT_OUTPUT) as f:
    for line in f:
      print line

def identifyComponents():
  callMatlab(SIFT_DETECT_SCRIPT)
  return extractComponentInfo(SIFT_OUTPUT)

''' OpenSCAD location and scripts '''
OPENSCAD = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
CHECK_SIZE_SCRIPT = os.path.join(os.getcwd(), 'checksize.scad')
CHECK_INTERSECT_SCRIPT = os.path.join(os.getcwd(), 'checkintersect.scad')
PART_AND_BOSS_SCRIPT = os.path.join(os.getcwd(), 'partboss.scad')
SCRATCH = os.path.join(os.getcwd(),'scratch.stl')

def callOpenSCAD(script, oname, otherargs=''):
  call = [OPENSCAD, '-o', oname, otherargs, script]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)

def writeOpenSCAD(script, components, body='', debug=False):
  text = ''
  if script is CHECK_SIZE_SCRIPT:
    comps = ''
    for component in components:
      comps += '\timport("%(fileloc)s");\n' % component
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
  translate(%(coords_0)s) {
    rotate(%(rot_0)s) {
      import("%(comp_0)s");
    }
  }
  translate(%(coords_1)s) {
    roate(%(rot_0)s) {
      import("%(comp_1)s");
    }
  }
}
''' % {
    'coords_0':str(components[0]['coords']),
    'comp_0':components[0]['fileloc'],
    'rot_0':components[0]['rotation'],
    'coords_1':str(components[1]['coords']),
    'comp_1':components[1]['fileloc'],
    'rot_1':components[1]['rotation'],
  }
  if script is PART_AND_BOSS_SCRIPT:
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
                            'c1':c1['fileloc'],
                            'c1l':string(c1['coords']),
                            'c2':c2['fileloc'],
                            'c2l':string(c2['coords']),
                            }
                       )

''' Meshlab location and scripts '''
MESHLAB = '/Applications/meshlab.app/Contents/MacOS/meshlabserver'
SHELL_SCRIPT = os.path.join(os.getcwd(), 'shell.meshlab')

def callMeshlab(fname, oname, script='', otherargs=''):
  call = [MESHLAB, '-i', fname, '-o', oname, '-s', script, otherargs]
  # this will throw an exception if the call fails for some reason
  subprocess.check_call(call)


''' main function '''

def main(body):
  #components = identifyComponents(body)
  #checkSize(components, body)
  #checkIntersections(components)
  #partAndBoss(components, body)
  #shellPart(body)

if __name__ == '__main__':
  main(sys.argv[1])
