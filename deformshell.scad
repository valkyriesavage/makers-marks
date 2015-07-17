union() {

  difference() {
    import("obj/goodcontroller-shelled.stl");
    
translate([24.2395477, -157.4700916, 32.236216]) {
  rotate([0.0, 175.6475, -110.8791]) {
    rotate([0, 0, -20.4817])rotate([180,0,0])translate([0,0,7.5]) {
      import("stls/main_board-clearance.stl");
    }
  }
}

  }
    
    difference() {
     
translate([24.2395477, -157.4700916, 32.236216]) {
  rotate([0.0, 175.6475, -110.8791]) {
    rotate([0, 0, -20.4817])rotate([180,0,0])translate([0,0,7.5]) {
      import("/Users/noon/Desktop/procrustes/actual_hollow.stl");
    }
  }
}

      import("obj/goodcontroller.stl");
       }
    
} // close union