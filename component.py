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
            cls.boss,cls.servo_mount,cls.hole,cls.camera]

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

