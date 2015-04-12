% ***********
% Iterates through .jpg tags in /tags folder and texture .jpgs associated
% with the .obj in the /obj folder, writes to sift.txt which is formatted
% tag tag_filename.jpg
% filename matching_texture_image.jpg 
% left [lu,lv]
% center [cu,cv]
% right [ru,rv]
%
% Does this via SIFT and RANSAC.
% Needs no arguments, just have the files in the right folders.
% ***********
addpath('obj/');
addpath('tags/');
fnames = strsplit(ls('obj/'));
snames = strsplit(ls('tags/'));
%create the output file
fileID = fopen('sift.txt', 'w+');
%iterate through stickers
for sname = snames
    str = sname{1};
    if strcmp(str, '')
        continue;
    end
    ext = strsplit(str, '.');
    if strcmp(ext(2),'jpg')
        prev_inliers = 0;
        curr_inliers = 0;
        for fname = fnames %iterate through jpg textures
            fstr = fname{1};
            if strcmp(fstr, '')
                continue;
            end
            fext = strsplit(fstr, '.');
            if strcmp(fext(2),'jpg')
                [t_filename, t_lu, t_lv, t_cu, t_cv, t_ru, t_rv, inliers] = tag_detection(str, fstr);
                curr_inliers = inliers;
                if curr_inliers > 10 %remember all data stronger than 10
                    filename = t_filename;
    %{
                    lu = t_lu;
                    lv = t_lv;
                    cu = t_cu;
                    cv = t_cv;
                    ru = t_ru;
                    rv = t_rv;
%}
                    fprintf(fileID, 'sticker %s\n', str);
                    fprintf(fileID, 'filename %s\n', t_filename);
                    fprintf(fileID, 'inliers %f\n', curr_inliers);                   
                    fprintf(fileID, 'left [%f,%f]\n', t_lu, t_lv);
                    fprintf(fileID, 'center [%f,%f]\n', t_cu, t_cv);
                    fprintf(fileID, 'right [%f,%f]\n', t_ru, t_rv); 
                    prev_inliers = curr_inliers;
                end
            end
        end 
        if prev_inliers == 0
            %the sticker doesn't exist anywhere in the obj
            continue;
        end
    end
end

fclose(fileID);