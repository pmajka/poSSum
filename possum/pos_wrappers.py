import copy
import subprocess as sub
from pos_parameters import string_parameter, value_parameter, filename_parameter, \
                ants_transformation_parameter, vector_parameter, list_parameter, \
                switch_parameter, ants_regularization_parameter, boolean_parameter
import pos_parameters


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
        self.p = copy.deepcopy(self._parameters)

        self.updateParameters(kwargs)

    def __str__(self):
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
        return " ".join(self._template.format(**replacement).strip().split())
        #return self._template.format(**replacement).strip()

    def __call__(self, *args, **kwargs):
        print "Executing: %s" % str(self)

        # Tested against execution of multiple commands
        # http://stackoverflow.com/questions/359347/execute-commands-sequentially-in-python
        stdout, stderr =  sub.Popen(str(self), stdout=sub.PIPE,
                            stderr=sub.PIPE, shell=True,
                            close_fds=True).communicate()
        print stdout.strip()
        print stderr.strip()

        execution = {'port': {}, 'stdout': stdout, 'stderr': stderr}

        if hasattr(self, '_io_pass'):
            for k, v in self._io_pass.iteritems():
                execution['port'][v] = str(self.p[k])
        return execution

    def updateParameters(self, parameters):
        for (name, value) in parameters.items():
            self.p[name].value = value
        return self

