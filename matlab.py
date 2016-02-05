import os, subprocess, sys
from config import MATLAB, SIFT_DETECT_SCRIPT, FIND_ROTATION_SCRIPT, \
                   TRANSFORM_OUTPUT, SIFT_OUTPUT

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
    'center': (u,v),
    'threed_center': (x,y,z),
    'threed_top_left': (x,y,z),
    'threed_top_right': (x,y,z),
    },
    ...
  ]
These dictionaries describe the details of each detected component
sticker.
'''

def callMatlab(script, variables={}):
  '''
    Invoke Matlab on the given script, and share with it any variables.
  '''
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
  '''
    After Matlab has determined the transforms for each component sticker,
    we extract that info from the file it outputs.
  '''
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
  '''
    After Matlab detects each component sticker, we need to extract the
    location and type of component from the file it writes.
  '''
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
  '''
    We use Matlab to calculate the 3D transform necessary to align a
    component STL with its appropriate location in an object.
  '''
  # in here we need threed_center, threed_top_right,
  # threed_top_left, and threed_normal
  callMatlab(FIND_ROTATION_SCRIPT, component)
  calculated = extractComponentInfo(location=TRANSFORM_OUTPUT)
  component.update(calculated)
  return component

def postProcComps(comps):
  '''
    Some components, like the parting line, require additional post processing.
    The parting line is averaged from two parting line stickers to get a more
    accurate placement. Anything that relies on access to multiple stickers
    can be processed here.
  '''
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
  '''
    Given an OBJ file, we need to identify the components in it.
    This function scans the OBJ's texture files for the registered components
    (that is, all components with an image file in the correct directory),
    and finds their STL coordinates from the OBJ's geometry. it will
    return a list of dictionaries that have information on how to translate and
    rotate a 3D component into the correct place on the STL.
  '''
  callMatlab(SIFT_DETECT_SCRIPT)
  comp_list = extractSIFTComponentInfo(SIFT_OUTPUT)
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
      getSTLCoordsFromImgCoords(dict_w_most_inliers, args)
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

def getSTLCoordsFromImgCoords(tag_dictionary, args):
  '''
    given a set of image coordinates (i.e., those detected by Matlab), check
    the OBJ's correspondences between image and STL coordinates, and infer
    the STL coordinates.
  '''
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
  '''
    invoke the C++ program that does the image to STL coordinate conversion
  '''
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

