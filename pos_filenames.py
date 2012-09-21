import numpy as np
import os, sys
from itertools import izip
import datetime, time
from optparse import OptionParser, OptionGroup

from pos_parameters import generic_parameter, filename_parameter, string_parameter, list_parameter

class filename(generic_parameter):
    def __init__(self, name, value = None, str_template = None,\
                             job_dir = None, work_dir = None):
        
        generic_parameter.__init__(self, name, value = value, \
                str_template = str_template)
        
        self.job_dir = job_dir
        self.work_dir = work_dir
        
        # Possibility of complex behaviour
        self.override_dir = None
        self.override_fname = None
        self.override_path = None
    
    def _get_job_dir(self):
        return self._job_dir
    
    def _set_job_dir(self, value):
        self._job_dir = value
    
    def _get_work_dir(self):
        return self._work_dir
    
    def _set_work_dir(self, value):
        self._work_dir = value
    
    def _get_base_dir(self):
        return os.path.join(self.job_dir, self.work_dir)
    
    def _set_base_dir(self, value):
        pass
    
    def updateParameters(self, parameters):
        for (name, value) in parameters.items():
            setattr(self, name, value)
        return self
    
    def _serialize(self):
        if self.override_fname:
            return self.override_fname
        else:
            return self._str_template.format(**self.__dict__)
    
    def __str__(self):
        if self.override_dir:
            return os.path.join(self.override_dir, self._serialize())
        if self.override_path:
            return self.override_path
        
        return os.path.join(self.job_dir, self.work_dir, self._serialize())
    
    def __call__(self, **parameters):
        self.updateParameters(parameters)
        return str(self)
     
    job_dir = property(_get_job_dir, _set_job_dir)
    work_dir = property(_get_work_dir, _set_work_dir)
    base_dir = property(_get_base_dir, _set_base_dir)


"""
In [1]: f = filename('resliced_rgb', job_dir = 'jobdir', work_dir ="01_resliced_rgb",  str_template = 'f{fixed:04d}_m{moving:04d}Affine.txt')
In [3]: f.name
Out[3]: 'resliced_rgb'

In [4]: f.job_dir
Out[4]: 'jobdir'

In [5]: f.work_dir
Out[5]: '01_resliced_rgb'

In [6]: f.template
Out[6]: 'f{fixed:04d}_m{moving:04d}Affine.txt'

In [7]: f()
---------------------------------------------------------------------------
KeyError

In [8]: f(fixed=1,moving=9)
Out[8]: 'jobdir/01_resliced_rgb/f0001_m0009Affine.txt'

"""
