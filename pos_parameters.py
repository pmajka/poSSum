import sys, os
import unittest

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
        if self.value:
            return self._str_template.format(**self.__dict__)
        else:
            return ""

class string_parameter(generic_parameter):
        
    def _serialize(self):
        if self.value:
            return self._str_template.format(**self.__dict__)
        else:
            return ""

class filename_parameter(string_parameter):
    _str_template = "{_value}"

class value_parameter(string_parameter):
    _str_template = "{_value}"

class list_parameter(generic_parameter):
    _delimiter = " "
    
    def _serialize(self):
        if self.value:
            self._list = self._delimiter.join(map(str,self._value))
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

class antsIntensityMetric(object):
    _template = "-m {metric}[{fixed_image},{moving_image},{weight},{parameter}]"
    
    _parameters = {\
            'metric' : string_parameter('metric', 'CC'),
            'fixed_image' : filename_parameter('fixed_image', None),
            'moving_image': filename_parameter('fixed_image', None),
            'weight'      : value_parameter('weight', None),
            'parameter'   : value_parameter('parameter', None)
            }
    
    def __init__(self, fixed_image, moving_image, metric='CC', weight = 1, param = 4):
        pass
        self.fixed_image  = fixed_image
        self.moving_image = moving_image
        self.metric = metric
        self.weight = weight
        self.param = param
    
    def __getattr__(self, attr):
        if attr in self._parameters.keys():
            return  self._parameters[attr].value
        else:
            return super(self.__class__, self).__getattr__(attr)
    
    def __setattr__(self, attr, value):
        if attr in self._parameters.keys():
            return setattr(self._parameters[attr],'value',value)
        else:
            return super(self.__class__, self).__setattr__(attr, value)
    
    def __str__(self):
        replacement = dict(map(lambda (k,v): (k, v.value), self._parameters.iteritems()))
        print replacement
        return self._template.format(**replacement)

class ants_registration(object):
    _parameters = { \
            }

"""
switch_parameter('useNN', False, "--{_name}")

param = switch_parameter():
    _boolParams = \
           {'verbose'        : antsParam('verbose', True),
            'continueAffine' : antsParam('continue-affine', True),
            'useNN'          : antsParam('use-NN', False),
            'rigidAffine'    : antsParam('rigid-affine', False),
            'hiistogramMatching' : antsParam('use-Histogram-Matching', True),
            'allMetricsConverge' : antsParam('use-all-metrics-for-convergence', False)}
    
    _filenameParams = \
           {'initialAffine' : antsParam('initial-affine', None),
            'fixedImageInitialAffine' : antsParam('fixed-image-initial-affine', None),
            'outputNaming' : antsParam('output-naming', None)}
    
    _vectorParams = \
            {'iterations' : antsParam('number-of-iterations', (5000,)*4),
             'affineIterations' : antsParam('number-of-affine-iterations', (10000,)*5),
             'affineGradientDescent' : antsParam('affine-gradient-descent-option', None)}

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


"""


if __name__ == '__main__':
    switch_parameter('useNN', False, " --{_name} ")
