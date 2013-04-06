import os
import copy
from pos_parameters import string_parameter, value_parameter, filename_parameter, ants_transformation_parameter, vector_parameter, list_parameter, switch_parameter, ants_regularization_parameter


class generic_wrapper(object):
    """
    A generic command line wrapper class. Actually, it is of no use and should
    be subclassed. This class provides only general mechanisms for executing
    command line processes.

    >>> print generic_wrapper()
    Traceback (most recent call last):
    AttributeError: 'NoneType' object has no attribute 'format'

    >>> w=generic_wrapper()
    >>> w #doctest: +ELLIPSIS
    <__main__.generic_wrapper object at 0x...>

    >>> w._template
    >>> w._template='Serialization template {name}'
    >>> print w
    Traceback (most recent call last):
    KeyError: 'name'

    >>> w._parameters
    {}

    """
    _template = None

    _parameters = {}

    def __init__(self, **kwargs):

        # Hardcopy the parameters to split instance parameters
        # from default class parameters
        #self.p = dict(self._parameters)
        self.p = copy.deepcopy(self._parameters)

        self.updateParameters(kwargs)

    def __str__(self):
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
        return self._template.format(**replacement)

    def __call__(self, *args, **kwargs):
        command = str(self)
        # TODO: Replace with subprocess
        os.system(command)

        execution = {'port': {}}
        if hasattr(self, '_io_pass'):
            for k, v in self._io_pass.iteritems():
                execution['port'][v] = str(self.p[k])
        return execution

    def updateParameters(self, parameters):
        for (name, value) in parameters.items():
            self.p[name].value = value
        return self


class ants_registration(generic_wrapper):
    """
    """
    _template = """ANTS {dimension} \
       {verbose} \
       {transformation} {regularization} {outputNaming} \
       {imageMetrics} \
       {iterations} {affineIterations}\
       {rigidAffine} {continueAffine}\
       {useNN} {histogramMatching} {allMetricsConverge} \
       {initialAffine} {fixedImageInitialAffine} {affineGradientDescent} \
       {maskImage} """

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'verbose': switch_parameter('verbose', True, str_template='--{_name} {_value}'),
        'transformation': ants_transformation_parameter('transformation', ('SyN', [0.25])),
        'regularization': ants_regularization_parameter('regularization', ('Gausas', (3.0, 1.0))),
        'outputNaming': filename_parameter('output-naming', None, str_template='--{_name} {_value}'),
        'iterations': vector_parameter('number-of-iterations', (5000,) * 4, '--{_name} {_list}'),
        'affineIterations': vector_parameter('number-of-affine-iterations', (10000,) * 5, '--{_name} {_list}'),
        'rigidAffine': switch_parameter('rigid-affine', True, str_template='--{_name} {_value}'),
        'continueAffine': switch_parameter('continue-affine', True, str_template='--{_name} {_value}'),
        'useNN': switch_parameter('use-NN', False, str_template='--{_name}'),
        'histogramMatching': switch_parameter('use-Histogram-Matching', True, str_template='--{_name} {_value}'),
        'allMetricsConverge': switch_parameter('use-all-metrics-for-convergence', True, str_template='--{_name} {_value}'),
        'initialAffine': filename_parameter('initial-affine', None, str_template='--{_name} {_value}'),
        'fixedImageInitialAffine': filename_parameter('fixed-image-initial-affine', None, str_template='--{_name} {_value}'),
        'affineGradientDescent': vector_parameter('affine-gradient-descent-option', None, '--{_name} {_value}'),
        'imageMetrics': list_parameter('image_to_image_metrics', [], '{_list}'),
        'maskImage': filename_parameter('mask-image', None, str_template='--{_name} {_value}')
    }

    _io_pass = {
        'dimension': 'dimension'
    }

    def __call__(self, *args, **kwargs):
        execution = super(self.__class__, self).__call__(*args, **kwargs)
        execution['port']['deformable_list'] = [str(self.p['outputNaming']) + 'Warp.nii.gz']

        if self.p['affineIterations']:
            execution['port']['affine_list'] = [str(self.p['outputNaming']) + 'Affine.txt']

        execution['port']['moving_image'] = self.p['imageMetrics'].value[0].p['moving_image'].value

        return execution


class ants_reslice(generic_wrapper):
    """
    """
    _template = """WarpImageMultiTransform {dimension} \
                  {moving_image} {output_image} \
                  {reference_image} \
                  {useNN} {useBspline} \
                  {deformable_list} {affine_list}"""

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'moving_image': filename_parameter('moving_image', None),
        'output_image': filename_parameter('output_image', None),
        'reference_image': filename_parameter('reference_image', None, str_template='-R {_value}'),
        'useNN': switch_parameter('use-NN', None, str_template='--{_name}'),
        'useBspline': switch_parameter('use-BSpline', None, str_template='--{_name}'),
        'deformable_list': list_parameter('deformable_list', [], str_template='{_list}'),
        'affine_list': list_parameter('affine_list', [], str_template='{_list}')
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }



