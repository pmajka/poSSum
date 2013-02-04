import os
import copy

"""
pos parameters
"""


class generic_parameter(object):
    """
    """
    _str_template = None

    def __init__(self, name, value=None, str_template=None):
        
        # Obligatory
        self.name = name
        
        # Initialize default value to None. If any no-None value is provided
        # override the default one.
        self._value = None
        if value:
            self.value = value
        
        # Override default serialization template if non-None template is
        # provided.
        if str_template:
            self._str_template = str_template

    def _serialize(self):
        raise NotImplementedError, "Reimplement this method in a subclass"

    def __str__(self):
        return self._serialize()

    def _validate(self):
        raise NotImplementedError, "Reimplement this method in a subclass"

    def _set_value(self, value):
        self._value = value

    def _get_value(self):
        return self._value

    def _set_str_template(self, value):
        self._str_template = value

    def _get_str_template(self):
        return self._str_template

    def _set_name(self, value):
        self._name = value

    def _get_name(self):
        return self._name

    value = property(_get_value, _set_value)
    template = property(_get_str_template, _set_str_template)
    name = property(_get_name, _set_name)


class switch_parameter(generic_parameter):
    """
    >>> p=switch_parameter('a_switch', False, "--{_name}")
    >>> p #doctest: +ELLIPSIS
    <__main__.switch_parameter object at 0x...>

    >>> print p
    <BLANKLINE>

    >>> p.value = True
    >>> p.name = 'something'
    >>> print p
    --something

    >>> p.name = 'sth'
    >>> print p
    --sth

    >>> p.template
    '--{_name}'

    >>> p.template = '--{_value} --{_name}'
    >>> print p
    --True --sth
    """

    def _serialize(self):
        if self.value is not None:
            return self._str_template.format(**self.__dict__)
        else:
            return ""


class string_parameter(generic_parameter):
    """
    >>> p=string_parameter('a_name')

    >>> p #doctest: +ELLIPSIS
    <__main__.string_parameter object at 0x...>

    >>> print p
    <BLANKLINE>

    >>> p.value

    >>> p.value = "a_value"

    >>> print p
    a_value

    >>> del p
    >>> p=string_parameter('a_name', value="a_value")
    >>> print p
    a_value

    >>> del p
    >>> p=string_parameter('a_name', value="a_value")
    >>> print p
    a_value

    >>> p=string_parameter('a_name', value="a_value", str_template="__{_value}__ __{_name}__")
    >>> print p
    __a_value__ __a_name__
    """
    _str_template = "{_value}"

    def _serialize(self):
        if self.value is not None:
            return self._str_template.format(**self.__dict__)
        else:
            return ""


class filename_parameter(string_parameter):
    """
    This class is designed to be used as a filename.
    When creating filename parameter this class should be used instead of generic class :class:`string_parameter`.
    """
    _str_template = "{_value}"


class value_parameter(string_parameter):
    """
    This class sould be used to handle any string parameter. This class should be used instead
    """
    _str_template = "{_value}"


class list_parameter(generic_parameter):
    """

    A generic class for storing list parameters. The class accepts a list as a
    value.  During serialization, the list is mapped to string and joined with a
    delimiter. The default delimiter is a space. Note that only strings can be
    delimiters. Passing other types (such as ints, floats or other lists) will
    cause exceptions.

    >>> p=list_parameter()
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 arguments (1 given)
    
    >>> p=list_parameter(value=[1,2,3])
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 non-keyword arguments (1 given)

    >>> p=list_parameter(name='test')
    >>> p #doctest: +ELLIPSIS
    <__main__.list_parameter object at 0x...>

    >>> p=list_parameter(name='test', value=[1,2,3,4])
    >>> print p
    1 2 3 4

    >>> p.name
    'test'
    >>> p.value
    [1, 2, 3, 4]
    >>> p._delimiter
    ' '

    >>> p._delimiter='-'
    >>> print p
    1-2-3-4

    >>> p._delimiter=str
    >>> print p
    Traceback (most recent call last):
    TypeError: descriptor 'join' requires a 'str' object but received a 'list'

    >>> p._delimiter=9
    >>> print p
    Traceback (most recent call last):
    AttributeError: 'int' object has no attribute 'join'
    
    """
    _str_template = "{_list}"
    _delimiter = " "

    def _serialize(self):
        if self.value:
            self._list = self._delimiter.join(map(str, self.value))
            return self._str_template.format(**self.__dict__)
        else:
            return ""


