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
    <possum.pos_wrappers.generic_wrapper object at 0x...>

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
        stdout, stderr = sub.Popen(str(self), stdout=sub.PIPE,
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
    """
    A very simple ``touch`` bash command wrapper.

    :param files: A list of files to touch. Even if you're touching only a
                  single file you have to still pass it as a list.
    :type files: list of strings

    >>> touch_wrapper
    <class 'possum.pos_wrappers.touch_wrapper'>

    >>> touch_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.touch_wrapper object at 0x...>

    >>> print touch_wrapper()
    touch

    >>> p = touch_wrapper(files=['file1.txt'])
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.touch_wrapper object at 0x...>

    >>> print p
    touch file1.txt

    >>> p = touch_wrapper(files=['file1.txt', 'file2.txt'])
    >>> print p
    touch file1.txt file2.txt

    >>> print p.updateParameters({"files":[]})
    touch

    >>> print p.updateParameters({"files":"a_poorly_provided_parameter.txt"})
    touch a _ p o o r l y _ p r o v i d e d _ p a r a m e t e r . t x t

    >>> print p.updateParameters({"files":["f1.txt","f2.py", "f3.nii.gz"]})
    touch f1.txt f2.py f3.nii.gz

    >>> print p.updateParameters({"files":None})
    touch

    >>> print p.updateParameters({"files":True})
    Traceback (most recent call last):
    TypeError: argument 2 to map() must support iteration

    >>> print p.updateParameters({"files":2})
    Traceback (most recent call last):
    TypeError: argument 2 to map() must support iteration
    """

    _template = """touch {files}"""

    _parameters = {
        'files': list_parameter('files', [], str_template='{_list}'),
    }


class mkdir_wrapper(generic_wrapper):
    """
     A very simple ``mkdir`` bash command wrapper with default
     -p option.

    :param dir_list: A list of directories to to create. Even if you're creating
                  only a single directory you have to still pass it as a list.
    :type files: list of strings

    >>> mkdir_wrapper
    <class 'possum.pos_wrappers.mkdir_wrapper'>

    >>> mkdir_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.mkdir_wrapper object at 0x...>

    >>> print mkdir_wrapper()
    mkdir -p

    >>> p = mkdir_wrapper(dir_list=['dir1'])
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.mkdir_wrapper object at 0x...>

    >>> print p
    mkdir -p dir1

    >>> p = mkdir_wrapper(dir_list=['dir1', 'dir2'])
    >>> print p
    mkdir -p dir1 dir2

    >>> print p.updateParameters({"dir_list":[]})
    mkdir -p

    >>> print p.updateParameters({"dir_list":"a_poorly_provided_parameter"})
    mkdir -p a _ p o o r l y _ p r o v i d e d _ p a r a m e t e r

    >>> print p.updateParameters({"dir_list":["dir1","dir2", "dir"]})
    mkdir -p dir1 dir2 dir

    >>> print p.updateParameters({"dir_list":None})
    mkdir -p

    >>> print p.updateParameters({"dir_list":True})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pos_wrappers.py", line 46, in __str__
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_wrappers.py", line 46, in <lambda>
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_parameters.py", line 38, in __str__
        return self._serialize()
      File "pos_parameters.py", line 231, in _serialize
        self._list = self._delimiter.join(map(str, self.value))
    TypeError: argument 2 to map() must support iteration

    >>> print p.updateParameters({"dir_list":2})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pos_wrappers.py", line 46, in __str__
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_wrappers.py", line 46, in <lambda>
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_parameters.py", line 38, in __str__
        return self._serialize()
      File "pos_parameters.py", line 231, in _serialize
        self._list = self._delimiter.join(map(str, self.value))
    TypeError: argument 2 to map() must support iteration
    """

    _template = """mkdir -p {dir_list}"""

    _parameters = {
        'dir_list': list_parameter('dir_list', [], str_template='{_list}')
    }


class rmdir_wrapper(generic_wrapper):
    """
     A very simple ``rm`` bash command wrapper with default
     -rfv options.

    :param dir_list: A list of directories to remove. Even if you're removing
                  only a single directory you have to still pass it as a list.
    :type files: list of strings

    >>> rmdir_wrapper
    <class 'possum.pos_wrappers.rmdir_wrapper'>

    >>> rmdir_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.rmdir_wrapper object at 0x...>

    >>> print rmdir_wrapper()
    rm -rfv

    >>> p = rmdir_wrapper(dir_list=['dir1'])
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.rmdir_wrapper object at 0x...>

    >>> print p
    rm -rfv dir1

    >>> p = rmdir_wrapper(dir_list=['dir1', 'dir2'])
    >>> print p
    rm -rfv dir1 dir2

    >>> print p.updateParameters({"dir_list":[]})
    rm -rfv

    >>> print p.updateParameters({"dir_list":"a_poorly_provided_parameter"})
    rm -rfv a _ p o o r l y _ p r o v i d e d _ p a r a m e t e r

    >>> print p.updateParameters({"dir_list":["dir1","dir2", "dir"]})
    rm -rfv dir1 dir2 dir

    >>> print p.updateParameters({"dir_list":None})
    rm -rfv

    >>> print p.updateParameters({"dir_list":True})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pos_wrappers.py", line 46, in __str__
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_wrappers.py", line 46, in <lambda>
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_parameters.py", line 38, in __str__
        return self._serialize()
      File "pos_parameters.py", line 231, in _serialize
        self._list = self._delimiter.join(map(str, self.value))
    TypeError: argument 2 to map() must support iteration

    >>> print p.updateParameters({"dir_list":2})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pos_wrappers.py", line 46, in __str__
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_wrappers.py", line 46, in <lambda>
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_parameters.py", line 38, in __str__
        return self._serialize()
      File "pos_parameters.py", line 231, in _serialize
        self._list = self._delimiter.join(map(str, self.value))
    TypeError: argument 2 to map() must support iteration
    """


    _template = """rm -rfv {dir_list}"""

    _parameters = {
        'dir_list': list_parameter('dir_list', [], str_template='{_list}')
    }


class copy_wrapper(generic_wrapper):
    """
    A very simple ``cp`` bash command wrapper with default
     -rfv options.

    :param source: A list of files to copy. Even if you're copying
                  only a single you have to still pass the argument
                  as a list.
    :type files: list of strings

    :param target: A path to destination where you want to copy source(s)
    :type files: string

    >>> copy_wrapper
    <class 'possum.pos_wrappers.copy_wrapper'>

    >>> copy_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.copy_wrapper object at 0x...>

    >>> print copy_wrapper()
    cp -rfv

    >>> p = copy_wrapper(source=['source_file1'], target='destination_dir')
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.copy_wrapper object at 0x...>

    >>> print p
    cp -rfv source_file1 destination_dir

    >>> p = copy_wrapper(source=['source_file1', 'source_file2'], target='destination_dir')
    >>> print p
    cp -rfv source_file1 source_file2 destination_dir

    >>> print p.updateParameters({"source":[], "target":''})
    cp -rfv

    >>> print p.updateParameters({"source":"a_poorly_provided_parameter", "target":''})
    cp -rfv a _ p o o r l y _ p r o v i d e d _ p a r a m e t e r

    >>> print p.updateParameters({"source":["dir1","dir2", "dir"], "target":'destination_dir'})
    cp -rfv dir1 dir2 dir destination_dir

    >>> print p.updateParameters({"source":None, "target":None})
    cp -rfv

    >>> print p.updateParameters({"source":True, "target":True})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pos_wrappers.py", line 46, in __str__
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_wrappers.py", line 46, in <lambda>
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_parameters.py", line 38, in __str__
        return self._serialize()
      File "pos_parameters.py", line 231, in _serialize
        self._list = self._delimiter.join(map(str, self.value))
    TypeError: argument 2 to map() must support iteration

    >>> print p.updateParameters({"source":2, "target":2})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pos_wrappers.py", line 46, in __str__
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_wrappers.py", line 46, in <lambda>
        replacement = dict(map(lambda (k, v): (k, str(v)), self.p.iteritems()))
      File "pos_parameters.py", line 38, in __str__
        return self._serialize()
      File "pos_parameters.py", line 231, in _serialize
        self._list = self._delimiter.join(map(str, self.value))
    TypeError: argument 2 to map() must support iteration
    """
    _template = """cp -rfv {source} {target}"""

    _parameters = {
        'source': list_parameter('source', [], str_template='{_list}'),
        'target': value_parameter('target')
    }


class compress_wrapper(generic_wrapper):
    """
    A very simple ``tar`` bash command wrapper with default
     -cvvzf options.

    :param archive_filename: A pathname to archive you want to create.
    :type files: string

    :param pathname: A path to a source file which you want to compress.
    :type files: string

    >>> compress_wrapper
    <class 'possum.pos_wrappers.compress_wrapper'>

    >>> compress_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.compress_wrapper object at 0x...>

    >>> print compress_wrapper()
    tar -cvvzf .tgz

    >>> p = compress_wrapper(archive_filename='archive_file_name', \
                                pathname='file_to_compress')
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.compress_wrapper object at 0x...>

    >>> print p
    tar -cvvzf archive_file_name.tgz file_to_compress

    >>> p = compress_wrapper(archive_filename='', \
                        pathname='file_to_compress')
    >>> print p
    tar -cvvzf .tgz file_to_compress

    >>> print p.updateParameters({"archive_filename":'', "pathname":''})
    tar -cvvzf .tgz

    >>> print p.updateParameters({"archive_filename":None, "pathname":None})
    tar -cvvzf .tgz

    >>> print p.updateParameters({"archive_filename":True, "pathname":True})
    tar -cvvzf True.tgz True

    """

    _template = """tar -cvvzf {archive_filename}.tgz {pathname}"""

    _parameters = {
        'archive_filename': filename_parameter('archive_filename', None),
        'pathname': filename_parameter('pathname', None),
    }


class ants_jacobian(generic_wrapper):
    _template = """ANTSJacobian {dimension} {input_image} {output_naming}"""

    _parameters = {
        'dimension': value_parameter('dimension', 2),
        'input_image': filename_parameter('input_image', None),
        'output_naming': filename_parameter('output_naming', None),
    }


class ants_registration(generic_wrapper):
    """
    Wrapper for the Advanced Normalization Tools. Tested with the following
    ANTS versions:

        1. ANTs-1.9.v4-Linux
        2. ANTs-1.9.x-Linux

    >>> metric = ants_intensity_meric(fixed_image='f.nii.gz', moving_image='m.nii.gz')
    >>> wrapper = ants_registration(imageMetrics=[metric], outputNaming="test_")
    >>> wrapper() # doctest: +ELLIPSIS
    Executing: ...

    """

    _template = """ANTS {dimension} \
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
        'affineGradientDescent': vector_parameter('affine-gradient-descent-option', None, '--{_name} {_list}'),
        'imageMetrics': list_parameter('image_to_image_metrics', [], '{_list}'),
        'maskImage': filename_parameter('mask-image', None, str_template='--{_name} {_value}'),
        'miOption': vector_parameter('MI-option', None, str_template='--{_name} {_list}'),
        'affineMetricType': value_parameter('affine-metric-type', None, str_template='--{_name} {_value}')
    }

    _io_pass = {
        'dimension': 'dimension'
    }

    def __call__(self, *args, **kwargs):
        execution = super(self.__class__, self).__call__(*args, **kwargs)
        execution['port']['deformable_list'] = [str(self.p['outputNaming'].value) + 'Warp.nii.gz']

        if self.p['affineIterations']:
            execution['port']['affine_list'] = [str(self.p['outputNaming'].value) + 'Affine.txt']

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
    <class 'possum.pos_wrappers.ants_intensity_meric'>

    >>> ants_intensity_meric() #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_intensity_meric object at 0x...>

    >>> print ants_intensity_meric()
    -m CC[,,1,4]

    >>> p=ants_intensity_meric(fixed_image='fixed.nii.gz',moving_image='moving.nii.gz')
    >>> print p
    -m CC[fixed.nii.gz,moving.nii.gz,1,4]

    >>> print ants_intensity_meric(fixed_image='fixed.nii.gz',moving_image='moving.nii.gz',metric="XXX")
    -m XXX[fixed.nii.gz,moving.nii.gz,1,4]

    >>> p=ants_intensity_meric(fixed_image='fixed.nii.gz',moving_image='moving.nii.gz')
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_intensity_meric object at 0x...>
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
    <possum.pos_wrappers.ants_intensity_meric object at 0x...>

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

    >>> p.value = None

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
    <class 'possum.pos_wrappers.ants_point_set_estimation_metric'>

    >>> p=ants_point_set_estimation_metric()
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_point_set_estimation_metric object at 0x...>

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
    <possum.pos_wrappers.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,1.0]

    >>> p.updateParameters({"point_set_sigma":0.25}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,1.0,0.25]

    >>> p.updateParameters({"point_set_sigma":None, "boundary_points_only":True}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,1.0,True]

    >>> p.updateParameters({"point_set_percentage":0.1,"point_set_sigma":None, "boundary_points_only":True}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_point_set_estimation_metric object at 0x...>
    >>> print p
    -m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,0.1,True]

    >>> p.value = None
    >>> p.value == '-m PSE[fixed.nii.gz,moving.nii.gz,fixed_points.nii.gz,moving_points.nii.gz,0.5,0.1,True]'
    True

    """

    _template = "-m PSE[{fixed_image},{moving_image},{fixed_points},{moving_points},{weight},{point_set_percentage}{point_set_sigma}{boundary_points_only}]"

    _parameters = {
        'fixed_image': filename_parameter('fixed_image', None),
        'moving_image': filename_parameter('moving_image', None),
        'fixed_points': filename_parameter('fixed_points', None),
        'moving_points': filename_parameter('moving_points', None),
        'weight': value_parameter('weight', 1),
        'point_set_percentage': value_parameter('point_set_percentage', 1.0),
        'point_set_sigma': value_parameter('point_set_sigma', None,  str_template=',{_value}'),
        'boundary_points_only': boolean_parameter('boundary_points_only', False, str_template=',{_value}'),
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
    <class 'possum.pos_wrappers.ants_average_affine_transform'>

    >>> ants_average_affine_transform() #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_average_affine_transform object at 0x...>

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
    <possum.pos_wrappers.ants_average_affine_transform object at 0x...>
    >>> print str(p).strip()
    AverageAffineTransform 3 out.txt -R reference_affine.txt

    >>> p.updateParameters({"affine_list":["affine_1.txt", "affine_2.txt", "affine_3.txt"]}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_average_affine_transform object at 0x...>
    >>> print str(p).strip()
    AverageAffineTransform 3 out.txt -R reference_affine.txt affine_1.txt affine_2.txt affine_3.txt

    >>> p.updateParameters({"reference_affine_transform":None}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_average_affine_transform object at 0x...>
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
    >>> ants_compose_multi_transform
    <class 'possum.pos_wrappers.ants_compose_multi_transform'>

    >>> ants_compose_multi_transform() #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_compose_multi_transform object at 0x...>

    >>> str(ants_compose_multi_transform._parameters['dimension']) == '2'
    True

    >>> str(ants_compose_multi_transform._parameters['output_image']) == ''
    True

    >>> str(ants_compose_multi_transform._parameters['reference_image']) == ''
    True

    >>> str(ants_compose_multi_transform._parameters['deformable_list']) == ''
    True

    >>> str(ants_compose_multi_transform._parameters['affine_list']) == ''
    True

    >>> str(ants_compose_multi_transform()).strip() == 'ComposeMultiTransform 2'
    True

    >>> str(ants_compose_multi_transform(dimension=3)).strip() == 'ComposeMultiTransform 3'
    True

    >>> p = ants_compose_multi_transform(dimension=3, output_image="out.nii.gz") #doctest: +NORMALIZE_WHITESPACE
    >>> print str(p).strip()
    ComposeMultiTransform 3 out.nii.gz

    >>> p.updateParameters({"affine_list":["affine_1.txt", "affine_2.txt", "affine_3.txt"]}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_compose_multi_transform object at 0x...>
    >>> print str(p).strip()
    ComposeMultiTransform 3 out.nii.gz affine_1.txt affine_2.txt affine_3.txt

    >>> p.updateParameters({"reference_image":"reference_image.nii.gz"}) #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <possum.pos_wrappers.ants_compose_multi_transform object at 0x...>
    >>> print str(p).strip()
    ComposeMultiTransform 3 out.nii.gz -R reference_image.nii.gz affine_1.txt affine_2.txt affine_3.txt

    >>> p.updateParameters({"reference_image":None}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_compose_multi_transform object at 0x...>
    >>> print str(p).strip()
    ComposeMultiTransform 3 out.nii.gz affine_1.txt affine_2.txt affine_3.txt

    >>> p.updateParameters({"deformable_list":['warp_1.nii.gz','warp_2.nii.gz']}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_compose_multi_transform object at 0x...>
    >>> print str(p).strip()
    ComposeMultiTransform 3 out.nii.gz warp_1.nii.gz warp_2.nii.gz affine_1.txt affine_2.txt affine_3.txt
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
    >>> ants_average_images
    <class 'possum.pos_wrappers.ants_average_images'>

    >>> ants_average_images() #doctest: +ELLIPSIS
    <possum.pos_wrappers.ants_average_images object at 0x...>

    >>> str(ants_average_images._parameters['dimension']) == '2'
    True

    >>> str(ants_average_images._parameters['normalize']) == ''
    True

    >>> str(ants_average_images._parameters['input_images']) == ''
    True

    >>> str(ants_average_images._parameters['output_image']) == ''
    True

    >>> wrapper = ants_average_images()
    >>> wrapper() # doctest: +ELLIPSIS
    Executing: ...

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
    `pos_stack_sections` script.

    .. note:: There are two obligatory parameters: `stack_mask` and
              `output_volume_fn`.

    .. note:: Please be careful when stacking the input volume as `slice_start`
              - the parameters: `slice_start` `slice_end` `slice_step` has to
              go togeather.

    >>> stack_and_reorient_wrapper
    <class 'possum.pos_wrappers.stack_and_reorient_wrapper'>

    >>> stack_and_reorient_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.stack_and_reorient_wrapper object at 0x...>

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
    pos_stack_sections -i -o --permutation 0 1 2 \
        --orientation RAS --type uchar \
        --spacing 1.0 1.0 1.0 --origin 0 0 0

    >>> p=stack_and_reorient_wrapper()
    >>> p.updateParameters({"parameter_that_does_not_exist":0.5})
    Traceback (most recent call last):
    KeyError: 'parameter_that_does_not_exist'

    >>> print p.updateParameters({"stack_mask":"%04d.nii.gz"}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_sections -i %04d.nii.gz -o --permutation 0 1 2 \
        --orientation RAS --type uchar --spacing 1.0 1.0 1.0 \
        --origin 0 0 0

    >>> print p.updateParameters({"slice_start":"%04d.nii.gz",
    ... "slice_end" : 20, "slice_start" : 1, "slice_step":1}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_sections -i %04d.nii.gz -o --stacking-range 1 20 1 \
        --permutation 0 1 2  --orientation RAS  --type uchar \
        --spacing 1.0 1.0 1.0 --origin 0 0 0

    >>> print p.updateParameters({"output_volume_fn": "output.nii.gz"}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_sections -i %04d.nii.gz -o output.nii.gz \
      --stacking-range 1 20 1 --permutation 0 1 2 --orientation RAS \
      --type uchar --spacing 1.0 1.0 1.0 --origin 0 0 0

    >>> print p.updateParameters({"output_type": "ushort",
    ... "spacing" : [0.5, 0.5, 0.5], "origin" : [1, 1, 1],
    ... "interpolation" : "Cubic",
    ... "permutation_order" : [2, 1, 0], "resample": [0.5, 2.0, 3.0],
    ... "orientation_code" : "RAS"}) #doctest: +NORMALIZE_WHITESPACE
    pos_stack_sections -i %04d.nii.gz -o output.nii.gz --stacking-range 1 20 1\
      --permutation 2 1 0 --orientation RAS --type ushort\
      --spacing 0.5 0.5 0.5 --origin 1 1 1 --interpolation Cubic\
      --resample 0.5 2.0 3.0
    """

    _template = """pos_stack_sections \
        -i {stack_mask} \
        -o {output_volume_fn} \
        {slice_start} {slice_end} {slice_step} \
        --permutation {permutation_order} \
        {flip_axes} \
        --orientation {orientation_code} \
        --type {output_type} \
        --spacing {spacing} \
        --origin {origin} \
        {interpolation} {resample}"""

    _parameters = {
        'stack_mask': filename_parameter('stack_mask', None),
        'slice_start': value_parameter('stacking-range', None, str_template='--{_name} {_value}'),
        'slice_end': value_parameter('slice_end', None),
        'slice_step': value_parameter('slice_end', None),
        'output_volume_fn': filename_parameter('output_volume_fn', None),
        'permutation_order': list_parameter('permutation_order', [0, 1, 2], str_template='{_list}'),
        'orientation_code': string_parameter('orientation_code', 'RAS'),
        'flip_axes': list_parameter('flip', None, str_template='--{_name} {_list}'),
        'output_type': string_parameter('output_type', 'uchar'),
        'spacing': list_parameter('spacing', [1., 1., 1.], str_template='{_list}'),
        'origin': list_parameter('origin', [0, 0, 0], str_template='{_list}'),
        'interpolation': string_parameter('interpolation', None, str_template='--{_name} {_value}'),
        'resample': list_parameter('resample', [], str_template='--{_name} {_list}')
    }


class alignment_preprocessor_wrapper(generic_wrapper):
    """
    A wrapper for the `pos_preprocess_image` script. Since the script itself
    provides an extensive documentation, the detailed description of command
    line options is skipped in the wrapper's documentation.

    .. note::
        Use the following syntax when setting boolean parameters::

            >>> boolean_parameter = [None, True][int(value)] #doctest: +SKIP

        Yes, it is tricky and yes, is should be changed.


    >>> alignment_preprocessor_wrapper
    <class 'possum.pos_wrappers.alignment_preprocessor_wrapper'>

    >>> alignment_preprocessor_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.alignment_preprocessor_wrapper object at 0x...>

    >>> print alignment_preprocessor_wrapper() #doctest: +NORMALIZE_WHITESPACE
    pos_preprocess_image --input-image

    >>> print alignment_preprocessor_wrapper(input_image="input.nii.gz",
    ... grayscale_output_image="grayscale.nii.gz",
    ... color_output_image="color.nii.gz") #doctest: +NORMALIZE_WHITESPACE
    pos_preprocess_image --input-image input.nii.gz -g grayscale.nii.gz -r color.nii.gz

    >>> p=alignment_preprocessor_wrapper(input_image="i.nii.gz",
    ... grayscale_output_image="g.nii.gz",
    ... color_output_image="c.nii.gz")
    >>> p #doctest: +ELLIPSIS
    <possum.pos_wrappers.alignment_preprocessor_wrapper object at 0x...>

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
    pos_preprocess_image --input-image i.nii.gz -g g.nii.gz -r c.nii.gz --median-filter-radius 2 2

    >>> print p.updateParameters({"median_filter_radius" : [2,2],
    ... 'invert_grayscale':True,
    ... 'invert_multichannel':True,
    ... 'registration_color': 'green'}) #doctest: +NORMALIZE_WHITESPACE
    pos_preprocess_image --input-image i.nii.gz -g g.nii.gz -r c.nii.gz --color-channel green --median-filter-radius 2 2 --invert-source-image --invert-rgb-image

    >>> print p.updateParameters({"median_filter_radius" : [2,2],
    ... 'invert_grayscale':False,
    ... 'invert_multichannel':False,
    ... 'registration_color': 'red'}) #doctest: +NORMALIZE_WHITESPACE
    pos_preprocess_image --input-image i.nii.gz -g g.nii.gz -r c.nii.gz --color-channel red --median-filter-radius 2 2 --invert-source-image --invert-rgb-image

    >>> print p.updateParameters({"median_filter_radius" : None,
    ... 'invert_grayscale':None,
    ... 'invert_multichannel': None,
    ... 'registration_color': 'red'}) #doctest: +NORMALIZE_WHITESPACE
    pos_preprocess_image --input-image i.nii.gz -g g.nii.gz -r c.nii.gz --color-channel red

    >>> print p.updateParameters({"median_filter_radius" : 2})
    Traceback (most recent call last):
    TypeError: argument 2 to map() must support iteration

    >>> print p.updateParameters({"median_filter_radius" : None,
    ... 'invert_grayscale' : None,
    ... 'invert_multichannel' : None,
    ... 'registration_color': None}) #doctest: +NORMALIZE_WHITESPACE
    pos_preprocess_image --input-image i.nii.gz -g g.nii.gz -r c.nii.gz
    """

    _template = """pos_preprocess_image \
                  --input-image {input_image} \
                  {grayscale_output_image} {color_output_image} \
                  {registration_roi} {registration_resize} \
                  {registration_color} \
                  {median_filter_radius} \
                  {invert_grayscale} {invert_multichannel}"""

    _parameters = {
        'input_image': filename_parameter('input_image', None),
        'grayscale_output_image': filename_parameter('-g', None, str_template="{_name} {_value}"),
        'color_output_image': filename_parameter('-r', None, str_template="{_name} {_value}"),
        'registration_roi': list_parameter('extract-roi', None, str_template="--{_name} {_list}"),
        'registration_resize': value_parameter('resize-factor', None, str_template="--{_name} {_value}"),
        'registration_color': string_parameter('color-channel', None, str_template="--{_name} {_value}"),
        'median_filter_radius': list_parameter('median-filter-radius', None, str_template="--{_name} {_list}"),
        'invert_grayscale': switch_parameter('invert-source-image', False, str_template="--{_name}"),
        'invert_multichannel': switch_parameter('invert-rgb-image', False, str_template="--{_name}")}


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

    :param resampling: (optional) amount of upsampling or downsampling of the
        image once it is resliced, expressed in percents. The resampling is applied
        once the images has been resliced, however before the stacking.
        Just remember that you have to provide a list of two positive values.
        They may not be equal, but they have to be non-zero positive values.
    :type resampling: [float, float, float] representing how much the new
        image will be larger or smaller than the original image, expressed in percents.

    :param inversion_flag: (optional) True / False. Inverts the image after
        reslicing. Note that this option requires the image type that exactly meets
        the script specification - three channel, 8bit RGB image. Will not work for
        any other type of the image.
    :type inversion_flag: bool

    Doctests
    --------

    >>> command_warp_rgb_slice
    <class 'possum.pos_wrappers.command_warp_rgb_slice'>

    >>> command_warp_rgb_slice() #doctest: +ELLIPSIS
    <possum.pos_wrappers.command_warp_rgb_slice object at 0x...>

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

    >>> print command_warp_rgb_slice(moving_image='moving.nii.gz',
    ... reference_image='reference.nii.gz', output_image='output.nii.gz',
    ... transformation='transformation.txt', background=255,
    ... region_origin=[20,20], region_size=[100,100],
    ... inversion_flag=True, resampling=[120,10])  #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose -background 255 reference.nii.gz -as ref -clear \
        -mcs moving.nii.gz -as b -pop -as g -pop -as r \
        -push ref -push r -reslice-itk transformation.txt \
          -region 20x20vox 100x100vox -resample 120x10% -scale -1 -shift 255 -type uchar -as rr -type uchar -clear \
        -push ref -push g -reslice-itk transformation.txt \
          -region 20x20vox 100x100vox -resample 120x10% -scale -1 -shift 255 -type uchar -as rg -type uchar -clear \
        -push ref -push b -reslice-itk transformation.txt \
          -region 20x20vox 100x100vox -resample 120x10% -scale -1 -shift 255 -type uchar -as rb -type uchar -clear \
        -push rr -push rg -push rb -omc 3 output.nii.gz
    """

    _template = "c{dimension}d -verbose {background} {interpolation}\
       {reference_image} -as ref -clear \
       -mcs {moving_image}\
       -as b \
       -pop -as g \
       -pop -as r \
       -push ref -push r -reslice-itk {transformation} {region_origin} {region_size} {resampling} {inversion_flag} -as rr -type uchar -clear \
       -push ref -push g -reslice-itk {transformation} {region_origin} {region_size} {resampling} {inversion_flag} -as rg -type uchar -clear \
       -push ref -push b -reslice-itk {transformation} {region_origin} {region_size} {resampling} {inversion_flag} -as rb -type uchar -clear \
       -push rr -push rg -push rb -omc 3 {output_image}"

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'background': pos_parameters.value_parameter('background', None, '-{_name} {_value}'),
        'interpolation': pos_parameters.value_parameter('interpolation', None, '-{_name} {_value}'),
        'reference_image': pos_parameters.filename_parameter('reference_image', None),
        'moving_image': pos_parameters.filename_parameter('moving_image', None),
        'transformation': pos_parameters.filename_parameter('transformation', None),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'region_origin': pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size': pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
        'resampling': pos_parameters.vector_parameter('resampling', None, '-resample {_list}%'),
        'inversion_flag': pos_parameters.boolean_parameter('inversion_flag', None, str_template=' -scale -1 -shift 255 -type uchar'),
    }


class command_warp_grayscale_image(generic_wrapper):
    """
    A special instance of reslice grayscale image dedicated for the sequential
    alignment script.

    :param dimension: (optional) Dimension of the transformation (2 or 3)
    :type dimension: int

    :param background: (optional) default background color
        applied during image reslicing.
    :type background: float

    :param interpolation: (optional) Image intrerplation method.
        The allowed values are: Cubic Gaussian Linear Nearest Sinc
        cubic gaussian linear nearest sinc.
        Please consult the Convert3D online documentation for the details of
        the image interpolation methods:
        http://www.itksnap.org/pmwiki/pmwiki.php?n=Convert3D.Documentation
    :type interpolation: str

    :param reference_image: (required) Filename of the reference image used during the
        resampling process. The prefereble type of the image if of course Niftii
        format.
    :type reference_image: str

    :param moving_image: (required) Image to be resliced.
    :type moving_image: str

    :param transformation: (required) Affine transformation to be applied. ITKv3 affine
        transformation file (a human readable text file) is required. Other types
        of transformations are not well supproted.
    :type transformation: str

    :param resampling: (optional) amount of upsampling or downsampling of the
        image once it is resliced, expressed in percents. The resampling is applied
        once the images has been resliced and optionally cropped,
        however before the stacking.
        Just remember that you have to provide a list of two positive values.
        They may not be equal, but they have to be non-zero positive values.
    :type resampling: [float, float, float] representing how much the new
        image will be larger or smaller than the original image, expressed in percents.

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
    <class 'possum.pos_wrappers.command_warp_grayscale_image'>

    >>> command_warp_grayscale_image() #doctest: +ELLIPSIS
    <possum.pos_wrappers.command_warp_grayscale_image object at 0x...>

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
    <possum.pos_wrappers.command_warp_grayscale_image object at 0x...>
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose -background 255 -interpolation nn ref.nii.gz -as ref -clear\
    moving.nii.gz -as moving -push ref -push moving -reslice-itk transf.txt \
    -type uchar -o output.nii.gz

    >>> p.updateParameters({'region_origin': [10,10,10],
    ... 'region_size': [50,50,50], 'dimension': 3}) #doctest: +ELLIPSIS
    <possum.pos_wrappers.command_warp_grayscale_image object at 0x...>
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    c3d -verbose -background 255 -interpolation nn ref.nii.gz -as ref -clear \
    moving.nii.gz -as moving -push ref -push moving -reslice-itk transf.txt \
    -region 10x10x10vox 50x50x50vox -type uchar -o output.nii.gz

    >>> p = command_warp_grayscale_image(reference_image='ref.nii.gz',
    ... moving_image='moving.nii.gz', transformation='transf.txt',
    ... output_image='output.nii.gz', resampling=[40,50]) #doctest: +NORMALIZE_WHITESPACE
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    c2d -verbose ref.nii.gz -as ref -clear \
    moving.nii.gz -as moving -push ref -push moving -reslice-itk transf.txt \
    -resample 40x50% -type uchar -o output.nii.gz

    """

    _template = "c{dimension}d -verbose {background} {interpolation}\
        {reference_image} -as ref -clear \
        {moving_image} -as moving \
        -push ref -push moving -reslice-itk {transformation} \
        {region_origin} {region_size} {resampling} \
        -type uchar -o {output_image}"

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'background': pos_parameters.value_parameter('background', None, '-{_name} {_value}'),
        'interpolation': pos_parameters.value_parameter('interpolation', None, '-{_name} {_value}'),
        'reference_image': pos_parameters.filename_parameter('reference_image', None),
        'moving_image': pos_parameters.filename_parameter('moving_image', None),
        'transformation': pos_parameters.filename_parameter('transformation', None),
        'resampling': pos_parameters.vector_parameter('resampling', None, '-resample {_list}%'),
        'region_origin': pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size': pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
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
    <class 'possum.pos_wrappers.image_similarity_wrapper'>

    >>> image_similarity_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.image_similarity_wrapper object at 0x...>

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
    <class 'possum.pos_wrappers.split_multichannel_image'>

    >>> split_multichannel_image() #doctest: +ELLIPSIS
    <possum.pos_wrappers.split_multichannel_image object at 0x...>

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
    <class 'possum.pos_wrappers.merge_components'>

    >>> merge_components() #doctest: +ELLIPSIS
    <possum.pos_wrappers.merge_components object at 0x...>

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
        'region_origin': pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size': pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
        'output_type': pos_parameters.string_parameter('output_type', 'uchar', str_template='-type {_value}'),
        'components_no': pos_parameters.value_parameter('components_no', 3),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'other_files_remove': pos_parameters.list_parameter('other_files_remove', [], str_template='{_list}')
        }


class image_voxel_count_wrapper(generic_wrapper):
    """
    Determines the amount (sum or integral) of non-background pixels in the
    provided image.  The backgorund color can be customized. The wrapper
    requires setting up the: `image`, `background`, `voxel_sum` or
    `voxel_integral` parameters to work properly.

    .. note ::
        Only positive (incl. 0) background values are supported.

    >>> image_voxel_count_wrapper
    <class 'possum.pos_wrappers.image_voxel_count_wrapper'>

    >>> image_voxel_count_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.image_voxel_count_wrapper object at 0x...>

    >>> print image_voxel_count_wrapper()
    c2d -shift - -thresh 0 0 0 1 | cut -f3 -d' '


    Verify initial parameters values

    >>> str(image_voxel_count_wrapper._parameters['dimension']) == '2'
    True

    >>> str(image_voxel_count_wrapper._parameters['image']) == ''
    True

    >>> str(image_voxel_count_wrapper._parameters['background']) == ''
    True

    >>> str(image_voxel_count_wrapper._parameters['voxel_sum']) == ''
    True

    >>> str(image_voxel_count_wrapper._parameters['voxel_integral']) == ''
    True


    Testing individual parameters

    >>> print image_voxel_count_wrapper(dimension=3)
    c3d -shift - -thresh 0 0 0 1 | cut -f3 -d' '

    >>> print image_voxel_count_wrapper(image='image.nii.gz')
    c2d image.nii.gz -shift - -thresh 0 0 0 1 | cut -f3 -d' '

    >>> print image_voxel_count_wrapper(background=-20)
    c2d -shift --20 -thresh 0 0 0 1 | cut -f3 -d' '

    >>> print image_voxel_count_wrapper(background=0.0)
    c2d -shift -0.0 -thresh 0 0 0 1 | cut -f3 -d' '

    >>> print image_voxel_count_wrapper(background=20.0)
    c2d -shift -20.0 -thresh 0 0 0 1 | cut -f3 -d' '

    >>> print image_voxel_count_wrapper(voxel_sum=True)
    c2d -shift - -thresh 0 0 0 1 -voxel-sum | cut -f3 -d' '

    >>> print image_voxel_count_wrapper(voxel_integral=True)
    c2d -shift - -thresh 0 0 0 1 -voxel-integral | cut -f3 -d' '


    And all of them combined

    >>> print image_voxel_count_wrapper(dimension=3, image='image.nii.gz',
    ... background=255, voxel_sum=True)
    c3d image.nii.gz -shift -255 -thresh 0 0 0 1 -voxel-sum | cut -f3 -d' '

    """

    _template = """c{dimension}d {image} -shift -{background} \
        -thresh 0 0 0 1 {voxel_sum} {voxel_integral} | cut -f3 -d' ' """

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'image': pos_parameters.filename_parameter('image', False),
        'background' : pos_parameters.value_parameter('shift', 0, '{_value}'),
        'voxel_sum' : pos_parameters.boolean_parameter('voxel-sum', None, str_template='-{_name}'),
        'voxel_integral' : pos_parameters.boolean_parameter('voxel-integral', None, str_template='-{_name}')
    }


class align_by_center_of_gravity(generic_wrapper):
    """
    Calculates a transformation between two images so that the images' centres
    of gravity matches.

    >>> align_by_center_of_gravity
    <class 'possum.pos_wrappers.align_by_center_of_gravity'>

    >>> align_by_center_of_gravity() #doctest: +ELLIPSIS
    <possum.pos_wrappers.align_by_center_of_gravity object at 0x...>

    >>> print align_by_center_of_gravity()
    pos_align_by_moments

    >>> p = align_by_center_of_gravity(fixed_image="fixed.nii.gz",
    ... moving_image="moving.nii.gz", output_transformation="output.txt")
    >>> print p
    pos_align_by_moments --fixed-image fixed.nii.gz --moving-image moving.nii.gz --transformation-filename output.txt

    >>> print p.updateParameters({"fixed_image": None})
    pos_align_by_moments --moving-image moving.nii.gz --transformation-filename output.txt

    >>> print p.updateParameters({"moving_image": None})
    pos_align_by_moments --transformation-filename output.txt

    >>> print p.updateParameters({"moving_image": "m.nii.gz", "fixed_image": "f.nii.gz"})
    pos_align_by_moments --fixed-image f.nii.gz --moving-image m.nii.gz --transformation-filename output.txt
    """

    _template = """pos_align_by_moments {fixed_image} {moving_image} {output_transformation}"""

    _parameters = {
        'fixed_image': pos_parameters.filename_parameter('fixed_image', None, str_template="--fixed-image {_value}"),
        'moving_image': pos_parameters.filename_parameter('moving_image', None, str_template="--moving-image {_value}"),
        'output_transformation': pos_parameters.filename_parameter('output_transformation', None, str_template="--transformation-filename {_value}"),
    }


class slice_volume_wrapper(generic_wrapper):
    """
    Wrapper for the pos_slice_volume script. Provides basic functionality of
    the full script.

    >>> slice_volume_wrapper
    <class 'possum.pos_wrappers.slice_volume_wrapper'>

    >>> slice_volume_wrapper() #doctest: +ELLIPSIS
    <possum.pos_wrappers.slice_volume_wrapper object at 0x...>

    >>> print slice_volume_wrapper()
    pos_slice_volume -i -o "%04d.nii.gz" -s 1 -r 1

    Checking default parameteres values:

    >>> print slice_volume_wrapper._parameters['input_image']
    <BLANKLINE>

    >>> print slice_volume_wrapper._parameters['output_naming']
    %04d.nii.gz

    >>> print slice_volume_wrapper._parameters['slicing_axis']
    1

    >>> print slice_volume_wrapper._parameters['start_slice']
    <BLANKLINE>

    >>> print slice_volume_wrapper._parameters['end_slice']
    <BLANKLINE>

    >>> print slice_volume_wrapper._parameters['step']
    1

    >>> print slice_volume_wrapper._parameters['shift_indexes']
    <BLANKLINE>


    Checking robustness of the parameters dictionary:

    >>> p = slice_volume_wrapper(input_image="input.nii.gz",
    ... output_naming="%04d.nii.gz", slicing_axis=1, start_slice=0,
    ... end_slice=100)
    >>> print p
    pos_slice_volume -i input.nii.gz -o "%04d.nii.gz" -s 1 -r 0 100 1

    >>> p = slice_volume_wrapper(input_image="input.nii.gz",
    ... output_naming="%04d.nii.gz", slicing_axis=1, start_slice=0,
    ... end_slice=100, shift_indexes=-10)
    >>> print p
    pos_slice_volume -i input.nii.gz -o "%04d.nii.gz" -s 1 -r 0 100 1 --output-filenames-offset -10

    >>> p = slice_volume_wrapper(input_image="input.nii.gz",
    ... output_naming="%04d.nii.gz", slicing_axis=1,
    ... end_slice=100, shift_indexes=-10)
    >>> print p
    pos_slice_volume -i input.nii.gz -o "%04d.nii.gz" -s 1 -r 100 1 --output-filenames-offset -10

    >>> p = slice_volume_wrapper()
    >>> print p
    pos_slice_volume -i -o "%04d.nii.gz" -s 1 -r 1

    >>> p.updateParameters({"parameter_that_does_not_exist":0.5})
    Traceback (most recent call last):
    KeyError: 'parameter_that_does_not_exist'

    >>> print p.updateParameters({"input_image": "input_image.nii.gz"})
    pos_slice_volume -i input_image.nii.gz -o "%04d.nii.gz" -s 1 -r 1

    >>> print p.updateParameters({"output_naming":
    ... "output_directory/%04d.nii.gz"}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_volume -i input_image.nii.gz -o "output_directory/%04d.nii.gz" -s 1 -r 1

    >>> print p.updateParameters({"slicing_axis": 2, "start_slice": 50,
    ... "end_slice": 100, "step": 2}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_volume -i input_image.nii.gz -o "output_directory/%04d.nii.gz" -s 2 -r 50 100 2

    >>> print p.updateParameters({"shift_indexes": 1})
    pos_slice_volume -i input_image.nii.gz -o "output_directory/%04d.nii.gz" -s 2 -r 50 100 2 --output-filenames-offset 1

    Nonsense / empty parameters are allowed as well:

    >>> print p.updateParameters({"shift_indexes": range(10)})
    pos_slice_volume -i input_image.nii.gz -o "output_directory/%04d.nii.gz" -s 2 -r 50 100 2 --output-filenames-offset [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    >>> print p.updateParameters({"input_image": 2 + 4}) #doctest: +NORMALIZE_WHITESPACE
    pos_slice_volume -i 6 -o "output_directory/%04d.nii.gz" -s 2 -r 50 100 2 --output-filenames-offset [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    >>> print p.updateParameters({"input_image": None, "shift_indexes": None})
    pos_slice_volume -i -o "output_directory/%04d.nii.gz" -s 2 -r 50 100 2

    That's new: make all the paramters none and see what will happen:

    >>> none_parameters_dict =  dict(map(lambda k: (k, None),
    ... slice_volume_wrapper._parameters.keys()))
    >>> print p.updateParameters(none_parameters_dict)
    pos_slice_volume -i -o "" -s -r
    """

    _template = """pos_slice_volume \
            -i {input_image} \
            -o "{output_naming}" \
            -s {slicing_axis} \
            -r {start_slice} {end_slice} {step} \
            {shift_indexes}"""

    _parameters = { \
            'input_image' : filename_parameter('input_image', None),
            'output_naming' : filename_parameter('output_naming', "%04d.nii.gz"),
            'slicing_axis' : value_parameter('slicing_axis', 1),
            'start_slice' : value_parameter('start_slice', None),
            'end_slice' : value_parameter('end_slice', None),
            'step' : value_parameter('step', 1),
            'shift_indexes' : value_parameter('output-filenames-offset', None, str_template="--{_name} {_value}")
            }


class get_affine_from_landmarks_wrapper(generic_wrapper):
    """
    Wrapper for ANTSUseLandmarkImagesToGetAffineTransform from the ANTS
    package. Calculates affine or rigid transformation based on set of two
    landmarks images. The landmarks images are assumed to be inexed images the
    same physical space as the images to register. Both images has to have the
    same set of landmarks defined.

    This parser is crazy messy and probably should be rewritten entirely or
    replaced with something better. The main problem is that, so fat, the
    landmark matching in convert 3d is implemented only for three dimensional
    images. This means that it does not work well for 2D images. The only way
    to align 2D images with landmark matching is to consider them as 3D image
    which will produce a 3D transformation and then convert is somehow to 2D
    transformation. This is what the clumsy awk part of the script doing.
    Again, this should be done in a better way, but hey! it works and produces
    good results.
    """

    _template = """c3d {fixed_image} {moving_image} -alm {transformation_type} {output_transformation} && \
        c3d_affine_tool {output_transformation} -oitk {output_transformation} && \
        sed -i s/MatrixOffsetTransformBase_double_3_3/MatrixOffsetTransformBase_double_2_2/ {output_transformation} && \
        awk 'NR==1 {{print $0}} NR==2 {{print $0}} NR==3 {{print $0}} NR==4 {{print $1,$2,$3,$5,$6,$11,$12}} NR==5 {{print $1,$2,$3}}' < {output_transformation} > {output_transformation}.txt && \
        mv {output_transformation}.txt {output_transformation}"""

    _parameters = {
        'fixed_image': pos_parameters.filename_parameter('fixed_image', None, str_template="{_value}"),
        'moving_image': pos_parameters.filename_parameter('moving_image', None, str_template="{_value}"),
        'transformation_type': pos_parameters.string_parameter('transformation_type', 'rigid', str_template="{_value}"),
        'output_transformation': pos_parameters.filename_parameter('output_transformation', None, str_template="{_value}"),
    }


if __name__ == 'possum.pos_wrappers':
    import doctest
    doctest.testmod()