class ants_intensity_meric(generic_wrapper):
    """
    A wrapper for ANTS intensity metric syntax. Note that this wrapper does not
    support point set estimation image-to-image metrics.

    Kwargs:
        there are a number of possible keyword arguments. See description below.

    :param metric: The name to use.
    :type metric: str

    :param fixed_image: Reference image of the metric. Cross correlation ('CC')
                        is the default value
    :type fixed_image: str

    :param moving_image: Moving image of the metric.
    :type moving_image: str

    :param weight: Weight of the metric. Default is 1.
    :type weight: float

    :param parameter: Metric-specific parameter. Default is 4.
    :type parameter: int

    >>> ants_intensity_meric
    <class '__main__.ants_intensity_meric'>

    >>> ants_intensity_meric() #doctest: +ELLIPSIS
    <__main__.ants_intensity_meric object at 0x...>

    >>> print ants_intensity_meric()
    -m CC[,,1,4]

    >>> p=ants_intensity_meric(fixed_image='fixed.nii.gz',moving_image='moving.nii.gz')
    >>> print p
    -m CC[fixed.nii.gz,moving.nii.gz,1,4]

    >>> print ants_intensity_meric(fixed_image='fixed.nii.gz',moving_image='moving.nii.gz',metric="XXX")
    -m XXX[fixed.nii.gz,moving.nii.gz,1,4]

    >>> p=ants_intensity_meric(fixed_image='fixed.nii.gz',moving_image='moving.nii.gz')
    >>> p #doctest: +ELLIPSIS
    <__main__.ants_intensity_meric object at 0x...>
    >>> print p
    -m CC[fixed.nii.gz,moving.nii.gz,1,4]

    >>> print ants_intensity_meric._parameters['parameter']
    4
    >>> print ants_intensity_meric._parameters['weight']
    1
    >>> print ants_intensity_meric._parameters['moving_image']
    <BLANKLINE>

    >>> p.value
    '-m CC[fixed.nii.gz,moving.nii.gz,1,4]'

    >>> p.updateParameters({"weight":0.5}) #doctest: +ELLIPSIS
    <__main__.ants_intensity_meric object at 0x...>

    >>> p.updateParameters({"parameter_that_does_not_exist":0.5})
    Traceback (most recent call last):
    KeyError: 'parameter_that_does_not_exist'

    >>> print p.updateParameters({"weight":0.5,"parameter":1})
    -m CC[fixed.nii.gz,moving.nii.gz,0.5,1]

    >>> print p.updateParameters({"weight":0.5, "parameter":1, "fixed_image":"f.nii.gz"})
    -m CC[f.nii.gz,moving.nii.gz,0.5,1]

    >>> print p
    -m CC[f.nii.gz,moving.nii.gz,0.5,1]

    >>> print p.updateParameters({"fixed_image":"f.nii.gz","moving_image":"m.nii.gz"})
    -m CC[f.nii.gz,m.nii.gz,0.5,1]

    >>> print p.updateParameters({"metric":"MI"})
    -m MI[f.nii.gz,m.nii.gz,0.5,1]

    """
    _template = "-m {metric}[{fixed_image},{moving_image},{weight},{parameter}]"

    _parameters = {
        'metric': string_parameter('metric', 'CC'),
        'fixed_image': filename_parameter('fixed_image', None),
        'moving_image': filename_parameter('moving_image', None),
        'weight': value_parameter('weight', 1),
        'parameter': value_parameter('parameter', 4)
    }

    def _get_value(self):
        return str(self)

    def _set_value(self, value):
        pass

    value = property(_get_value, _set_value)


class ants_compose_multi_transform(generic_wrapper):
    """
    """
    _template = """ComposeMultiTransform {dimension} \
                  {output_image} \
                  {reference_image} \
                  {deformable_list} {affine_list}"""

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'output_image': filename_parameter('output_image', None),
        'reference_image': filename_parameter('reference_image', None, str_template='-R {_value}'),
        'deformable_list': list_parameter('deformable_list', [], str_template='{_list}'),
        'affine_list': list_parameter('affine_list', [], str_template='{_list}')
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }



class average_images(generic_wrapper):
    """
    """
    _template = """c{dimension}d  {input_images} -mean {output_type} -o {output_image}"""

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'input_images': list_parameter('input_images', [], str_template='{_list}'),
        'output_image': filename_parameter('output_image'),
        'output_type': string_parameter('output_type', 'uchar', str_template='-type {_value}')
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }
   # TODO: merge average image with weighted average image
   # TODO: and then validate the output.



class images_weighted_average(generic_wrapper):
    """
    """
    _template = """c{dimension}d  {input_images} -weighted-sum {weights} {output_type} -o {output_image}"""

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'input_images': list_parameter('input_images', [], str_template='{_list}'),
        'weights': list_parameter('weights', [], str_template='{_list}'),
        'output_image': filename_parameter('output_image'),
        'output_type': string_parameter('output_type', 'uchar', str_template='-type {_value}')
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }



