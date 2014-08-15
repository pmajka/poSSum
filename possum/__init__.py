"""

"""

__version__ = '0.16.0'

import os

import pos_common

print os.environ
if os.environ.get('TRAVIS') is not 'true':
    import pos_itk_core

import pos_parameters
import pos_wrapper_skel

import pos_wrappers
import pos_deformable_wrappers

import deformable_histology_iterations
