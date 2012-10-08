from pos_parameters import generic_wrapper, filename_parameter,\
        value_parameter, string_parameter

class preprocess_slice_volume(generic_wrapper):
    _template = """sliceVol.py \
            -i {input_image} \
            -o "{output_naming}" \
            -s {slicing_plane} \
            -r {start_slice} {end_slice} {step} \
            {shift_indexes}; \
            for i in `ls -1 {slice_mask}`; do c2d $i {output_type} -o {output_dir}/`basename $i .png`.nii.gz; done; """
    
    _parameters = { \
            'input_image'   : filename_parameter('input_image', None),
            'output_naming' : filename_parameter('output_naming', None),
            'slicing_plane' : value_parameter('slicing_plane', 1),
            'start_slice' : value_parameter('start_slice', None),
            'end_slice'   : value_parameter('end_slice', None),
            'step'        : value_parameter('step', 1),
            'slice_mask'  : filename_parameter('slice_mask', None),
            'output_type'   : string_parameter('output_type', 'uchar', str_template = "-type {_value}"),
            'shift_indexes' : value_parameter('shift_indexes', None, str_template="--{_name} {_value}"),
            'output_dir'   : string_parameter('output_dir', None),
            }

class blank_slice_deformation_wrapper(generic_wrapper):
    _template = """c{dimension}d  {input_image} -scale 0 -dup -omc {dimension} {output_image}"""
    
    _parameters = {\
        'dimension'      : value_parameter('dimension', 2),
        'input_image'  : filename_parameter('input_image', None),
        'output_image'  : filename_parameter('output_image', None),
         }
