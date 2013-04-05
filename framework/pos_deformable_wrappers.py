from pos_parameters import filename_parameter, value_parameter, string_parameter
import pos_wrappers

class preprocess_slice_volume(pos_wrappers.generic_wrapper):
    _template = """sliceVol.py \
            -i {input_image} \
            -o "{output_naming}" \
            -s {slicing_plane} \
            -r {start_slice} {end_slice} {step} \
            {leave_overflows} \
            {shift_indexes}; \
            set -xe; for i in `ls -1 {slice_mask}`; do c2d $i {output_type} -o {output_dir}/`basename $i .png`.nii.gz; done; """
    
    _parameters = { \
            'input_image'   : filename_parameter('input_image', None),
            'output_naming' : filename_parameter('output_naming', None),
            'slicing_plane' : value_parameter('slicing_plane', 1),
            'start_slice' : value_parameter('start_slice', None),
            'end_slice'   : value_parameter('end_slice', None),
            'step'        : value_parameter('step', 1),
            'slice_mask'  : filename_parameter('slice_mask', None),
            'output_type'     : string_parameter('output_type', 'uchar', str_template = "-type {_value}"),
            'leave_overflows' : value_parameter('leaveOverflows', None, str_template="--{_name}"),
            'shift_indexes' : value_parameter('shift_indexes', None, str_template="--{_name} {_value}"),
            'output_dir'   : string_parameter('output_dir', None),
            }

class blank_slice_deformation_wrapper(pos_wrappers.generic_wrapper):
    _template = """c{dimension}d  {input_image} -scale 0 -dup -omc {dimension} {output_image}"""
    
    _parameters = {\
        'dimension'      : value_parameter('dimension', 2),
        'input_image'  : filename_parameter('input_image', None),
        'output_image'  : filename_parameter('output_image', None),
         }

class gnuplot_wrapper(pos_wrappers.generic_wrapper):
    _template = "gnuplot {plot_file}; inkscape {svg_file} --export-png={output_file} -d 300 -y 1;"
    
    _parameters = {
            'plot_file' : filename_parameter('plot_file', None),
            'svg_file' : filename_parameter('svg_file', None),
            'output_file' : filename_parameter('output_file', None),
            }
