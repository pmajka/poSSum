from pos_parameters import filename_parameter, value_parameter, \
                            string_parameter, list_parameter
import pos_wrappers


class preprocess_slice_volume(pos_wrappers.generic_wrapper):
    _template = """pos_slice_volume.py \
            -i {input_image} \
            -o "{output_naming}" \
            -s {slicing_plane} \
            -r {start_slice} {end_slice} {step} \
            {shift_indexes}"""

    _parameters = { \
            'input_image'   : filename_parameter('input_image', None),
            'output_naming' : filename_parameter('output_naming', None),
            'slicing_plane' : value_parameter('slicing_plane', 1),
            'start_slice' : value_parameter('start_slice', None),
            'end_slice'   : value_parameter('end_slice', None),
            'step'        : value_parameter('step', 1),
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


class visualize_wrap_field(pos_wrappers.generic_wrapper):
    _template = """python ../../draw_glyphs_2d.py \
        --warpImage {warp_image} \
        --sliceImage {slice_image} \
        --screenshot {screenshot_filename} \
        --configuration {configuration_filename} \
        --cleanup"""

    _parameters = {
        'warp_image'  : filename_parameter('warp_image', None),
        'slice_image' : filename_parameter('slice_image', None),
        'screenshot_filename'  : filename_parameter('screenshot_filename', None),
        'configuration_filename' : filename_parameter('configuration_filename', None)
        }
