#!/bin/bash -xe

# The serctions used in this example are downloaded from the
# BrainMaps.org website
# 
# http://brainmaps.org/index.php?action=viewslides&datid=54
#
# Mikula, S., Trotts, I., Stone, J. M., & Jones, E. G. (2007).
# Internet-enabled high-resolution brain mapping and virtual microscopy.
# NeuroImage, 35(1), 9–15. doi:10.1016/j.neuroimage.2006.11.053
# 
# If you want to redownload the section, please uncomment the lines below 
# 
# wget -i list_of_axial_sections_to_download 
# mogrify -r resize 25% *.jpg
# zip exmaple_axial_cuts.zip *.jpg

rm -rf *.jpg
unzip exmaple_axial_cuts.zip
pos_stack_sections \
    -i %04d.jpg \
    -o stacked_axial_exmaple.nii.gz \
    --stacking-range 1020 1300 5 \
    --permutation 0 1 2 \
    --orientation RAS \
    --origin 0 0 0 \
    --flip 0 1 0 \
    --spacing 1.0 1.0 3.5 \
    --type uchar \
    --loglevel DEBUG 
rm -rf *.jpg