class vector_parameter(list_parameter):
    """
    A specialized class for holding lists which are intended to be a vector.
    A default delimiter for this class is an "x" character. Otherwise it is a regular
    :class:`list_parameter`
    
    >>> p=vector_parameter('number-of-iterations', [10000,10000,10000], "--{_name} {_list}")
    >>> p #doctest: +ELLIPSIS
    <__main__.vector_parameter object at 0x...>

    >>> print p
    --number-of-iterations 10000x10000x10000

    >>> p.name
    'number-of-iterations'

    >>> p.template
    '--{_name} {_list}'

    >>> p._list
    '10000x10000x10000'

    >>> p.name = 'any_name'
    >>> print p
    --any_name 10000x10000x10000

    >>> p.value
    [10000, 10000, 10000]
    >>> p.value = (0,0,0,0)
    >>> print p
    --any_name 0x0x0x0

    """
    _delimiter = 'x'


class ants_specific_parameter(generic_parameter):
    """
    This class cannot be instantized. Use one of the subclasses instead.
    """
    _switch = None

    def _serialize(self):
        meaning = self.value[0]
        values  = self.value[1]

        retStr = " "+ self._switch +" " + meaning + "["
        retStr+= ",".join(map(str, values))
        retStr+="] "

        return retStr


class ants_transformation_parameter(ants_specific_parameter):
    """
    >>> ants_transformation_parameter
    <class '__main__.ants_transformation_parameter'>

    >>> p=ants_transformation_parameter(value=['Gauss',(0,0)])
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 non-keyword arguments (1 given)

    >>> p=ants_transformation_parameter('test', value=['Gauss',(0,0)])
    >>> p #doctest: +ELLIPSIS
    <__main__.ants_transformation_parameter object at 0x...>

    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -t Gauss[0,0]

    >>> p.value=['Gauss', (1.0, 1)]
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -t Gauss[1.0,1]

    >>> p.value=['reg_type', (1.0, 1)]
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -t reg_type[1.0,1]

    >>> p._switch
    '-t'

    """
    _switch = '-t'


