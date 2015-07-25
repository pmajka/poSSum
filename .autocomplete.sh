
POS_INTERPOLATION_OPTIONS='nn linear'
POS_DATA_TYPES='char uchar short ushort int uint float double'
POS_ORIENTATION_PRESETS='saggital coronal horizontal'
POS_ORIENTATION_CODES="RPI LAS LPI RAS RSP LIA"


_pos_stack_sections()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --input-image -i --stacking-range  --output-image -o \
        --interpolation  --resample  --permutation  --flip  --flip-around-origin  \
        --spacing  --origin  --type  --orientation  --use-orientation-preset \
        --job-id -j --work-dir -d --loglevel --log-filename --disable-shared-memory \
        --specimen-id  --dry-run  --cpus  --archive-work-dir  --cleanup"

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
        COMPREPLY=( $(compgen -W "rx_float ry_float rz_float" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--archive-work-dir' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--log-filename' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

}

_pos_slice_volume() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help -h --input-image -i --output-filenames-offset  --slicing-axis -s --file-series-format -o --slicing-range -r --extract-roi"

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
complete -F _pos_slice_volume pos_slice_volume
complete -F _pos_stack_sections pos_stack_sections
