addpath('rot/');

% ok, we are being given two sets of things: one is a set of 2D points
% the other is a set of 3D points.  we need to figure out the rotation.

sticker_top_left = [0,0,0];
sticker_top_right = [1,0,0];
sticker_center = [.5,.5,0];
sticker_normal = [0,0,1];

threed_top_left = [0,0,1];
threed_top_right = [sqrt(2),sqrt(2),1];
threed_center = [.5,.5,1];
threed_normal = [0,0,2];

% translate the normal/z-axis into place
x_translate = threed_center(1)-sticker_center(1);
y_translate = threed_center(2)-sticker_center(2);
z_translate = threed_center(3)-sticker_center(3);
translation = [x_translate, y_translate, z_translate];

% find out what rotations around x and y actually make 'em align
% note that we have to work with a translated 3D normal... to make it
% appear to be a unit vector with the same origin as sticker_normal
r = vrrotvec(sticker_normal, (threed_normal - translation));
% note, rot_axis is right now in STICKER SPACE (not 3D space)
rot_axis = r(1:3);
rot_angle = r(4);

% rotate the x axes into place.
if (isequal(rot_axis, [0,0,0]) || isequal(rot_angle, 0))
    % this means we didn't have to rotate in X and Y.
    % just do Z in the next step.
    rotated_tr = sticker_top_right;
else
    % to rotate, we need to align the bases of the vectors
    % since rot_axis is in STICKER SPACE we just need to slide it over
    % from the center of the sticker to the upper right corner.
    rot_axis = rot_axis - sticker_center;
    rot_axis
    sticker_top_right
    rotated_tr = rotVecAroundArbAxis(sticker_top_right,rot_axis,rot_angle);
end

% now slide the x-axes to match

translated_tl = sticker_top_left + translation;
translated_tr = rotated_tr + translation;

% ok!  now we just have to figure out the rotation about z.
translated_sticker_vect = translated_tr-translated_tl;
threed_vect = threed_top_right-threed_top_left;
mags = norm(translated_sticker_vect)*norm(threed_vect);

z_rot = acos(dot(translated_sticker_vect, threed_vect)/mags);
% can use acosd if we want degrees instead of radians
z_rot

%exit();