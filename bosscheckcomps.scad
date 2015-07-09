union() {

intersection() {
	
translate([15.7206, -185.039, 48.3318]) {
  rotate([0, 85.5722, -166.7193]) {
    translate([-150, 0, -150]) {
      import("stls/boss-add.stl");
    }
  }
}

	union(){
translate([26.024393000000007, -145.36394799999997, 58.24692400000002]) {
  rotate([0.0, 12.0416, 96.79]) {
    rotate([0, 0, -95.692]) {
      import("stls/button-clearance.stl");
    }
  }
}

translate([0.299243000000001, -146.69679799999994, 56.87762399999999]) {
  rotate([0.0, 4.0543, 133.4089]) {
    rotate([0, 0, -129.9031]) {
      import("stls/button-clearance.stl");
    }
  }
}

translate([-37.44382930000003, -174.08821859999986, 58.22565399999998]) {
  rotate([0.0, 5.3241, 107.9094]) {
    rotate([0, 0, 152.8863]) {
      import("stls/joystick-clearance.stl");
    }
  }
}

translate([62.16631159999998, -174.4773002999999, 56.35882600000001]) {
  rotate([0.0, 5.1047, 98.3725]) {
    rotate([0, 0, -96.4875]) {
      import("stls/joystick-clearance.stl");
    }
  }
}

translate([15.847738500000004, -158.68645799999996, -5.224679999999996]) {
  rotate([0.0, 175.6475, -110.8791]) {
    rotate([0, 0, -20.4817]) {
      import("stls/main_board-clearance.stl");
    }
  }
}

translate([15.7206, -185.039, 48.3318]) {
  rotate([0, 85.5722, -166.7193]) {
    rotate(-19.4488) {
      import("stls/parting_line_calculated-clearance.stl");
    }
  }
}
}
}

} // close union