
POS_INTERPOLATION_OPTIONS='nn linear'
POS_DATA_TYPES='char uchar short ushort int uint float double'
POS_ORIENTATION_PRESETS='sagittal coronal horizontal'
POS_ORIENTATION_CODES="RPI LAS LPI RAS RSP LIA"
POS_LOGLEVEL_OPTIONS="CRITICAL ERROR WARNING INFO DEBUG"
POS_IMAGEMAGICK_COLORS="snow red maroon pink crimson maroon orchid thistle plum violet fuchsia magenta purple lavender blue navy azure aqua cyan teal turquoise honeydew lime green ivory beige yellow olive khaki gold cornsilk goldenrod wheat orange moccasin tan bisque linen peru chocolate seashell sienna coral tomato salmon white gray black"
POS_IMAGEMAGICK_COLOR_CHANNELS="red green blue"

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

complete -F _pos_slice_volume pos_slice_volume
complete -F _pos_stack_sections pos_stack_sections
complete -F _pos_process_source_images pos_process_source_images
complete -F _pos_reorder_volume pos_reorder_volume
complete -F _pos_align_by_moments pos_align_by_moments
complete -F _pos_stack_histogram_matching pos_stack_histogram_matching
