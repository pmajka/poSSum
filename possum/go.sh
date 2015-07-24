STACK_SIZE=253
IDX_FIRST_SLICE=1
IDX_LAST_SLICE=253
IDX_FIRST_SLICE_ZERO=0
IDX_LAST_SLICE_ZERO=252

SOURCE_FULLRES_SPACING=0.007576
SOURCE_NOMINAL_SPACING=0.015151
SOURCE_SPACING=0.015151
SOURCE_THICKNESS=0.040000

FULLSIZE_CANVAS_SIZE="1600 1200"

ATLAS_PLATE_SPACING=0.100000
ATLAS_PLATE_EXTENT="1000 1000"

SLICING_PLANE_INDEX=1
SLICING_PLANE_VERBAL="coronal"

OUTPUT_VOLUME_SPACING="0.0151512 0.04 0.0151512"
OUTPUT_VOLUME_ORIGIN="0 0 0"
OUTPUT_VOLUME_PERMUTATION="0 2 1"
OUTPUT_VOLUME_FLIPPING="0 0 0"
OUTPUT_VOLUME_ORIENTATION="RAS"

OUTPUT_VOLUME_PROPERTIES=" --output-volume-orientation ${OUTPUT_VOLUME_ORIENTATION} --output-volume-spacing ${OUTPUT_VOLUME_SPACING} --output-volume-permute-axes ${OUTPUT_VOLUME_PERMUTATION} --flip ${OUTPUT_VOLUME_FLIPPING} --output-volume-origin ${OUTPUT_VOLUME_ORIGIN}"


pos_stack_histogram_matching \
    --input-images-dir /home/pmajka/Downloads/later_on/mba/mouse_brainarchitecture_org_seriesbrowser_viewer_3250/10_input_data/04_source_downsampled/ \
    --sections-range 1 253 \
    --add-reference-section 1 \
    --add-reference-section 2 \
    --add-reference-section 10 \
    --add-reference-section 19 \
    --add-reference-section 25 \
    --add-reference-section 37 \
    --add-reference-section 46 \
    --add-reference-section 54 \
    --add-reference-section 66 \
    --add-reference-section 75 \
    --add-reference-section 85 \
    --add-reference-section 96 \
    --add-reference-section 108 \
    --add-reference-section 116 \
    --add-reference-section 125 \
    --add-reference-section 131 \
    --add-reference-section 146 \
    --add-reference-section 156 \
    --add-reference-section 165 \
    --add-reference-section 173 \
    --add-reference-section 182 \
    --add-reference-section 187 \
    --add-reference-section 194 \
    --add-reference-section 200 \
    --add-reference-section 208 \
    --add-reference-section 216 \
    --add-reference-section 223 \
    --add-reference-section 231 \
    --add-reference-section 237 \
    --add-reference-section 241 \
    --add-reference-section 253 \
    \
    ${OUTPUT_VOLUME_PROPERTIES}\
    \
    --loglevel=DEBUG

