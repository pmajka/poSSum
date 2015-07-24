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
#       COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -X '!*.@(nii|nii.gz|vtk|png|tif|tiff)' -- ${cur}) )
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--file-series-format' ] || [ ${prev} == '-o' ] ; then
        COMPREPLY=( $(compgen -o plusdirs -o dirnames -o nospace -f -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--slicing-range' ] || [ ${prev} == '-r' ] ; then
        COMPREPLY=( $(compgen -W "start end step" -- ${cur}) )
        return 0
    fi

    if [ ${prev} == '--slicing-axis' ] || [ ${prev} == '-s' ] ; then
        COMPREPLY=( $(compgen -W "0 1 2" -- ${cur}) )
        return 0
    fi
}
complete -F _pos_slice_volume pos_slice_volume