class ants_regularization_parameter(ants_specific_parameter):
    """
    >>> ants_regularization_parameter
    <class '__main__.ants_regularization_parameter'>
    
    >>> p=ants_regularization_parameter()
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 arguments (1 given)
    
    >>> print ants_regularization_parameter('a_parameter')
    Traceback (most recent call last):
    TypeError: 'NoneType' object is unsubscriptable
    
    >>> print ants_regularization_parameter(value=['s'])
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 non-keyword arguments (1 given)
    
    >>> print ants_regularization_parameter('a_parameter', value=[9,0])
    Traceback (most recent call last):
    TypeError: cannot concatenate 'str' and 'int' objects
    
    >>> print ants_regularization_parameter('a_parameter', value=['s'])
    Traceback (most recent call last):
    IndexError: list index out of range

    >>> p=ants_regularization_parameter('a_parameter', value=['s',(2,2)])
    >>> p #doctest: +ELLIPSIS
    <__main__.ants_regularization_parameter object at 0x...>
    
    >>> p=ants_regularization_parameter('a_parameter', value=['Gauss',(2,2)])
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -r Gauss[2,2]

    >>> p.name
    'a_parameter'

    >>> p.name='xxxx'
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -r Gauss[2,2]

    >>> p.value
    ['Gauss', (2, 2)]

    >>> p.value=['Regularization', (0.0, 0.2)]
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -r Regularization[0.0,0.2]

    >>> p._switch
    '-r'
    """
    _switch = '-r'


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
        replacement = dict(map(lambda (k,v): (k, str(v)), self.p.iteritems()))
        return self._template.format(**replacement)
    
    def __call__(self, *args, **kwargs):
        command = str(self)
        os.system(command)
        
        execution = {'port': {}}
        if hasattr(self, '_io_pass'):
            for k, v in self._io_pass.iteritems():
                execution['port'][v] = self.p[k]
        return execution
    
    def updateParameters(self, parameters):
        for (name, value) in parameters.items():
            self.p[name].value = value
        return self


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

    _parameters = {\
            'metric' : string_parameter('metric', 'CC'),
            'fixed_image' : filename_parameter('fixed_image', None),
            'moving_image': filename_parameter('moving_image', None),
            'weight'      : value_parameter('weight', 1),
            'parameter'   : value_parameter('parameter', 4)
            }

    def _get_value(self):
        return str(self)

    def _set_value(self, value):
        pass

    value = property(_get_value, _set_value)


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

    _parameters = { \
            'dimension'      : value_parameter('dimension', 2),
            'verbose'        : switch_parameter('verbose', True, str_template = '--{_name} {_value}'),
            'transformation' : ants_transformation_parameter('transformation', ('SyN', [0.25])),
            'regularization' : ants_regularization_parameter('regularization', ('Gausas', (3.0, 1.0))),
            'outputNaming'   : filename_parameter('output-naming', None, str_template = '--{_name} {_value}'),
            'iterations'     : vector_parameter('number-of-iterations', (5000,)*4, '--{_name} {_list}'),
            'affineIterations'      : vector_parameter('number-of-affine-iterations', (10000,)*5, '--{_name} {_list}'),
            'rigidAffine'    : switch_parameter('rigid-affine', True, str_template = '--{_name} {_value}'),
            'continueAffine' : switch_parameter('continue-affine', True, str_template = '--{_name} {_value}'),
            'useNN'          : switch_parameter('use-NN', False, str_template = '--{_name}'),
            'histogramMatching' : switch_parameter('use-Histogram-Matching', True, str_template = '--{_name} {_value}'),
            'allMetricsConverge': switch_parameter('use-all-metrics-for-convergence', True, str_template = '--{_name} {_value}'),
            'initialAffine'     : filename_parameter('initial-affine', None, str_template = '--{_name} {_value}'),
            'fixedImageInitialAffine': filename_parameter('fixed-image-initial-affine', None, str_template = '--{_name} {_value}'),
            'affineGradientDescent' : vector_parameter('affine-gradient-descent-option', None, '--{_name} {_value}'),
            'imageMetrics'          : list_parameter('image_to_image_metrics', [], '{_list}'),
            'maskImage'      : filename_parameter('mask-image', None, str_template = '--{_name} {_value}')
            }

    _io_pass = { \
            'dimension' : 'dimension'
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

    _parameters = { \
        'dimension'      : value_parameter('dimension', 2),
        'moving_image'  : filename_parameter('moving_image', None),
        'output_image'  : filename_parameter('output_image', None),
        'reference_image'  : filename_parameter('reference_image', None, str_template = '-R {_value}'),
        'useNN'            : switch_parameter('use-NN', None, str_template = '--{_name}'),
        'useBspline'       : switch_parameter('use-BSpline', None, str_template = '--{_name}'),
        'deformable_list'  : list_parameter('deformable_list', [], str_template = '{_list}'),
        'affine_list'  : list_parameter('affine_list', [], str_template = '{_list}')
                }

    _io_pass = { \
            'dimension'    : 'dimension',
            'output_image' : 'input_image'
            }


class ants_compose_multi_transform(generic_wrapper):
    """
    """
    _template = """ComposeMultiTransform {dimension} \
                  {output_image} \
                  {reference_image} \
                  {deformable_list} {affine_list}"""

    _parameters = { \
        'dimension'      : value_parameter('dimension', 2),
        'output_image'  : filename_parameter('output_image', None),
        'reference_image'  : filename_parameter('reference_image', None, str_template = '-R {_value}'),
        'deformable_list'  : list_parameter('deformable_list', [], str_template = '{_list}'),
        'affine_list'  : list_parameter('affine_list', [], str_template = '{_list}')
                }

    _io_pass = { \
            'dimension'    : 'dimension',
            'output_image' : 'input_image'
            }


class average_images(generic_wrapper):
    """
    """
    _template = """c{dimension}d  {input_images} -mean {output_type} -o {output_image}"""

    _parameters = { \
            'dimension'    : value_parameter('dimension', 2),
            'input_images' : list_parameter('input_images', [], str_template = '{_list}'),
            'output_image' : filename_parameter('output_image'),
            'output_type'  : string_parameter('output_type', 'uchar', str_template = '-type {_value}')
            }

    _io_pass = { \
            'dimension'    : 'dimension',
            'output_image' : 'input_image'
            }


class images_weighted_average(generic_wrapper):
    """
    """
    _template = """c{dimension}d  {input_images} -weighted-sum {weights} {output_type} -o {output_image}"""

    _parameters = { \
            'dimension'    : value_parameter('dimension', 2),
            'input_images' : list_parameter('input_images', [], str_template = '{_list}'),
            'weights'      : list_parameter('weights', [], str_template = '{_list}'),
            'output_image' : filename_parameter('output_image'),
            'output_type'  : string_parameter('output_type', 'uchar', str_template = '-type {_value}')
            }

    _io_pass = { \
            'dimension'    : 'dimension',
            'output_image' : 'input_image'
            }


class chain_affine_transforms(generic_wrapper):
    """
    """
    _template = """ComposeMultiTransform {dimension} {output_filename} {input_images}"""

    _parameters = { \
            'dimension'    : value_parameter('dimension', 2),
            'input_images' : list_parameter('input_images', [], str_template = '{_list}'),
            'output_filename' : filename_parameter('output_filename')
            }

    _io_pass = { \
            'dimension'    : 'dimension',
            'output_filename' : 'filename_filename'
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

    _parameters = { \
            'temp_volume_fn' : filename_parameter('temp_volume_fn', None),
            'output_volume_fn' : filename_parameter('output_volume_fn', None),
            'stack_mask' : filename_parameter('stack_mask', None),
            'permutation_order' : list_parameter('permutation_order', [0,2,1], str_template = '{_list}'),
            'orientation_code' : string_parameter('orientation_code', 'RAS'),
            'output_type'  : string_parameter('output_type', 'uchar'),
            'spacing' : list_parameter('spacing', [1.,1.,1.], str_template = '{_list}'),
            'origin' : list_parameter('origin', [0,0,0], str_template = '{_list}'),
            'interpolation' : string_parameter('interpolation', None, str_template = '--{_name} {_value}'),
            'resample' : list_parameter('resample', [], str_template = '--{_name} {_list}')
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

    _parameters = { \
            'stack_mask' : filename_parameter('stack_mask', None),
            'slice_start'  : value_parameter('slice_start', None),
            'slice_end'    : value_parameter('slice_end', None),
            'temp_volume_fn' : filename_parameter('temp_volume_fn', None),
            'permutation_order' : list_parameter('permutation_order', [0,2,1], str_template = '{_list}'),
            'orientation_code' : string_parameter('orientation_code', 'RAS'),
            'output_type'  : string_parameter('output_type', 'uchar'),
            'spacing' : list_parameter('spacing', [1.,1.,1.], str_template = '{_list}'),
            'origin' : list_parameter('origin', [0,0,0], str_template = '{_list}'),
            'interpolation' : string_parameter('interpolation', None, str_template = '--{_name} {_value}'),
            'resample' : list_parameter('resample', [], str_template = '--{_name} {_list}'),
            'output_volume_fn' : filename_parameter('output_volume_fn', None)
            }


class mkdir_wrapper(generic_wrapper):
    _template = """mkdir -p {dir_list}"""

    _parameters = { \
            'dir_list' : list_parameter('dir_list', [], str_template = '{_list}')
            }


class rmdir_wrapper(generic_wrapper):
    _template = """rm -rfv {dir_list}"""

    _parameters = { \
            'dir_list' : list_parameter('dir_list', [], str_template = '{_list}')
            }

if __name__ == '__main__':
    import doctest
    doctest.testmod()