class chain_affine_transforms(generic_wrapper):
    """
    Wrapper for ANTS ComposeMultiTransform program. Merges transforms generated
    with ANTS and, possibly, other transforms ITK transforms. The results may
    vary between ANTS compiled with ITK3.2 and those with ITK4.0.

    :param dimension: Dimension of the transformation (2 or 3)
    :type dimension: int

    :param output_transform: output transformation filename
    :type output_transform: str

    :param input_transforms: list of input transformations filenames
    :type input_transforms: list of strings

    >>> str(chain_affine_transforms()).strip()
    'ComposeMultiTransform 2'

    >>> c = chain_affine_transforms(dimension = 3, input_transforms = ['01.txt'], output_transform = "out.txt")
    >>> print c
    ComposeMultiTransform 3 out.txt 01.txt

    >>> c = chain_affine_transforms(dimension = 3, input_transforms = ['01.txt', '02.txt'], output_transform = "out.txt")
    >>> print c
    ComposeMultiTransform 3 out.txt 01.txt 02.txt

    >>> c() == {'port': {'dimension': '3', 'output_transform': 'out.txt'}}
    True
    """

    _template = """ComposeMultiTransform {dimension} {output_transform} {input_transforms}"""

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'input_transforms': list_parameter('input_transforms', [], str_template='{_list}'),
        'output_transform': filename_parameter('output_transform')
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_transform': 'output_transform'
    }



class stack_slices_gray_wrapper(generic_wrapper):
    _template = """StackSlices {temp_volume_fn} -1 -1 0 {stack_mask};\
            reorientImage.py -i {temp_volume_fn} \
            --permutationOrder {permutation_order} \
            --orientationCode {orientation_code} \
            --outputVolumeScalarType {output_type} \
            --setSpacing {spacing} \
            --setOrigin {origin} \
            {interpolation} \
            {resample} \
            -o {output_volume_fn} \
            --cleanup | bash -xe;
            rm {temp_volume_fn};"""

    _parameters = {
        'temp_volume_fn': filename_parameter('temp_volume_fn', None),
        'output_volume_fn': filename_parameter('output_volume_fn', None),
        'stack_mask': filename_parameter('stack_mask', None),
        'permutation_order': list_parameter('permutation_order', [0, 2, 1], str_template='{_list}'),
        'orientation_code': string_parameter('orientation_code', 'RAS'),
        'output_type': string_parameter('output_type', 'uchar'),
        'spacing': list_parameter('spacing', [1., 1., 1.], str_template='{_list}'),
        'origin': list_parameter('origin', [0, 0, 0], str_template='{_list}'),
        'interpolation': string_parameter('interpolation', None, str_template='--{_name} {_value}'),
        'resample': list_parameter('resample', [], str_template='--{_name} {_list}')
    }



class stack_slices_rgb_wrapper(generic_wrapper):
    _template = """stack_rgb_slices.py \
            -f {stack_mask} \
            -b {slice_start} \
            -e {slice_end} \
            -o {temp_volume_fn};\
         reorientImage.py -i {temp_volume_fn} \
            --permutationOrder {permutation_order} \
            --orientationCode {orientation_code} \
            --outputVolumeScalarType {output_type} \
            --setSpacing {spacing} \
            --setOrigin {origin} \
            --multichannelImage \
            {interpolation} \
            {resample} \
            -o {output_volume_fn} \
            --cleanup | bash -xe;
            rm {temp_volume_fn};"""

    _parameters = {
        'stack_mask': filename_parameter('stack_mask', None),
        'slice_start': value_parameter('slice_start', None),
        'slice_end': value_parameter('slice_end', None),
        'temp_volume_fn': filename_parameter('temp_volume_fn', None),
        'permutation_order': list_parameter('permutation_order', [0, 2, 1], str_template='{_list}'),
        'orientation_code': string_parameter('orientation_code', 'RAS'),
        'output_type': string_parameter('output_type', 'uchar'),
        'spacing': list_parameter('spacing', [1., 1., 1.], str_template='{_list}'),
        'origin': list_parameter('origin', [0, 0, 0], str_template='{_list}'),
        'interpolation': string_parameter('interpolation', None, str_template='--{_name} {_value}'),
        'resample': list_parameter('resample', [], str_template='--{_name} {_list}'),
        'output_volume_fn': filename_parameter('output_volume_fn', None)
    }



class mkdir_wrapper(generic_wrapper):
    _template = """mkdir -p {dir_list}"""

    _parameters = {
        'dir_list': list_parameter('dir_list', [], str_template='{_list}')
    }



class rmdir_wrapper(generic_wrapper):
    _template = """rm -rfv {dir_list}"""

    _parameters = {
        'dir_list': list_parameter('dir_list', [], str_template='{_list}')
    }


if __name__ == '__main__':
    import doctest
    doctest.testmod()