class touch_wrapper(generic_wrapper):
    _template = """touch {files}"""

    _parameters = {
        'files': list_parameter('files', [], str_template='{_list}'),
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


class copy_wrapper(generic_wrapper):
    _template = """cp -rfv {source} {target}"""

    _parameters = {
        'source': list_parameter('source', [], str_template='{_list}'),
        'target': value_parameter('target')
    }


class compress_wrapper(generic_wrapper):
    _template = """tar -cvvzf {archive_filename}.tgz {pathname}"""

    _parameters = {
        'archive_filename': filename_parameter('archive_filename', None),
        'pathname' : filename_parameter('pathname', None),
    }


class ants_jacobian(generic_wrapper):
    _template = """ANTSJacobian {dimension} {input_image} {output_naming}"""

    _parameters = {
        'dimension'     : value_parameter('dimension', 2),
        'input_image'   : filename_parameter('input_image', None),
        'output_naming' : filename_parameter('output_naming', None),
        }


class ants_registration(generic_wrapper):
    """
    """
    _template = """/opt/ANTs-1.9.x-Linux/bin//ANTS {dimension} \
       {verbose} \
       {transformation} {regularization} {outputNaming} \
       {imageMetrics} \
       {iterations} {affineIterations}\
       {rigidAffine} {continueAffine}\
       {useNN} {histogramMatching} {allMetricsConverge} \
       {initialAffine} {fixedImageInitialAffine} {affineGradientDescent} \
       {affineMetricType} {maskImage} {miOption} """

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
        'maskImage': filename_parameter('mask-image', None, str_template='--{_name} {_value}'),
        'miOption': vector_parameter('MI-option', None, str_template='--{_name} {_list}'),
        'affineMetricType' : value_parameter('affine-metric-type', None, str_template='--{_name} {_value}')
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
    :note: Be carefull when setting the useNN parameter as it is easy to
    misconfigure the value. The correct way to set the parameter is to use the
    following syntax::

    useNN = [None, nn][int(nn)]

    where nn is the boolean value indicating the NN interpolation. In other
    words, when NN interpolation is not required useNN should be None, in the
    other case is shiuld be True. A bit strange, but that's how it works.
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

class ants_point_set_estimation_metric(generic_wrapper):
    """
    Wrapper for ANTS Point Set Estimation metric template.  The role of this
    metric is to help in registering the images using labelled volumes instead
    of the intensity images instead. PartialMatchingIterations, kNeighborhood
    parameters are skipped and default values are used for this parameter.

    PSE/point-set-expectation/PointSetExpectation[
                fixedImage,movingImage,fixedPoints,movingPoints,
                weight,pointSetPercentage,pointSetSigma,boundaryPointsOnly,
                kNeighborhood,PartialMatchingIterations=100000]

    Kwargs:
        there are a number of possible keyword arguments. See description below.

    :param fixed_image: Reference image of the metric. Cross correlation ('CC')
                        is the default value
    :type fixed_image: str

    :param moving_image: Moving image of the metric.
    :type moving_image: str

    :param fixed_points: labelled or landmark volume for fixed images
    :type fixed_point: str

    :param moving_points: labelled or landmark volume for moving points
    :type moving_points: labelled or landmark volume for fixed points

    :param weight: Weight of the metric. Default is 1.
    :type weight: float

    :param point_set_percentage: percentage of points to sample from the volume
    :type point_set_percentage: float

    :param point_set_sigma: gaussian smoothing sigma to be applied to the points (in mm)
    :type point_set_sigma: float

    :param boundary_points_only: If true, only points from the boundary will be used in the metric. If False, all the points (superficial and those inside) are used for the registration.
    :type boundary_points_only: bool

    >>> ants_point_set_estimation_metric
    <class '__main__.ants_point_set_estimation_metric'>

    >>> p=ants_point_set_estimation_metric()
    >>> p #doctest: +ELLIPSIS
    <__main__.ants_point_set_estimation_metric object at 0x...>

    >>> str(ants_point_set_estimation_metric._parameters['boundary_points_only']) == ''
    True
    >>> str(ants_point_set_estimation_metric._parameters['fixed_image']) == ''
    True
    >>> ants_point_set_estimation_metric._parameters['weight'].value == 1
    True
    >>> ants_point_set_estimation_metric._parameters['boundary_points_only'].value == None
    True
    >>> ants_point_set_estimation_metric._parameters['point_set_sigma'].value == None
    True
    >>> ants_point_set_estimation_metric._parameters['moving_points'].value == None
    True

    >>> print p
    -m PSE[,,,,1,1.0]

    >>> p=ants_point_set_estimation_metric(fixed_image='fixed.nii.gz',moving_image='moving.nii.gz',fixed_points='fixed_points.nii.gz',moving_points='moving_points.nii.gz')
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,1,1.0]

    >>> p.updateParameters({"weight":0.5}) #doctest: +ELLIPSIS
    <__main__.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,1.0]

    >>> p.updateParameters({"point_set_sigma":0.25}) #doctest: +ELLIPSIS
    <__main__.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,1.0,0.25]

    >>> p.updateParameters({"point_set_sigma":None, "boundary_points_only":True}) #doctest: +ELLIPSIS
    <__main__.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,1.0,True]

    >>> p.updateParameters({"point_set_percentage":0.1,"point_set_sigma":None, "boundary_points_only":True}) #doctest: +ELLIPSIS
    <__main__.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,0.1,True]
    """

    _template = "-m PSE[{fixed_image},{moving_image},{fixed_points},{moving_points},{weight},{point_set_percentage}{point_set_sigma}{boundary_points_only}]"

    _parameters = {
        'fixed_image': filename_parameter('fixed_image', None),
        'moving_image': filename_parameter('moving_image', None),
        'fixed_points': filename_parameter('fixed_points', None),
        'moving_points': filename_parameter('moving_points', None),
        'weight': value_parameter('weight', 1),
        'point_set_percentage' : value_parameter('point_set_percentage', 1.0),
        'point_set_sigma' : value_parameter('point_set_sigma', None,  str_template=',{_value}'),
        'boundary_points_only' : boolean_parameter('boundary_points_only', False, str_template=',{_value}'),
        }

    def _get_value(self):
        return str(self)

    def _set_value(self, value):
        pass

    value = property(_get_value, _set_value)

class ants_average_affine_transform(generic_wrapper):
    """
    AverageAffineTransform ImageDimension output_affine_transform
                   [-R reference_affine_transform]
                   {[-i] affine_transform_txt [weight(=1)] ]}

    >>> ants_average_affine_transform
    <class '__main__.ants_average_affine_transform'>

    >>> ants_average_affine_transform() #doctest: +ELLIPSIS
    <__main__.ants_average_affine_transform object at 0x...>

    >>> str(ants_average_affine_transform._parameters['dimension']) == '2'
    True
    >>> str(ants_average_affine_transform._parameters['output_affine_transform']) == ''
    True
    >>> ants_average_affine_transform._parameters['reference_affine_transform'].value == None
    True
    >>> ants_average_affine_transform._parameters['reference_affine_transform'].value == None
    True
    >>> ants_average_affine_transform._parameters['affine_list'].value == None
    True

    >>> str(ants_average_affine_transform()).strip() == 'AverageAffineTransform 2'
    True

    >>> str(ants_average_affine_transform(dimension=3)).strip() == 'AverageAffineTransform 3'
    True

    >>> p = ants_average_affine_transform(dimension=3, output_affine_transform="out.txt") #doctest: +NORMALIZE_WHITESPACE
    >>> print str(p).strip()
    AverageAffineTransform 3 out.txt

    >>> p.updateParameters({"reference_affine_transform":"reference_affine.txt"}) #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <__main__.ants_average_affine_transform object at 0x...>
    >>> print str(p).strip()
    AverageAffineTransform 3 out.txt -R reference_affine.txt

    >>> p.updateParameters({"affine_list":["affine_1.txt", "affine_2.txt", "affine_3.txt"]}) #doctest: +ELLIPSIS
    <__main__.ants_average_affine_transform object at 0x...>
    >>> print str(p).strip()
    AverageAffineTransform 3 out.txt -R reference_affine.txt affine_1.txt affine_2.txt affine_3.txt

    >>> p.updateParameters({"reference_affine_transform":None}) #doctest: +ELLIPSIS
    <__main__.ants_average_affine_transform object at 0x...>
    >>> print str(p).strip()
    AverageAffineTransform 3 out.txt affine_1.txt affine_2.txt affine_3.txt
    """

    _template = "AverageAffineTransform {dimension} \
            {output_affine_transform} \
            {reference_affine_transform} \
            {affine_list}"

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'output_affine_transform': filename_parameter('output_affine_transform', None),
        'reference_affine_transform': filename_parameter('reference_affine_transform', None, str_template='-R {_value}'),
        'affine_list': list_parameter('affine_list', [], str_template='{_list}')
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_affine_transform': 'input_affine_transform'
    }


