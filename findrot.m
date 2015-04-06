addpath('rot/');

% ok, we are being given two sets of things: one is a set of 2D points
% the other is a set of 3D points.  we need to figure out the rotation.

%% VARIABLES (except these never change... we need commandline vars)

sticker_top_left = [0,1,0];
sticker_top_right = [1,1,0];
sticker_center = [.5,.5,0];
sticker_normal = [0,0,1];

%% TRANSLATION

% translate the normal/z-axis into place
x_translate = threed_center(1)-sticker_center(1);
y_translate = threed_center(2)-sticker_center(2);
z_translate = threed_center(3)-sticker_center(3);
translation = [x_translate, y_translate, z_translate];

%% ROTATION TO ALIGN NORMALS

threed_norm_polar = [norm(threed_normal), ...
                     acos(threed_normal(3)/norm(threed_normal)), ...
                     atan2(threed_normal(2),threed_normal(1))];
r = threed_norm_polar(1);
theta = threed_norm_polar(2);
phi = threed_norm_polar(3);
x_rot = 0;
y_rot = radtodeg(theta);
z_rot = radtodeg(phi);

%% ROTATION TO ALIGN CORNERS

sticker_axis = sticker_top_right - sticker_top_left;
sticker_axis_polar = [norm(sticker_axis), ...
                      acos(sticker_axis(3)/norm(sticker_axis)), ...
                      atan2(sticker_axis(2), sticker_axis(1))];
threed_axis = (threed_top_right - threed_top_left)/norm(threed_top_right - threed_top_left);
unrotate = rotz(-z_rot)*roty(-y_rot)*rotx(-x_rot);
threed_axis_unrotated = (unrotate*threed_axis.').';
threed_axis_polar = [norm(threed_axis_unrotated), ...
                     acos(threed_axis_unrotated(3)/norm(threed_axis_unrotated)), ...
                     atan2(threed_axis_unrotated(2), threed_axis_unrotated(1))];

axis_rot = radtodeg(threed_axis_polar(3) - sticker_axis_polar(3));


%% OUTPUT

translation
rotation = [x_rot,y_rot,z_rot]
axis_rot

fileID = fopen('transform.txt','w+');
fprintf(fileID,'coords [%.4f,%.4f,%.4f]\n',translation);
fprintf(fileID,'rotations [%.4f,%.4f,%.4f]\n',rotation);
fprintf(fileID,'axis [%.4f,%.4f,%.4f]\n',rotation);
fclose(fileID);