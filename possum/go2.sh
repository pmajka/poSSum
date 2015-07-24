STACK_SIZE=176
IDX_FIRST_SLICE=1
IDX_LAST_SLICE=176
IDX_FIRST_SLICE_ZERO=0
IDX_LAST_SLICE_ZERO=175

SOURCE_FULLRES_SPACING=0.014473
SOURCE_NOMINAL_SPACING=0.040000
SOURCE_SPACING=0.040017
SOURCE_THICKNESS=0.200000

FULLSIZE_CANVAS_SIZE="1800 1600"

ATLAS_PLATE_SPACING=0.040000
ATLAS_PLATE_EXTENT="825 550"

SLICING_PLANE_INDEX=1
SLICING_PLANE_VERBAL="coronal"

OUTPUT_VOLUME_SPACING="0.0400173 0.2 0.0400173"
OUTPUT_VOLUME_ORIGIN="0 0 0"
OUTPUT_VOLUME_PERMUTATION="0 2 1"
OUTPUT_VOLUME_FLIPPING="0 0 0"
OUTPUT_VOLUME_ORIENTATION="RAS"

OUTPUT_VOLUME_PROPERTIES=" --output-volume-orientation ${OUTPUT_VOLUME_ORIENTATION} --output-volume-spacing ${OUTPUT_VOLUME_SPACING} --output-volume-permute-axes ${OUTPUT_VOLUME_PERMUTATION} --flip ${OUTPUT_VOLUME_FLIPPING} --output-volume-origin ${OUTPUT_VOLUME_ORIGIN}"


python __stackHistogramMatching.py \
    --input-images-dir /home/pmajka/x/ \
    --sections-range 1 176 \
    --add-reference-section 1 \
    --add-reference-section 2 \
    --add-reference-section 5 \
    --add-reference-section 9 \
    --add-reference-section 12 \
    --add-reference-section 16 \
    --add-reference-section 13 \
    --add-reference-section 17 \
    --add-reference-section 22 \
    --add-reference-section 23 \
    --add-reference-section 29 \
    --add-reference-section 33 \
    --add-reference-section 38 \
    --add-reference-section 42 \
    --add-reference-section 49 \
    --add-reference-section 54 \
    --add-reference-section 57 \
    --add-reference-section 65 \
    --add-reference-section 73 \
    --add-reference-section 82 \
    --add-reference-section 86 \
    --add-reference-section 88 \
    --add-reference-section 89 \
    --add-reference-section 95 \
    --add-reference-section 96 \
    --add-reference-section 99 \
    --add-reference-section 100 \
    --add-reference-section 108 \
    --add-reference-section 115 \
    --add-reference-section 121 \
    --add-reference-section 131 \
    --add-reference-section 135 \
    --add-reference-section 139 \
    --add-reference-section 143 \
    --add-reference-section 147 \
    --add-reference-section 151 \
    --add-reference-section 155 \
    --add-reference-section 159 \
    --add-reference-section 163 \
    --add-reference-section 165 \
    --add-reference-section 168 \
    --add-reference-section 173 \
    --add-reference-section 175 \
    --add-reference-section 176 \
    \
    ${OUTPUT_VOLUME_PROPERTIES}\
    \
    --loglevel=DEBUG

