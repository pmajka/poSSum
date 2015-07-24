#!/bin/bash -xe

# The serctions used in this example are downloaded from the
# BrainMaps.org website
# 
# http://brainmaps.org/index.php?action=viewslides&datid=141
# 

# Mikula, S., Trotts, I., Stone, J. M., & Jones, E. G. (2007).
# Internet-enabled high-resolution brain mapping and virtual microscopy.
# NeuroImage, 35(1), 9–15. doi:10.1016/j.neuroimage.2006.11.053
# 
# If you want to redownload the section, please uncomment the lines below 
# 
# bash -xe download_coronal_sections.sh
# 
# i=0; 
# for f in `ls -1 *.jpg`;
# do 
#     mv $f `printf %04d.jpg $i`;
#     i=$[i+1];
# done
# 
# zip example_coronal_sections.zip *.jpg
# rm -rf *.jpg

rm -rf *.jpg
unzip example_coronal_sections.zip
pos_stack_sections \
    -i %04d.jpg \
    -o stacked_coronal_exmaple.nii.gz \
    --stacking-range 0 106 1 \
    --permutation 0 2 1 \
    --orientation RAS \
    --origin 0 0 0 \
    --flip 0 1 0 \
    --spacing 0.15 0.3 0.15 \
    --interpolation linear \
    --type uchar \
    --loglevel DEBUG 

pos_stack_sections \
    -i %04d.jpg \
    -o stacked_coronal_exmaple_downsampled.nii.gz \
    --stacking-range 0 106 1 \
    --permutation 0 2 1 \
    --orientation RAS \
    --origin 0 0 0 \
    --flip 0 1 0 \
    --resample 0.5 0.5 0.5 \
    --spacing 0.3 0.6 0.3 \
    --interpolation linear \
    --type uchar \
    --loglevel DEBUG 
rm -rf *.jpg
