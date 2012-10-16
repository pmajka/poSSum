import sys, os
import unittest
import subprocess as sub

# type
# serialization function
# value, default valuse

class generic_parameter(object):
    _str_template = None
    
    def __init__(self, name, value = None,  str_template = None):
        self._value = None
        if value:
            self.value = value
        
        self._name = None
        self.name = name
        
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
    
    def _serialize(self):
        if self.value != None:
            return self._str_template.format(**self.__dict__)
        else:
            return ""

class string_parameter(generic_parameter):
    _str_template = "{_value}"
    
    def _serialize(self):
        if self.value != None:
            return self._str_template.format(**self.__dict__)
        else:
            return ""

class filename_parameter(string_parameter):
    _str_template = "{_value}"

class value_parameter(string_parameter):
    _str_template = "{_value}"

class list_parameter(generic_parameter):
    _str_template = "{_list}"
    _delimiter = " "
    
    def _serialize(self):
        if self.value:
            self._list = self._delimiter.join(map(str, self.value))
            return self._str_template.format(**self.__dict__)
        else:
            return ""

class vector_parameter(list_parameter):
    _delimiter = 'x'

class ants_specific_parameter(generic_parameter):
    _switch = None
    
    def _serialize(self):
        meaning = self.value[0]
        values  = self.value[1]
        
        retStr = " "+ self._switch +" " + meaning + "["
        retStr+= ",".join(map(str, values))
        retStr+="] "
        
        return retStr

class ants_transformation_parameter(ants_specific_parameter):
    _switch = '-t'

class ants_regularization_parameter(ants_specific_parameter):
    _switch = '-r'

class generic_wrapper(object):
    _template = None
    
    _parameters = {}
    
    def __init__(self, **kwargs):
        
        # Hardcopy the parameters to split instance parameters
        # from default class parameters
        self.p = dict(self._parameters)
        
        self.updateParameters(kwargs)
    
    def __str__(self):
        replacement = dict(map(lambda (k,v): (k, str(v)), self.p.iteritems()))
        return self._template.format(**replacement)
    
#   def __call__(self):
#       command = str(self)
#       p = sub.Popen(command.split(), stdout=sub.PIPE, stderr=sub.PIPE)
#       output, errors = p.communicate()
#       execution = {'command': command, 'output' : output, 'error' : errors, 'port' : {}}
#       
#       if hasattr(self, '_io_pass'):
#           for k, v in self._io_pass.iteritems():
#               execution['port'][v] = self._parameters[k].value
#       return execution

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
    _template = """ANTS {dimension} \
       {verbose} \
       {transformation} {regularization} {outputNaming} \
       {imageMetrics} \
       {iterations} {affineIterations}\
       {rigidAffine} {continueAffine}\
       {useNN} {histogramMatching} {allMetricsConverge} \
       {initialAffine} {fixedImageInitialAffine} {affineGradientDescent} \
       {maskImage}
       """
    
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
            'maskImage'      : filename_parameter('--mask-image', None, str_template = '--{_name} {_value}')
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
        'useNN'            : switch_parameter('use-NN', False, str_template = '--{_name}'),
        'useBspline'       : switch_parameter('use-BSpline', False, str_template = '--{_name}'),
        'deformable_list'  : list_parameter('deformable_list', [], str_template = '{_list}'),
        'affine_list'  : list_parameter('affine_list', [], str_template = '{_list}')
                }
    
    _io_pass = { \
            'dimension'    : 'dimension',
            'output_image' : 'input_image'
            }

class average_images(generic_wrapper):
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
    
"""

In [1]: p =  switch_parameter('useNN', False, "--{_name}")

In [2]: p
Out[2]: <__main__.switch_parameter object at 0x87506ec>

In [3]: str(p)
Out[3]: '--useNN'

In [4]: p.name = 'something'

In [5]: str(p)
Out[5]: '--something'
In [10]: p.name = 'sth'

In [11]: print p
 --sth 

 In [12]: p.template
 Out[12]: ' --{_name} '

 In [13]: p.template = ' --{_value} --{_name}'

 In [14]: print p
  --True --sth
In [11]: p=vector_parameter('number-of-iterations', [10000,10000,10000], "--{_name} {_list}")

In [12]: print p
--number-of-iterations 10000x10000x10000

In [13]: p.name
Out[13]: 'number-of-iterations'

In [14]: p.value
Out[14]: [10000, 10000, 10000]

In [15]: p.template
Out[15]: '--{_name} {_list}'

In [19]: p._list
Out[19]: '10000x10000x10000'

In [22]: p.name = 'any_name'


In [23]: p.name
Out[23]: 'any_name'

In [24]: p.value = (0,0,0,0)

In [25]: print p
--any_name 0x0x0x0

In [1]: p = ants_regularization_parameter('regularization', ('Gauss',(0.2,0.2)))

In [2]: print p
 -t Gauss[0.2,0.2]

In [1]: p=filename_parameter('file','file.txt')

In [2]: p._str_template
Out[2]: '{_value}'

In [3]: print p
file.txt

In [37]: print ants_transformation_parameter("transformation", ("SyN",(0,0)))
 -t SyN[0,0] 

 In [38]: transf = ants_transformation_parameter("transformation", ("SyN",(0,0)))

 In [39]: print transf
  -t SyN[0,0] 

In [40]: transf.value
Out[40]: ('SyN', (0, 0))

In [41]: transf.value = ("Elast",(0,1))

In [42]: print transf
 -t Elast[0,1] 

In [46]: transf._switch
Out[46]: '-t'

In [47]: transf._switch = '-h'

In [48]: print transf
 -h Elast[0,1] 

In [49]: transf.name
Out[49]: 'transformation'

In [50]: transf.name = 'whatever'

In [51]: print transf
 -h Elast[0,1] 


In [53]: transf._serialize()
Out[53]: ' -h Elast[0,1] '


In [55]: a = ants_intensity_meric('fixed.nii.gz',',moving.nii.gz')

In [56]: print a
-m CC[fixed.nii.gz,,moving.nii.gz,1,4]


In [57]: a.fixed_image = 'f.nii.gz'
^[[A
In [58]: print a
-m CC[f.nii.gz,,moving.nii.gz,1,4]

In [59]: a.moving_image = 'm.nii.gz'

In [60]: print a
-m CC[f.nii.gz,m.nii.gz,1,4]

In [61]: a.weight = 3

In [62]: print a
-m CC[f.nii.gz,m.nii.gz,3,4]
In [65]: a.parameter = 44

In [66]: print a
-m CC[f.nii.gz,m.nii.gz,3,44]

In [67]: a.parameter = '44'

In [68]: print a
-m CC[f.nii.gz,m.nii.gz,3,44]


In [75]: metric_settings = {'weight':2, 'metric' : 'MSQ', 'parameter' : 8}

In [76]: a=antsIntensityMetric('_f_.nii.gz','_m_.nii.gz', **metric_settings)

In [77]: print a
-m MSQ[_f_.nii.gz,_m_.nii.gz,2,8]


"""


if __name__ == '__main__':
    pass
