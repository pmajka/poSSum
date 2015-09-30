#!/bin/bash -xe

# The serctions used in this example are downloaded from the
# BrainMaps.org website
# 
#  http://brainmaps.org/index.php?action=viewslides&datid=6&start=1

# Mikula, S., Trotts, I., Stone, J. M., & Jones, E. G. (2007).
# Internet-enabled high-resolution brain mapping and virtual microscopy.
# NeuroImage, 35(1), 9–15. doi:10.1016/j.neuroimage.2006.11.053
# 
# If you want to redownload the section, please uncomment the lines below 
# 
#
# wget -i list_of_sagittal_sections_to_download
# mogrify -resize 25% *.jpg

# i=0; 
# for f in `ls -1 *.jpg`;
# do 
#     mv $f `printf %04d.jpg $i`;
#     i=$[i+1];
# done

# zip example_sagittal_sections.zip *.jpg

rm -rf *.jpg
unzip example_sagittal_sections.zip
pos_stack_sections \
    -i %04d.jpg \
    -o stacked_sagittal_exmaple.nii.gz \
    --stacking-range 0 55 1 \
    --permutation 2 0 1 \
    --orientation RAS \
    --origin 0 0 0 \
    --flip 0 1 0 \
    --spacing 0.25 0.05 0.05 \
    --type uchar \
    --loglevel DEBUG 
rm -rf *.jpg

