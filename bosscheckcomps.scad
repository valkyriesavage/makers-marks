
intersection() {
	
translate([-0.3507422539074021, 1.0312389995239926, -67.1537]) {
  rotate([0.0, 258.7783, 78.0132]) {
    rotate(0) {
      import("stls/boss-add.stl");
    }
  }
}

	union(){
translate([-13.325, -132.072, -67.1537]) {
  rotate([0.0, 168.7783, 78.0132]) {
    rotate([0, 0, 175.2094]) {
      import("stls/parting_line-clearance.stl");
    }
  }
}

translate([-8.9818, -149.114, 119.442]) {
  rotate([0.0, 13.6733, 53.3026]) {
    rotate([0, 0, 142.3733]) {
      import("stls/parting_line-clearance.stl");
    }
  }
}
}
}
