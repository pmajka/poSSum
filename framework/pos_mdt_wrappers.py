import pos_parameters
import pos_wrappers

class sddm_convergence(pos_wrappers.generic_wrapper):
    _template= """c{dimension}d {first_image} {second_image} -msq | cut -f 3 -d" " >> {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'first_image': pos_parameters.filename_parameter('first_image', None),
        'second_image': pos_parameters.filename_parameter('second_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }


class bias_correction(pos_wrappers.generic_wrapper):
    _template= """N4BiasFieldCorrection -d {dimension} -i {input_image} -o {output_image} -b [200] -s 3 -c [50x50x30x20,1e-6]"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class ants_multiply_images(pos_wrappers.generic_wrapper):
    """
    """
    _template = """MultiplyImages {dimension} {input_image} {multiplier} {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'multiplier': pos_parameters.value_parameter('multiplier', 1.0),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class calculate_sddm(pos_wrappers.average_images):
    """
    """
    _template = """c{dimension}d  {input_images} -scale {variance_n} -sqrt -o {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_images': pos_parameters.list_parameter('input_images', [], str_template='{_list}'),
        'variance_n' : pos_parameters.value_parameter('variance_n', 1),
        'output_image': pos_parameters.filename_parameter('output_image'),
        'output_type': pos_parameters.string_parameter('output_type', 'uchar', str_template='-type {_value}')
    }


class test_msq_3(pos_wrappers.generic_wrapper):
    """
    """
    _template = """c{dimension}d -mcs {input_image} -popas x -popas y -popas z -push x -dup -times -popas xx -push y  -dup -times -popas yy -push z  -dup -times  -popas zz -push xx -push yy -push zz -add -o {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 3),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class test_msq_2(pos_wrappers.generic_wrapper):
    """
    """
    _template = """c{dimension}d -mcs {input_image} -popas x -popas y -push x -dup -times -popas xx -push y  -dup -times -popas yy -push xx -push yy -add -o {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }
