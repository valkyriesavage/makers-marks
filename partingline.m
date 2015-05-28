%% we take as input

pl1_threed_center = [96.3136, -178.62, 52.7239];
pl1_threed_top_left = [87.089, -158.992, 47.3152];
pl1_threed_top_right = [-51.0498, -185.277, 68.7597],;
pl2_threed_center = [99.1276, -189.458, 55.9397];
pl2_threed_top_left = [87.089, -158.992, 47.3152];
pl2_threed_top_right = [-66.3344, -190.529, 47.8688],;

%% center of plane

center_of_centers = [16.2206, -184.5390,   48.3318]; %(pl1_threed_center + pl2_threed_center) / 2;

%% we need to find where the line actually is on each sticker

pl1_mdpt = (pl1_threed_top_right + pl1_threed_top_left)/2;
pl1_offset_to_center = pl1_mdpt - pl1_threed_center;
pl1_line_left = pl1_threed_top_left - pl1_offset_to_center;
pl1_line_right = pl1_threed_top_right - pl1_offset_to_center;
pl1_line_vect = pl1_line_right - pl1_line_left;
pl1_line_vect = pl1_line_vect/norm(pl1_line_vect);

pl2_mdpt = (pl2_threed_top_right + pl2_threed_top_left)/2;
pl2_offset_to_center = pl2_mdpt - pl2_threed_center;
pl2_line_left = pl2_threed_top_left - pl2_offset_to_center;
pl2_line_right = pl2_threed_top_right - pl2_offset_to_center;
pl2_line_vect = pl2_line_right - pl2_line_left;
pl2_line_vect = pl2_line_vect/norm(pl2_line_vect);

% note that we use - here instead of + since they are opposite directions
% (being on opposite sides of the object)
mdpt_vect = max((pl1_line_vect + pl2_line_vect),(pl1_line_vect - pl2_line_vect))/2;

%% so what define our plane here?

v1 = pl2_threed_center - pl1_threed_center;
v2 = mdpt_vect;

normal = cross(v1,v2);

% we'll leverage the work we already did:
threed_center = center_of_centers;
threed_normal = normal;
threed_top_right = center_of_centers + mdpt_vect;
threed_top_left = center_of_centers - mdpt_vect;
findrot

%% OUTPUT

% part_line_translate
% part_line_rotate = [x_rot,y_rot,z_rot]
% part_line_axis
% part_line_axis_rot
% 
% fileID = fopen('partingline.txt','w+');
% fprintf(fileID,'coords [%.4f,%.4f,%.4f]\n',part_line_translate);
% fprintf(fileID,'rotations [%.4f,%.4f,%.4f]\n',part_line_rotate);
% fprintf(fileID,'axis [%.4f,%.4f,%.4f]\n',part_line_axis);
% fprintf(fileID,'axisrot %.4f',part_line_axis_rot);
% fclose(fileID);