class ants_compose_multi_transform(generic_wrapper):
    """
    TODO: Provide doctest.
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


class ants_average_images(generic_wrapper):
    """
    """
    _template = """AverageImages {dimension} {output_image} {normalize} {input_images}"""

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'normalize': value_parameter('normalize', 0),
        'input_images': list_parameter('input_images', [], str_template='{_list}'),
        'output_image': filename_parameter('output_image'),
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


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


class average_images(images_weighted_average):
    """
    """
    _template = """c{dimension}d  {input_images} -mean -o {output_image}"""

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


class stack_and_reorient_wrapper(generic_wrapper):
    """
    A wraper for a swiss army kife for reorienting, stacking, permuting and
    flipping input volumes. For more details please check manual for
    `pos_stack_reorient` script.

    .. note:: There are two obligatory parameters: `stack_mask` and
              `output_volume_fn`.

    .. note:: Please be careful when stacking the input volume as `slice_start`
              - the parameters: `slice_start` `slice_end` `slice_step` has to
              go togeather.

    >>> stack_and_reorient_wrapper
    <class '__main__.stack_and_reorient_wrapper'>

    >>> stack_and_reorient_wrapper() #doctest: +ELLIPSIS
    <__main__.stack_and_reorient_wrapper object at 0x...>

    >>> print stack_and_reorient_wrapper._parameters['stack_mask']
    <BLANKLINE>

    >>> print stack_and_reorient_wrapper._parameters['slice_start']
    <BLANKLINE>

    >>> print stack_and_reorient_wrapper._parameters['slice_end']
    <BLANKLINE>

    >>> print stack_and_reorient_wrapper._parameters['slice_step']
    <BLANKLINE>

    >>> print stack_and_reorient_wrapper._parameters['output_volume_fn']
    <BLANKLINE>

    >>> print stack_and_reorient_wrapper._parameters['permutation_order']
    0 1 2

    >>> print stack_and_reorient_wrapper._parameters['orientation_code']
    RAS

    >>> print stack_and_reorient_wrapper._parameters['output_type']
    uchar

    >>> print stack_and_reorient_wrapper._parameters['spacing']
    1.0 1.0 1.0

    >>> print stack_and_reorient_wrapper._parameters['origin']
    0 0 0

    >>> print stack_and_reorient_wrapper._parameters['interpolation']
    <BLANKLINE>

    >>> print stack_and_reorient_wrapper._parameters['resample']
    <BLANKLINE>

    >>> print stack_and_reorient_wrapper() #doctest: +NORMALIZE_WHITESPACE
    pos_stack_reorient -i -o --permutation 0 1 2 \
        --orientationCode RAS --setType uchar \
        --setSpacing 1.0 1.0 1.0 --setOrigin 0 0 0

    >>> p=stack_and_reorient_wrapper()
    >>> p.updateParameters({"parameter_that_does_not_exist":0.5})
    Traceback (most recent call last):
    KeyError: 'parameter_that_does_not_exist'

    >>> print p.updateParameters({"stack_mask":"%04d.nii.gz"}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_reorient -i %04d.nii.gz -o --permutation 0 1 2 \
        --orientationCode RAS --setType uchar --setSpacing 1.0 1.0 1.0 \
        --setOrigin 0 0 0

    >>> print p.updateParameters({"slice_start":"%04d.nii.gz",
    ... "slice_end" : 20, "slice_start" : 1, "slice_step":1}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_reorient -i %04d.nii.gz -o --stackingOptions 1 20 1 \
        --permutation 0 1 2  --orientationCode RAS  --setType uchar \
        --setSpacing 1.0 1.0 1.0 --setOrigin 0 0 0

    >>> print p.updateParameters({"output_volume_fn": "output.nii.gz"}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_reorient -i %04d.nii.gz -o output.nii.gz \
      --stackingOptions 1 20 1 --permutation 0 1 2 --orientationCode RAS \
      --setType uchar --setSpacing 1.0 1.0 1.0 --setOrigin 0 0 0

    >>> print p.updateParameters({"output_type": "ushort",
    ... "spacing" : [0.5, 0.5, 0.5], "origin" : [1, 1, 1],
    ... "interpolation" : "Cubic",
    ... "permutation_order" : [2, 1, 0], "resample": [0.5, 2.0, 3.0],
    ... "orientation_code" : "RAS"}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_reorient -i %04d.nii.gz -o output.nii.gz --stackingOptions 1 20 1\
      --permutation 2 1 0 --orientationCode RAS --setType ushort\
      --setSpacing 0.5 0.5 0.5 --setOrigin 1 1 1 --interpolation Cubic\
      --resample 0.5 2.0 3.0
    """

    _template = """pos_stack_reorient \
        -i {stack_mask} \
        -o {output_volume_fn} \
        {slice_start} {slice_end} {slice_step} \
        --permutation {permutation_order} \
        {flip_axes} \
        --orientationCode {orientation_code} \
        --setType {output_type} \
        --setSpacing {spacing} \
        --setOrigin {origin} \
        {interpolation} {resample}"""

    _parameters = {
        'stack_mask': filename_parameter('stack_mask', None),
        'slice_start': value_parameter('stackingOptions', None, str_template='--{_name} {_value}'),
        'slice_end': value_parameter('slice_end', None),
        'slice_step': value_parameter('slice_end', None),
        'output_volume_fn': filename_parameter('output_volume_fn', None),
        'permutation_order': list_parameter('permutation_order', [0, 1, 2], str_template='{_list}'),
        'orientation_code': string_parameter('orientation_code', 'RAS'),
        'flip_axes': list_parameter('flipAxes', None, str_template='--{_name} {_list}'),
        'output_type': string_parameter('output_type', 'uchar'),
        'spacing': list_parameter('spacing', [1., 1., 1.], str_template='{_list}'),
        'origin': list_parameter('origin', [0, 0, 0], str_template='{_list}'),
        'interpolation': string_parameter('interpolation', None, str_template='--{_name} {_value}'),
        'resample': list_parameter('resample', [], str_template='--{_name} {_list}')
    }


class alignment_preprocessor_wrapper(generic_wrapper):
    """
    A wrapper for the `pos_slice_preprocess` script. Since the script itself
    provides an extensive documentation, the detailed description of command
    line options is skipped in the wrapper's documentation.

    .. note::
        Use the following syntax when setting boolean parameters::

            >>> boolean_parameter = [None, True][int(value)] #doctest: +SKIP

        Yes, it is tricky and yes, is should be chenged.


    >>> alignment_preprocessor_wrapper
    <class '__main__.alignment_preprocessor_wrapper'>

    >>> alignment_preprocessor_wrapper() #doctest: +ELLIPSIS
    <__main__.alignment_preprocessor_wrapper object at 0x...>

    >>> print alignment_preprocessor_wrapper() #doctest: +NORMALIZE_WHITESPACE
    pos_slice_preprocess --inputFilename

    >>> print alignment_preprocessor_wrapper(input_image="input.nii.gz",
    ... grayscale_output_image="grayscale.nii.gz",
    ... color_output_image="color.nii.gz") #doctest: +NORMALIZE_WHITESPACE
    pos_slice_preprocess --inputFilename input.nii.gz -g grayscale.nii.gz -r color.nii.gz

    >>> p=alignment_preprocessor_wrapper(input_image="i.nii.gz",
    ... grayscale_output_image="g.nii.gz",
    ... color_output_image="c.nii.gz")
    >>> p #doctest: +ELLIPSIS
    <__main__.alignment_preprocessor_wrapper object at 0x...>

    Checking default parameteres values:

    >>> print alignment_preprocessor_wrapper._parameters['input_image']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['grayscale_output_image']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['color_output_image']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['registration_roi']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['registration_resize']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['registration_color']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['median_filter_radius']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['invert_grayscale']
    <BLANKLINE>

    >>> print alignment_preprocessor_wrapper._parameters['invert_multichannel']
    <BLANKLINE>

    Checking robustness of the parameters dictionary:

    >>> p.updateParameters({"parameter_that_does_not_exist":0.5})
    Traceback (most recent call last):
    KeyError: 'parameter_that_does_not_exist'

    >>> print p.updateParameters({"median_filter_radius" : [2,2]}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_preprocess --inputFilename i.nii.gz -g g.nii.gz -r c.nii.gz --medianFilterRadius 2 2

    >>> print p.updateParameters({"median_filter_radius" : [2,2],
    ... 'invert_grayscale':True,
    ... 'invert_multichannel':True,
    ... 'registration_color': 'green'}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_preprocess --inputFilename i.nii.gz -g g.nii.gz -r c.nii.gz --registrationColorChannel green --medianFilterRadius 2 2 --invertSourceImage --invertMultichannelImage

    >>> print p.updateParameters({"median_filter_radius" : [2,2],
    ... 'invert_grayscale':False,
    ... 'invert_multichannel':False,
    ... 'registration_color': 'red'}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_preprocess --inputFilename i.nii.gz -g g.nii.gz -r c.nii.gz --registrationColorChannel red --medianFilterRadius 2 2 --invertSourceImage --invertMultichannelImage

    >>> print p.updateParameters({"median_filter_radius" : None,
    ... 'invert_grayscale':None,
    ... 'invert_multichannel': None,
    ... 'registration_color': 'red'}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_preprocess --inputFilename i.nii.gz -g g.nii.gz -r c.nii.gz --registrationColorChannel red

    >>> print p.updateParameters({"median_filter_radius" : 2})
    Traceback (most recent call last):
    TypeError: argument 2 to map() must support iteration

    >>> print p.updateParameters({"median_filter_radius" : None,
    ... 'invert_grayscale' : None,
    ... 'invert_multichannel' : None,
    ... 'registration_color': None}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_preprocess --inputFilename i.nii.gz -g g.nii.gz -r c.nii.gz
    """

    _template = """pos_slice_preprocess \
                  --inputFilename {input_image} \
                  {grayscale_output_image} {color_output_image} \
                  {registration_roi} {registration_resize} \
                  {registration_color} \
                  {median_filter_radius} \
                  {invert_grayscale} {invert_multichannel}"""

    _parameters = {
        'input_image' : filename_parameter('input_image', None),
        'grayscale_output_image': filename_parameter('-g', None, str_template="{_name} {_value}"),
        'color_output_image': filename_parameter('-r', None, str_template="{_name} {_value}"),
        'registration_roi': list_parameter('registrationROI', None, str_template="--{_name} {_list}"),
        'registration_resize': value_parameter('registrationResize', None, str_template="--{_name} {_value}"),
        'registration_color': string_parameter('registrationColorChannel', None, str_template="--{_name} {_value}"),
        'median_filter_radius': list_parameter('medianFilterRadius', None, str_template="--{_name} {_list}"),
        'invert_grayscale': switch_parameter('invertSourceImage', False, str_template="--{_name}"),
        'invert_multichannel': switch_parameter('invertMultichannelImage', False, str_template="--{_name}")}


class command_warp_rgb_slice(generic_wrapper):
    """
    A flexible RGB image __affine__ reslice wrapper. The wrapper is designed to
    work solely with the 8bit, three channel (RGB) images. Since the input
    image type is fixed, the output image type is the same as the input image
    type.

    :param dimension: (optional) Dimension of the transformation (2 or 3)
    :type dimension: int

    :param background: (optional) default background color applied during image reslicing.
    :type background: float

    :param interpolation: (optional) Image intrerplation method. The allowed values are:
        Cubic Gaussian Linear Nearest Sinc cubic gaussian linear nearest sinc.
        Please consult the Convert3D online documentation for the details of
        the image interpolation methods:
        http://www.itksnap.org/pmwiki/pmwiki.php?n=Convert3D.Documentation
    :type interpolation: str

    :param reference_image: (required) Filename of the reference image used ruring the
        resampling process. The prefereble type of the image if of course Niftii
        format.
    :type reference_image: str

    :param moving_image: (required) Image to be resliced.
    :type moving_image: str

    :param transformation: (required) Affine transformation to be applied. ITKv3 affine
        transformation file (a human readable text file) is required. Other types
        of transformations are not well supproted.
    :type transformation: str

    :param region_origin: (optional) If subregion extraction after the
        reslicing is to be done, this option determines the origin (in voxels) of
        the region to extract.
    :type region_origin: (int, int)

    :param region_size: (optional) If subregion extraction after the
        reslicing is to be done, this option determines the size (in voxels) of
        the region to extract.
    :type region_size: (int, int)

    :param inversion_flag: (optional) True / False. Inverts the image after
        reslicing. Note that this option requires the image type that exactly meets
        the script specification - three channel, 8bit RGB image. Will not work for
        any other type of the image.
    :type inversion_flag: bool

    Doctests
    --------

    >>> command_warp_rgb_slice
    <class '__main__.command_warp_rgb_slice'>

    >>> command_warp_rgb_slice() #doctest: +ELLIPSIS
    <__main__.command_warp_rgb_slice object at 0x...>

    >>> print command_warp_rgb_slice() #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose -as ref -clear \
        -mcs -as b -pop -as g -pop -as r \
        -push ref -push r -reslice-itk -as rr -type uchar -clear \
        -push ref -push g -reslice-itk -as rg -type uchar -clear \
        -push ref -push b -reslice-itk -as rb -type uchar -clear \
        -push rr -push rg -push rb -omc 3

    >>> print command_warp_rgb_slice(moving_image='moving.nii.gz',
    ... reference_image='reference.nii.gz',
    ... output_image='output.nii.gz',
    ... transformation='transformation.txt') #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose reference.nii.gz -as ref -clear \
        -mcs moving.nii.gz -as b -pop -as g -pop -as r \
        -push ref -push r -reslice-itk transformation.txt -as rr -type uchar -clear \
        -push ref -push g -reslice-itk transformation.txt -as rg -type uchar -clear \
        -push ref -push b -reslice-itk transformation.txt -as rb -type uchar -clear \
        -push rr -push rg -push rb -omc 3 output.nii.gz

    >>> print command_warp_rgb_slice(moving_image='moving.nii.gz',
    ... reference_image='reference.nii.gz', output_image='output.nii.gz',
    ... transformation='transformation.txt', background=255,
    ... region_origin=[20,20], region_size=[100,100],
    ... inversion_flag=True) #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose -background 255 reference.nii.gz -as ref -clear \
        -mcs moving.nii.gz -as b -pop -as g -pop -as r \
        -push ref -push r -reslice-itk transformation.txt \
          -region 20x20vox 100x100vox -scale -1 -shift 255 -type uchar -as rr -type uchar -clear \
        -push ref -push g -reslice-itk transformation.txt \
          -region 20x20vox 100x100vox -scale -1 -shift 255 -type uchar -as rg -type uchar -clear \
        -push ref -push b -reslice-itk transformation.txt \
          -region 20x20vox 100x100vox -scale -1 -shift 255 -type uchar -as rb -type uchar -clear \
        -push rr -push rg -push rb -omc 3 output.nii.gz
    """

    _template = "c{dimension}d -verbose {background} {interpolation}\
       {reference_image} -as ref -clear \
       -mcs {moving_image}\
       -as b \
       -pop -as g \
       -pop -as r \
       -push ref -push r -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rr -type uchar -clear \
       -push ref -push g -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rg -type uchar -clear \
       -push ref -push b -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rb -type uchar -clear \
       -push rr -push rg -push rb -omc 3 {output_image}"

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'background': pos_parameters.value_parameter('background', None, '-{_name} {_value}'),
        'interpolation': pos_parameters.value_parameter('interpolation', None, '-{_name} {_value}'),
        'reference_image': pos_parameters.filename_parameter('reference_image', None),
        'moving_image': pos_parameters.filename_parameter('moving_image', None),
        'transformation': pos_parameters.filename_parameter('transformation', None),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'region_origin' : pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size' : pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
        'inversion_flag' : pos_parameters.boolean_parameter('inversion_flag', None, str_template=' -scale -1 -shift 255 -type uchar'),
    }


class command_warp_grayscale_image(generic_wrapper):
    """
    A special instance of reslice grayscale image dedicated for the sequential
    alignment script.

    :param dimension: (optional) Dimension of the transformation (2 or 3)
    :type dimension: int

    :param background: (optional) default background color applied during image reslicing.
    :type background: float

    :param interpolation: (optional) Image intrerplation method. The allowed values are:
        Cubic Gaussian Linear Nearest Sinc cubic gaussian linear nearest sinc.
        Please consult the Convert3D online documentation for the details of
        the image interpolation methods:
        http://www.itksnap.org/pmwiki/pmwiki.php?n=Convert3D.Documentation
    :type interpolation: str

    :param reference_image: (required) Filename of the reference image used ruring the
        resampling process. The prefereble type of the image if of course Niftii
        format.
    :type reference_image: str

    :param moving_image: (required) Image to be resliced.
    :type moving_image: str

    :param transformation: (required) Affine transformation to be applied. ITKv3 affine
        transformation file (a human readable text file) is required. Other types
        of transformations are not well supproted.
    :type transformation: str

    :param region_origin: (optional) If subregion extraction after the
        reslicing is to be done, this option determines the origin (in voxels) of
        the region to extract.
    :type region_origin: (int, int)

    :param region_size: (optional) If subregion extraction after the
        reslicing is to be done, this option determines the size (in voxels) of
        the region to extract.
    :type region_size: (int, int)

    Doctests
    --------

    >>> command_warp_grayscale_image
    <class '__main__.command_warp_grayscale_image'>

    >>> command_warp_grayscale_image() #doctest: +ELLIPSIS
    <__main__.command_warp_grayscale_image object at 0x...>

    >>> print command_warp_grayscale_image() #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose -as ref -clear -as moving -push ref -push moving \
    -reslice-itk -type uchar -o

    >>> p = command_warp_grayscale_image(reference_image='ref.nii.gz',
    ... moving_image='moving.nii.gz', transformation='transf.txt',
    ... output_image='output.nii.gz') #doctest: +NORMALIZE_WHITESPACE
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose ref.nii.gz -as ref -clear moving.nii.gz -as moving \
    -push ref -push moving -reslice-itk transf.txt \
    -type uchar -o output.nii.gz

    >>> p.updateParameters({'background': 255, 'interpolation': 'nn'}) #doctest: +ELLIPSIS
    <__main__.command_warp_grayscale_image object at 0x...>
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose -background 255 -interpolation nn ref.nii.gz -as ref -clear\
    moving.nii.gz -as moving -push ref -push moving -reslice-itk transf.txt \
    -type uchar -o output.nii.gz

    >>> p.updateParameters({'region_origin': [10,10,10],
    ... 'region_size': [50,50,50], 'dimension': 3}) #doctest: +ELLIPSIS
    <__main__.command_warp_grayscale_image object at 0x...>
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    c3d -verbose -background 255 -interpolation nn ref.nii.gz -as ref -clear \
    moving.nii.gz -as moving -push ref -push moving -reslice-itk transf.txt \
    -region 10x10x10vox 50x50x50vox -type uchar -o output.nii.gz
    """

    _template = "c{dimension}d -verbose {background} {interpolation}\
        {reference_image} -as ref -clear \
        {moving_image} -as moving \
        -push ref -push moving -reslice-itk {transformation} \
        {region_origin} {region_size} \
        -type uchar -o {output_image}"

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'background': pos_parameters.value_parameter('background', None, '-{_name} {_value}'),
        'interpolation': pos_parameters.value_parameter('interpolation', None, '-{_name} {_value}'),
        'reference_image': pos_parameters.filename_parameter('reference_image', None),
        'moving_image': pos_parameters.filename_parameter('moving_image', None),
        'transformation': pos_parameters.filename_parameter('transformation', None),
        'region_origin' : pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size' : pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
        'output_image': pos_parameters.filename_parameter('output_image', None),
    }


class image_similarity_wrapper(generic_wrapper):
    """
    Calculates image similarity between two grayscale images using a provided
    similarity metric and applying optional affine transformation to the moving image.

    Ok, a few words of explanation here: This wrapper is a bit atypical since
    there are two templates. One template is used when a affine transformation
    is provided, the other command template is used when the is no affine
    transformation provided. The selection between templates is based on the
    value of the transformation parameters. This wrapper used a hack and
    overloads the __str__ function. This is a pretty unusual solution but I
    like it and probably will use it more.

    >>> print image_similarity_wrapper
    <class '__main__.image_similarity_wrapper'>

    >>> image_similarity_wrapper() #doctest: +ELLIPSIS
    <__main__.image_similarity_wrapper object at 0x...>

    >>> print image_similarity_wrapper() #doctest: +NORMALIZE_WHITESPACE
    c2d -ncor | cut -f3 -d' '

    # Verify initial parameters values

    >>> str(image_similarity_wrapper._parameters['dimension']) == '2'
    True

    >>> str(image_similarity_wrapper._parameters['reference_image']) == ''
    True

    >>> str(image_similarity_wrapper._parameters['moving_image']) == ''
    True

    >>> str(image_similarity_wrapper._parameters['metric']) == '-ncor'
    True

    >>> str(image_similarity_wrapper._parameters['affine_transformation']) == ''
    True

    Initial parameters are verified.

    >>> print image_similarity_wrapper(reference_image='r.nii.gz', moving_image='m.nii.gz')
    c2d r.nii.gz m.nii.gz -ncor | cut -f3 -d' '

    >>> print image_similarity_wrapper(reference_image='r.nii.gz', moving_image='m.nii.gz', dimension=3)
    c3d r.nii.gz m.nii.gz -ncor | cut -f3 -d' '

    # And now execution with a affine transformation

    >>> print image_similarity_wrapper(reference_image='r.nii.gz',
    ... moving_image='m.nii.gz', metric='mmi',
    ... affine_transformation='affine.txt')
    c2d r.nii.gz m.nii.gz -reslice-itk affine.txt r.nii.gz -mmi | cut -f3 -d' '

    >>> p = image_similarity_wrapper(reference_image='r.nii.gz',
    ... moving_image='m.nii.gz', affine_transformation='affine.txt')
    >>> print p
    c2d r.nii.gz m.nii.gz -reslice-itk affine.txt r.nii.gz -ncor | cut -f3 -d' '

    >>> print p.updateParameters({'affine_transformation' : None})
    c2d r.nii.gz m.nii.gz -ncor | cut -f3 -d' '

    >>> print p.updateParameters({'metric' : 'nmi'})
    c2d r.nii.gz m.nii.gz -nmi | cut -f3 -d' '

    >>> print p.updateParameters({'metric' : 'msq'})
    c2d r.nii.gz m.nii.gz -msq | cut -f3 -d' '

    >>> print p.updateParameters({'affine_transformation' : 'affine.txt'})
    c2d r.nii.gz m.nii.gz -reslice-itk affine.txt r.nii.gz -msq | cut -f3 -d' '
    """

    _template_affine = """c{dimension}d {reference_image} {moving_image} \
        -reslice-itk {affine_transformation} {reference_image} \
        {metric} | cut -f3 -d' '"""
    _template_no_affine = """c{dimension}d {reference_image} {moving_image} \
        {metric} | cut -f3 -d' '"""

    def __str__(self):
        if self.p['affine_transformation'].value is not None:
            self._template = self._template_affine
        else:
            self._template = self._template_no_affine
        return super(self.__class__, self).__str__()

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'reference_image': filename_parameter('reference_image', None),
        'moving_image': filename_parameter('moving_image', None),
        'metric': string_parameter('metric', 'ncor', str_template='-{_value}'),
        'affine_transformation': filename_parameter('affine_transformation', None)}

class split_multichannel_image(generic_wrapper):
    """
    Split the individual image into its components. By default the images are
    converted to the uchar type.

    Doctests
    --------

    >>> split_multichannel_image
    <class '__main__.split_multichannel_image'>

    >>> split_multichannel_image() #doctest: +ELLIPSIS
    <__main__.split_multichannel_image object at 0x...>

    >>> print split_multichannel_image() #doctest: +NORMALIZE_WHITESPACE
    c2d -mcs -foreach -type uchar -endfor -oo

    Verify initial parameters values

    >>> str(split_multichannel_image._parameters['dimension']) == '2'
    True

    >>> str(split_multichannel_image._parameters['input_image']) == ''
    True

    >>> str(split_multichannel_image._parameters['output_type']) == '-type uchar'
    True

    >>> str(split_multichannel_image._parameters['output_components']) == ''
    True

    >>> print split_multichannel_image(input_image='i.nii.gz',
    ... output_type='o.nii.gz',
    ... output_components = ['o1.nii.gz', 'o2.nii.gz', 'o3.nii.gz']) #doctest: +NORMALIZE_WHITESPACE
    c2d -mcs i.nii.gz -foreach -type o.nii.gz -endfor -oo o1.nii.gz o2.nii.gz o3.nii.gz

    >>> p = split_multichannel_image(input_image='i.nii.gz')
    >>> print p
    c2d -mcs i.nii.gz -foreach -type uchar -endfor -oo

    >>> print p.updateParameters({'output_type': 'ushort',
    ... 'output_components': ['a.nii.gz', 'b.nii.gz', 'c.nii.gz']})
    c2d -mcs i.nii.gz -foreach -type ushort -endfor -oo a.nii.gz b.nii.gz c.nii.gz

    >>> print p.updateParameters({'dimension': 3})
    c3d -mcs i.nii.gz -foreach -type ushort -endfor -oo a.nii.gz b.nii.gz c.nii.gz
    """

    _template = """c{dimension}d -mcs {input_image} -foreach {output_type} -endfor \
        -oo {output_components}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_type': pos_parameters.string_parameter('output_type', 'uchar', str_template='-type {_value}'),
        'output_components': pos_parameters.list_parameter('output_components', [], str_template='{_list}')
        }


class merge_components(generic_wrapper):
    """
    Merges the individual components of the multichannel image into actual
    multichannel image. The individual components are deleted afterwards.

    >>> merge_components
    <class '__main__.merge_components'>

    >>> merge_components() #doctest: +ELLIPSIS
    <__main__.merge_components object at 0x...>

    >>> print merge_components()
    c2d -foreach -type uchar -endfor -omc 3 ; rm -rfv ;


    Verify initial parameters values

    >>> str(merge_components._parameters['dimension']) == '2'
    True

    >>> str(merge_components._parameters['input_images']) == ''
    True

    >>> str(merge_components._parameters['region_origin']) == ''
    True

    >>> str(merge_components._parameters['region_size']) == ''
    True

    >>> str(merge_components._parameters['output_type']) == '-type uchar'
    True

    >>> str(merge_components._parameters['components_no']) == '3'
    True

    >>> str(merge_components._parameters['output_image']) == ''
    True

    >>> str(merge_components._parameters['other_files_remove']) == ''
    True


    Testing individual parameters

    >>> print merge_components(dimension=3)
    c3d -foreach -type uchar -endfor -omc 3 ; rm -rfv ;

    >>> print merge_components(input_images=['o1.nii.gz', 'o2.nii.gz',
    ... 'o3.nii.gz']) #doctest: +NORMALIZE_WHITESPACE
    c2d o1.nii.gz o2.nii.gz o3.nii.gz -foreach -type uchar -endfor -omc 3 ;\
    rm -rfv o1.nii.gz o2.nii.gz o3.nii.gz ;

    >>> print merge_components(region_origin=[10, 20, 30])
    c2d -foreach -region 10x20x30vox -type uchar -endfor -omc 3 ; rm -rfv ;

    >>> print merge_components(region_size=[1, 2, 3])
    c2d -foreach 1x2x3vox -type uchar -endfor -omc 3 ; rm -rfv ;

    >>> print merge_components(output_type='ushort')
    c2d -foreach -type ushort -endfor -omc 3 ; rm -rfv ;

    >>> print merge_components(components_no=4)
    c2d -foreach -type uchar -endfor -omc 4 ; rm -rfv ;

    >>> print merge_components(output_image='output.nii.gz')
    c2d -foreach -type uchar -endfor -omc 3 output.nii.gz; rm -rfv ;

    >>> print merge_components(other_files_remove=['some_othe_file.nii.gz'])
    c2d -foreach -type uchar -endfor -omc 3 ; rm -rfv some_othe_file.nii.gz;


    And all of them combined

    >>> print merge_components(dimension=2, region_origin=[10, 20, 30],
    ... region_size=[1, 2, 3], output_type='float', components_no=4,
    ... output_image='output.nii.gz', other_files_remove=['a_file.nii.gz']) #doctest: +NORMALIZE_WHITESPACE
    c2d -foreach -region 10x20x30vox 1x2x3vox -type float -endfor \
    -omc 4 output.nii.gz; rm -rfv a_file.nii.gz;
    """

    _template = """c{dimension}d {input_images} \
        -foreach {region_origin} {region_size} {output_type} -endfor \
        -omc {components_no} {output_image}; rm -rfv {input_images} {other_files_remove};"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_images': pos_parameters.list_parameter('input_images', [], str_template='{_list}'),
        'region_origin' : pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size' : pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
        'output_type': pos_parameters.string_parameter('output_type', 'uchar', str_template='-type {_value}'),
        'components_no' : pos_parameters.value_parameter('components_no', 3),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'other_files_remove': pos_parameters.list_parameter('other_files_remove', [], str_template='{_list}')
        }


if __name__ == '__main__':
    import doctest
    doctest.testmod()
