
function [filename, lu, lv, cu, cv, ru, rv, inliers] = tag_detection(tagphoto, comparisonphoto) 
    % --------------------------------------------------------------------
    %      Create image pair
    % --------------------------------------------------------------------
    sphoto = imread(tagphoto);
    photo = imread(comparisonphoto);
    Ia = imread(fullfile('tags/', tagphoto)) ;
    Ib = imread(fullfile('obj/', comparisonphoto)) ;
    % Gets a picture of SIFT matching and data points.
    % --------------------------------------------------------------------
    %      Extract features and match
    % --------------------------------------------------------------------
    [fa,da] = vl_sift(im2single(rgb2gray(Ia)), 'PeakThresh', 0) ;
    [fb,db] = vl_sift(im2single(rgb2gray(Ib)), 'PeakThresh', 0) ;
    [matches, ~] = vl_ubcmatch(da,db); 
    [mx,my] = size(matches);
    coordinates_source = zeros(my,2);
    coordinates_photo = zeros(my,2);
    for i=1:my
        sj = matches(1,i);
        pj = matches(2,i);
        coordinates_source(i,:) = transpose(fa(1:2,sj));
        coordinates_photo(i,:) = transpose(fb(1:2,pj));
    end

    %coordinates is a Mx2 matrix of [x, y] column vectors which specify the px
    %locations of the sticker in the scanstudio photo

    [cx, cy] = size(coordinates_source);

    %RANSAC/Geom transform to find inliers
    try
        [fRANSAC, inliers] = estimateFundamentalMatrix(coordinates_source, coordinates_photo, 'Method', 'RANSAC', 'InlierPercentage', 99, 'Confidence', 99.99, 'DistanceThreshold', 0.05);
        [rotMat, ginliers, ~] = estimateGeometricTransform(coordinates_source, coordinates_photo, 'affine');
        no_inliers = size(inliers(inliers~=0),1);
        no_ginliers = size(ginliers, 1);
    catch ME
        %not enough features, sticker probably isn't in this image, set
        %everything to 0
            lu = 0;
            lv = 0;
            cu = 0;
            cv = 0;
            ru = 0;
            rv = 0;
            filename = comparisonphoto;
            inliers = 0;
            return;
    end

    total_inliers = (no_inliers + no_ginliers) ./ 2;

    %find points in u,v space
    [scy, scx, ~] = size(sphoto);
    hscx = scx/2;
    hscy = scy/2;
    [cx, cy] = transformPointsForward(rotMat,hscx,hscy);
    [lx, ly] = transformPointsForward(rotMat,0,0);
    [rx, ry] = transformPointsForward(rotMat,scx,0);
    if strcmp(tagphoto, 'm.jpg') %fix mainboard corners
        [lx, ly] = transformPointsForward(rotMat,0,scy);
        [rx, ry] = transformPointsForward(rotMat,0,0);  
    end
    [iy, ix, ~] = size(photo);
    
%filling in data
    lu = lx / ix;
    lv = 1 - ly / iy;
    cu = cx / ix;
    cv = 1 - cy / iy;
    ru = rx / ix;
    rv = 1 - ry / iy;
    filename = comparisonphoto;
    inliers = total_inliers;
    if lu > 1 %sometimes this happens because bad skew mapping of parting lines
        lu = 1;
    end
    if ru > 1
        ru = 1;
    end
    if cu > 1 %sometimes this happens because bad skew mapping of parting lines
        cu = 1;
    end
    if cv > 1
        cv = 1;
    end
    if lv > 1 
        lv = 1;
    end
    if rv > 1
        rv = 1;
    end
    if lu < 0
        lu = 0;
    end
    if ru < 0 %this should never happen...
        ru = 0;
    end
    if lv < 0
        lv = 0;
    end
    if rv < 0 
        rv = 0;
    end   
    if cu < 0
        cu = 0;
    end
    if cv < 0 
        cv = 0;
    end  
end