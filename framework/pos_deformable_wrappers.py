from pos_parameters import filename_parameter, value_parameter, \
                            string_parameter, list_parameter
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


class visualize_wrap_field(pos_wrappers.generic_wrapper):
    _template = """python ../../draw_glyphs_2d.py \
        --warpImage {warp_image} \
        --sliceImage {slice_image} \
        --screenshot {screenshot_filename} \
        --deformationOverlayOpacity {deformation_opacity} \
        --jacobianOverlayOpacity {jacobian_opacity} \
        --deformationScaleRange {deformation_range} \
        --glyphConfiguration {glyphs_configuration} \
        --spacing {spacing} \
        --jacobianScaleMapping {jacobian_mapping} \
        --cleanup"""

    _parameters = {
        'warp_image'  : filename_parameter('warp_image', None),
        'slice_image' : filename_parameter('slice_image', None),
        'screenshot_filename'  : filename_parameter('screenshot_filename', None),
        'deformation_opacity' : value_parameter('deformation_opacity', 0.5),
        'jacobian_opacity' : value_parameter('jacobian_opacity', 0.5),
        'deformation_range' : list_parameter('deformation_range', [0.0, 1.0]),
        'jacobian_mapping' : list_parameter('jacobian_mapping', [0.9, 1.0, 1.1]),
        'spacing' : list_parameter('spacing', None),
        'glyphs_configuration' : list_parameter('glyphs_configuration', [5000, 10, 6])
        }
