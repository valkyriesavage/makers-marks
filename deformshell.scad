union() {

  difference() {
    import("obj/goodcontroller-shelled.stl");
    
translate([24.2395477, -157.4700916, 32.236216]) {
  rotate([0.0, 175.6475, -110.8791]) {
    rotate([0, 0, -20.4817]) {
      import("stls/main_board-bbsolid.stl");
    }
  }
}

  }
    
    difference() {
     
translate([24.2395477, -157.4700916, 32.236216]) {
  rotate([0.0, 175.6475, -110.8791]) {
    rotate([0, 0, -20.4817]) {
      import("stls/main_board-bbshell.stl");
    }
  }
}

      import("obj/goodcontroller.stl");
       }
    
} // close union