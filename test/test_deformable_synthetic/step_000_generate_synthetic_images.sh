slice_width=256
slice_height=256
max_deform_in_vox=3

python step_000_generate_synthetic_images.py

for i in `seq 0 1 99`
do
    ii=`printf %04d $i`

    convert -size ${slice_width}x${slice_height} xc: +noise Random -virtual-pixel tile \
    -blur 0x15 -fx intensity -normalize xwarp_${ii}.png

    convert -size ${slice_width}x${slice_height} xc: +noise Random -virtual-pixel tile \
    -blur 0x15 -fx intensity -normalize ywarp_${ii}.png

    c2d xwarp_${ii}.png -stretch 1% 99% -${max_deform_in_vox} ${max_deform_in_vox}\
        ywarp_${ii}.png -stretch 1% 99% -${max_deform_in_vox} ${max_deform_in_vox}\
        -omc 2 d${ii}.nii.gz ${ii}.png \
        -background 0\
        -warp  -o ${ii}.nii.gz
    c2d ${ii}.png -o w${ii}.nii.gz

rm -rfv xwarp_${ii}.png ywarp_${ii}.png d${ii}.nii.gz

done

pos_stack_sections \
    -i %04d.nii.gz \
    --stacking-range 0 99 1 \
    -o deformed_stack.nii.gz

pos_stack_sections \
    -i w%04d.nii.gz \
    --stacking-range 0 99 1 \
    -o initial_stack.nii.gz

rm ????.nii.gz w????.nii.gz ????.png

c3d deformed_stack.nii.gz \
    -stretch 1% 99% 0 255 \
    -clip 0 255 \
    -type uchar \
    -o deformed_stack.nii.gz

c3d initial_stack.nii.gz \
    -stretch 1% 99% 0 255 \
    -clip 0 255 \
    -type uchar \
    -o initial_stack.nii.gz
