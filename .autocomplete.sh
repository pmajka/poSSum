
POS_INTERPOLATION_OPTIONS='nn linear'
POS_DATA_TYPES='char uchar short ushort int uint float double'
POS_ORIENTATION_PRESETS='sagittal coronal horizontal'
POS_ORIENTATION_CODES="RPI LAS LPI RAS RSP LIA"
POS_LOGLEVEL_OPTIONS="CRITICAL ERROR WARNING INFO DEBUG"
POS_IMAGEMAGICK_COLORS="snow red maroon pink crimson maroon orchid thistle plum violet fuchsia magenta purple lavender blue navy azure aqua cyan teal turquoise honeydew lime green ivory beige yellow olive khaki gold cornsilk goldenrod wheat orange moccasin tan bisque linen peru chocolate seashell sienna coral tomato salmon white gray black"
POS_IMAGEMAGICK_COLOR_CHANNELS="red green blue"
POS_ANTS_IMAGE_METRICS="MSQ CC MI"

_pos_stack_sections()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --input-image -i --stacking-range  --output-image -o \
        --interpolation  --resample  --permutation  --flip  --flip-around-origin  \
        --spacing  --origin  --type  --orientation  --use-orientation-preset \
        --loglevel --log-filename "

    if [[ ${prev} == 'pos_stack_sections' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--input-image' ] || [ ${prev} == '-i' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-image' ] || [ ${prev} == '-o' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--stacking-range' ]; then
        COMPREPLY=( $(compgen -W "start end step" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--interpolation' ]; then
        COMPREPLY=( $(compgen -W "${POS_INTERPOLATION_OPTIONS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--use-orientation-preset' ]; then
        COMPREPLY=( $(compgen -W "${POS_ORIENTATION_PRESETS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-orientation' ] || [ ${prev} == '--orientation' ] ; then
        COMPREPLY=( $(compgen -W "${POS_ORIENTATION_CODES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-scalar-type' ] || [ ${prev} == '--type' ] ; then
        COMPREPLY=( $(compgen -W "${POS_DATA_TYPES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-resample' ] || [ ${prev} == '--resample' ] ; then
        COMPREPLY=( $(compgen -W "rx_float_0-1 ry_float_0-1 rz_float_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--log-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--loglevel' ] ; then
        COMPREPLY=( $(compgen -W "${POS_LOGLEVEL_OPTIONS}" -- ${cur}) )
        return
    fi

}

_pos_slice_volume()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --input-image -i --output-filenames-offset \
        --slicing-axis -s --file-series-format -o \
        --slicing-range -r --extract-roi"

    if [[ ${prev} == 'pos_slice_volume' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--input-image' ] || [ ${prev} == '-i' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--file-series-format' ] || [ ${prev} == '-o' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--slicing-axis' ] || [ ${prev} == '-s' ] ; then
        COMPREPLY=( $(compgen -W "0 1 2" -- ${cur}) )
        return 0
    fi
}

_pos_process_source_images()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --loglevel --log-filename --cpus \
        --specimen-id -d --work-dir --input-images-dir --header-file \
        --input-workbook --output-workbook \
        --enable-remasking --disable-remasking \
        --enable-slice-extraction --disable-slice-extraction \
        --enable-source-stacking --disable-source-stacking \
        --use-slice-to-slice-mask --use-slice-to-reference-mask \
        --enable-process-source-images --disable-process-source-images \
        --invert-input-images \
        --canvas-background \
        --mask-threshold --mask-color-channel --masking-background \
        --enable-reference --disable-reference --reference-background --reference-threshold \
        --input-reference-dir --use-reference-to-slice-mask --reference-extent"

    if [[ ${prev} == 'pos_process_source_images' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--masking-background' ]; then
        COMPREPLY=( $(compgen -W "integer_0-255 0 1 255" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--reference-extent' ]; then
        COMPREPLY=( $(compgen -W "extent_x_int extent_y_int" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--mask-threshold' ] || [ ${prev} == '--reference-threshold' ]; then
        COMPREPLY=( $(compgen -W "range_0_255_scaled_to_float_0_1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--mask-median' ]; then
        COMPREPLY=( $(compgen -W "`seq 0 1 12`" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--mask-color-channel' ]; then
        COMPREPLY=( $(compgen -W "${POS_IMAGEMAGICK_COLOR_CHANNELS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--canvas-background' ] || [ ${prev} == '--reference-background' ]; then
        COMPREPLY=( $(compgen -W "${POS_IMAGEMAGICK_COLORS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--input-workbook' ] || [ ${prev} == '--output-workbook' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.xls' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--header-file' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.sh' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '-d' ] || [ ${prev} == '--work-dir' ] || [ ${prev} == '--input-images-dir' ] || [ ${prev} == '--input-reference-dir' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o nospace  -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--log-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--loglevel' ] ; then
        COMPREPLY=( $(compgen -W "${POS_LOGLEVEL_OPTIONS}" -- ${cur}) )
        return 
    fi

}

_pos_reorder_volume()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h \
        --input-image --output-image \
        --mapping --slicing-axis"

    if [[ ${prev} == 'pos_reorder_volume' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--input-image' ] || [ ${prev} == '-i' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-image' ] || [ ${prev} == '-o' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--slicing-axis' ] || [ ${prev} == '-s' ] ; then
        COMPREPLY=( $(compgen -W "0 1 2" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--mapping' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi
}

_pos_align_by_moments()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --fixed-image -f --moving-image -m --output-image -o \
        --transformation-filename -t"
    

    if [[ ${prev} == 'pos_align_by_moments' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--transformation-filename' ] || [ ${prev} == '-t' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.txt' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-image' ] || [ ${prev} == '-o' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.nii.gz' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--moving-image' ] || [ ${prev} == '-m' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.nii.gz' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--fixed-image' ] || [ ${prev} == '-f' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.nii.gz' -- ${cur}) )
        return 0
    fi

}

_pos_stack_histogram_matching()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --loglevel --log-filename --cpus \
        --specimen-id -d --work-dir \
        --sections-range --add-reference-section \
        --exclude-section --histogram-matching-points \
        --output-volume-filename --input-sections-template \
        --output-volume-origin --output-volume-scalar-type \
        --output-volume-spacing --output-volume-resample \
        --output-volume-permute-axes --output-volume-orientation \
        --output-volume-interpolation --output-volume-filp-axes"

    if [[ ${prev} == 'pos_stack_histogram_matching' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--log-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--loglevel' ] ; then
        COMPREPLY=( $(compgen -W "${POS_LOGLEVEL_OPTIONS}" -- ${cur}) )
        return 
    fi

    if [ ${prev} == '-d' ] || [ ${prev} == '--work-dir' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o nospace  -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--sections-range' ]; then
        COMPREPLY=( $(compgen -W "two_int_arguments" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--add-reference-section' ] || [ ${prev} == '--exclude-section' ] || [ ${prev} == '--histogram-matching-points' ] ; then
        COMPREPLY=( $(compgen -W "int" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-filename' ] || [ ${prev} == '--input-sections-template' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.nii.gz' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-origin' ] ; then
        COMPREPLY=( $(compgen -W "ox_float oy_float oz_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-scalar-type' ] ; then
        COMPREPLY=( $(compgen -W "${POS_DATA_TYPES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-spacing' ] ; then
        COMPREPLY=( $(compgen -W "sx_float sy_float sz_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-resample' ] ; then
        COMPREPLY=( $(compgen -W "rx_float_0-1 ry_float_0-1 rz_float_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-permute-axes' ] ; then
        COMPREPLY=( $(compgen -W "three_ints_0_1_2" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-orientation' ] ; then
        COMPREPLY=( $(compgen -W "${POS_ORIENTATION_CODES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-interpolation' ]; then
        COMPREPLY=( $(compgen -W "${POS_INTERPOLATION_OPTIONS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-filp-axes' ] ; then
        COMPREPLY=( $(compgen -W "flip_x_0-1 flip_y_0-1 flip_z_0-1" -- ${cur}) )
        return 0
    fi
}

_pos_preprocess_image()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h \
         -i --input-image \
         -g --output-grayscale-image \
         -r --output-rgb-image \
         --extract-roi --resize-factor --color-channel \
         --median-filter-radius --invert-source-image \
         --invert-rgb-image"

    if [[ ${prev} == 'pos_preprocess_image' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--input-image' ] || [ ${prev} == '-i' ] || [ ${prev} == '--output-grayscale-image' ] || [ ${prev} == '-g' ] || [ ${prev} == '--output-rgb-image' ] || [ ${prev} == '-r' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--extract-roi' ] ; then
        COMPREPLY=( $(compgen -W "ox_oy_sx_sy_in_pixels" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--resize-factor' ] ; then
        COMPREPLY=( $(compgen -W "rx_float_0-1 ry_float_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--color-channel' ] ; then
        COMPREPLY=( $(compgen -W "${POS_IMAGEMAGICK_COLOR_CHANNELS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--median-filter-radius' ] ; then
        COMPREPLY=( $(compgen -W "int-x-radius_int-y-radius" -- ${cur}) )
        return 0
    fi
}

_pos_coarse_fine()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --loglevel --log-filename --cpus \
      --specimen-id -d --work-dir \
      --dry-run --disable-shared-memory \
      -i --fine-transform-filename-template \
      -s --smooth-transform-filename-template \
      -o --output-transform-filename-template \
      --sections-range \
      --reports-directory \
      --skip-transforms \
      --smoothing-simga \
      --smoothing-simga-rotation \
      --smoothing-simga-scaling \
      --smoothing-simga-offset \
      --smoothing-simga-fixed"


    if [[ ${prev} == 'pos_coarse_fine' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi


    if [ ${prev} == '--loglevel' ] ; then
        COMPREPLY=( $(compgen -W "${POS_LOGLEVEL_OPTIONS}" -- ${cur}) )
        return 
    fi

    if [ ${prev} == '--log-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '-d' ] || [ ${prev} == '--work-dir' ] || [ ${prev} == '--reports-directory' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o nospace  -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '-i' ] || [ ${prev} == '--fine-transform-filename-template' ] || \
       [ ${prev} == '-s' ] || [ ${prev} == '--smooth-transform-filename-template' ] || \
       [ ${prev} == '-o' ] || [ ${prev} == '--output-transform-filename-template' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.txt' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--sections-range' ] ; then
        COMPREPLY=( $(compgen -W "int_int" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--smoothing-simga' ] || \
       [ ${prev} == '--smoothing-simga-rotation' ] || \
       [ ${prev} == '--smoothing-simga-offset' ] || \
       [ ${prev} == '--smoothing-simga-scaling' ] || \
       [ ${prev} == '--smoothing-simga-fixed' ] ; then
        COMPREPLY=( $(compgen -W "float" -- ${cur}) )
        return 0
    fi
}

_pos_sequential_alignment()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --loglevel --log-filename --cpus \
      --specimen-id -d --work-dir \
      --dry-run --disable-shared-memory \
      --archive-work-dir \
      \
      --output-volume-origin \
      --output-volume-scalar-type \
      --output-volume-spacing \
      --output-volume-resample \
      --output-volume-permute-axes \
      --output-volume-orientation \
      --output-volume-interpolation \
      --output-volume-filp-axes \
      --output-volume-roi \
      \
      --slices-range \
      --input-images-directory \
      --enable-sources-slices-generation \
      --disable-sources-slices-generation \
      --registration-color-channel \
      --median-filter-radius\
      --invert-multichannel \
      --registration-roi \
      \
      --enable-transformations \
      --disable-transformations \
      --override-transformations \
      --enable-moments \
      --disable-moments \
      --transformations-directory \
      --registration-resize \
      --use-rigid-affine \
      --ants-image-metric \
      --ants-image-metric-opt \
      --affine-gradient-descent \
      --graph-edge-lambda \
      --graph-edge-epsilon \
      --graph-skip-section \
      \
      --enable-reslice \
      --disable-reslice \
      --reslice-backgorund \
      --reslice-interpolation \
      \
      --enable-output-volumes \
      --disable-output-volumes \
      --output-volumes-directory \
      --grayscale-volume-filename \
      --multichannel-volume-filename"

    if [[ ${prev} == 'pos_sequential_alignment' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--loglevel' ] ; then
        COMPREPLY=( $(compgen -W "${POS_LOGLEVEL_OPTIONS}" -- ${cur}) )
        return 
    fi

    if [ ${prev} == '--log-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '-d' ] || \
       [ ${prev} == '--work-dir' ] || \
       [ ${prev} == '--archive-work-dir' ] || \
       [ ${prev} == '--input-images-directory' ] || \
       [ ${prev} == '--transformations-directory' ] || \
       [ ${prev} == '--output-volumes-directory' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o nospace  -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-origin' ] ; then
        COMPREPLY=( $(compgen -W "ox_float oy_float oz_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-scalar-type' ] || [ ${prev} == '--type' ] ; then
        COMPREPLY=( $(compgen -W "${POS_DATA_TYPES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-spacing' ] ; then
        COMPREPLY=( $(compgen -W "sx_float sy_float sz_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-resample' ] || [ ${prev} == '--resample' ] ; then
        COMPREPLY=( $(compgen -W "rx_float_0-1 ry_float_0-1 rz_float_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-permute-axes' ] ; then
        COMPREPLY=( $(compgen -W "three_ints_0_1_2" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-orientation' ] || [ ${prev} == '--orientation' ] ; then
        COMPREPLY=( $(compgen -W "${POS_ORIENTATION_CODES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-interpolation' ]; then
        COMPREPLY=( $(compgen -W "${POS_INTERPOLATION_OPTIONS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-filp-axes' ] ; then
        COMPREPLY=( $(compgen -W "flip_x_0-1 flip_y_0-1 flip_z_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--slices-range' ]; then
        COMPREPLY=( $(compgen -W "start end" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--registration-color-channel' ]; then
        COMPREPLY=( $(compgen -W "${POS_IMAGEMAGICK_COLOR_CHANNELS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--median-filter-radius' ] ; then
        COMPREPLY=( $(compgen -W "int-x-radius_int-y-radius" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--registration-roi' ] ; then
        COMPREPLY=( $(compgen -W "ox_oy_sx_sy_in_pixels_separated_by_space" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--registration-resize' ] ; then
        COMPREPLY=( $(compgen -W "rx_float_0-1 ry_float_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--ants-image-metric' ] ; then
        COMPREPLY=( $(compgen -W "${POS_ANTS_IMAGE_METRICS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--ants-image-metric-opt' ] ; then
        COMPREPLY=( $(compgen -W "int_depends_on_particular_metric" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--affine-gradient-descent' ] ; then
        COMPREPLY=( $(compgen -W "maximum_step_length-x-relaxation_factor-x-minimum_step_length-x-translation_scales" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--graph-edge-lambda' ] ; then
        COMPREPLY=( $(compgen -W "positive_but_small_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--graph-edge-epsilon' ] ; then
        COMPREPLY=( $(compgen -W "1 2 3 4 5 6 7 8 9 10" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--graph-skip-section' ] ; then
        COMPREPLY=( $(compgen -W "valid_section_index_int" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--reslice-backgorund' ]; then
        COMPREPLY=( $(compgen -W "integer_0-255 0 1 255" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--reslice-interpolation' ]; then
        COMPREPLY=( $(compgen -W "${POS_INTERPOLATION_OPTIONS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-roi' ] ; then
        COMPREPLY=( $(compgen -W "ox_oy_sx_sy_in_pixels" -- ${cur}) )
        return 0
    fi
    
    if [ ${prev} == '--grayscale-volume-filename' ] || \
       [ ${prev} == '--multichannel-volume-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.nii.gz' -- ${cur}) )
        return 0
    fi
}

_pos_deformable_histology_reconstruction()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --loglevel --log-filename --cpus \
        --specimen-id -d --work-dir \
        --dry-run --disable-shared-memory \
        --archive-work-dir \
        --cleanup \
        --output-volume-origin \
        --output-volume-scalar-type \
        --output-volume-spacing \
        --output-volume-resample \
        --output-volume-permute-axes \
        --output-volume-orientation \
        --output-volume-interpolation \
        --output-volume-filp-axes \
        \
        --slicing-plane \
        --start-slice \
        --end-slice \
        --shift-final-indexes \
        --neighbourhood \
        --iterations \
        -i --input-volume \
        -o --outline-volume \
        -r --reference-volume \
        -m --masked-volume \
        --masked-volume-file \
        --register-subset \
        --output-naming \
        \
        --start-from-iteration \
        --skip-transformations \
        --skip-preprocessing \
        --stack-final-transformation \
        \
        --ants-image-metric \
        --ants-image-metric-opt \
        --ants-gradient-step \
        --ants-regularization-type \
        --ants-regularization \
        --ants-iterations \
        --plane-spacing"

    if [[ ${prev} == 'pos_deformable_histology_reconstruction' ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--loglevel' ] ; then
        COMPREPLY=( $(compgen -W "${POS_LOGLEVEL_OPTIONS}" -- ${cur}) )
        return 
    fi

    if [ ${prev} == '--log-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '-d' ] || \
       [ ${prev} == '--work-dir' ] || \
       [ ${prev} == '--archive-work-dir' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o nospace  -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-origin' ] ; then
        COMPREPLY=( $(compgen -W "ox_float oy_float oz_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-scalar-type' ] || [ ${prev} == '--type' ] ; then
        COMPREPLY=( $(compgen -W "${POS_DATA_TYPES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-spacing' ] ; then
        COMPREPLY=( $(compgen -W "sx_float sy_float sz_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-resample' ] || [ ${prev} == '--resample' ] ; then
        COMPREPLY=( $(compgen -W "rx_float_0-1 ry_float_0-1 rz_float_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-permute-axes' ] ; then
        COMPREPLY=( $(compgen -W "three_ints_0_1_2" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-orientation' ] || [ ${prev} == '--orientation' ] ; then
        COMPREPLY=( $(compgen -W "${POS_ORIENTATION_CODES}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-interpolation' ]; then
        COMPREPLY=( $(compgen -W "${POS_INTERPOLATION_OPTIONS}" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--output-volume-filp-axes' ] ; then
        COMPREPLY=( $(compgen -W "flip_x_0-1 flip_y_0-1 flip_z_0-1" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--slicing-plane' ] || \
       [ ${prev} == '--start-slice' ] || \
       [ ${prev} == '--shift-final-indexes' ] || \
       [ ${prev} == '--neighbourhood' ] || \
       [ ${prev} == '--iterations' ] || \
       [ ${prev} == '--start-from-iteration' ] || \
       [ ${prev} == '--ants-image-metric-opt' ] || \
       [ ${prev} == '--end-slice' ] ; then
        COMPREPLY=( $(compgen -W "int" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--ants-gradient-step' ] || \
       [ ${prev} == '--plane-spacing' ] ; then
        COMPREPLY=( $(compgen -W "float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--register-subset' ] || \
       [ ${prev} == '--masked-volume-file' ] ; then
        COMPREPLY=( $(compgen -o plusdirs  -f -X '!*.txt' -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--input-volume' ]     || \
       [ ${prev} == '-i' ]                 || \
       [ ${prev} == '--outline-volume' ]   || \
       [ ${prev} == '-o' ]                 || \
       [ ${prev} == '--reference-volume' ] || \
       [ ${prev} == '-r' ]                 || \
       [ ${prev} == '--masked-volume' ]    || \
       [ ${prev} == '-m' ] ; then
        COMPREPLY=( $(compgen -W "float_0-1_and_nifti_filename" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--ants-image-metric' ] ; then
        COMPREPLY=( $(compgen -W "CC MI MSQ" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--ants-iterations' ] ; then
        COMPREPLY=( $(compgen -W "eg_1000x1000_1000x200" -- ${cur}) )
        return 0
    fi
}



#   if [ ${prev} == '--input-image' ] || [ ${prev} == '-i' ] || [ ${prev} == '--output-grayscale-image' ] || [ ${prev} == '-g' ] || [ ${prev} == '--output-rgb-image' ] || [ ${prev} == '-r' ] ; then
#       COMPREPLY=( $(compgen -o plusdirs  -f -- ${cur}) )
#       return 0
#   fi

#   if [ ${prev} == '--extract-roi' ] ; then
#       COMPREPLY=( $(compgen -W "ox_oy_sx_sy_in_pixels" -- ${cur}) )
#       return 0
#   fi

#   if [ ${prev} == '--resize-factor' ] ; then
#       COMPREPLY=( $(compgen -W "rx_float_0-1 ry_float_0-1" -- ${cur}) )
#       return 0
#   fi

#   if [ ${prev} == '--color-channel' ] ; then
#       COMPREPLY=( $(compgen -W "${POS_IMAGEMAGICK_COLOR_CHANNELS}" -- ${cur}) )
#       return 0
#   fi

#   if [ ${prev} == '--median-filter-radius' ] ; then
#       COMPREPLY=( $(compgen -W "int-x-radius_int-y-radius" -- ${cur}) )
#       return 0
#   fi
#

complete -F _pos_slice_volume pos_slice_volume
complete -F _pos_stack_sections pos_stack_sections
complete -F _pos_process_source_images pos_process_source_images
complete -F _pos_reorder_volume pos_reorder_volume
complete -F _pos_align_by_moments pos_align_by_moments
complete -F _pos_stack_histogram_matching pos_stack_histogram_matching
complete -F _pos_preprocess_image pos_preprocess_image
complete -F _pos_coarse_fine pos_coarse_fine
complete -F _pos_sequential_alignment pos_sequential_alignment
complete -F _pos_deformable_histology_reconstruction pos_deformable_histology_reconstruction


# MedianFilter.py*
# pos_deformable_histology_reconstruction*
# pos_pairwise_registration*
# pos_stack_warp_image_multi_transform*
