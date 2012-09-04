import multiprocessing
import logging
import sys
import os
import subprocess as sub
import numpy as np
from collections import namedtuple

import networkx as nx
import json
import unittest

def listToChain(listToSplit):
    if len(listToSplit) == 1:
        return [(listToSplit[0], listToSplit[0])]
    else:
        return zip(listToSplit[:-1], listToSplit[1:])

def getVectorString(iterable):
    return "x".join(map(str, map(int,iterable)))

antsParam = namedtuple('antsParam', 'antsName defValue')

class antsWrapper(object):
    pass

class antsIntensityMetric(antsWrapper):
    def __init__(self, fixedImage, movingImage, metric='CC', weight = 1, param = 4):
        self.metric = metric
        self.fixedImage = fixedImage
        self.movingImage = movingImage
        self.weight = weight
        self.param = param
    
    def __str__(self):
        retStr = "-m " + self.metric
        retStr+= "[" + self.fixedImage + "," + self.movingImage + "," + str(self.weight)
        retStr+= "," + str(self.param) + "]"
        return retStr

class antsLinearRegistrationWrapper(antsWrapper):
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
    
    def __init__(self, outputNaming, metrics, dimension = 2, parameters = None):
        
        self._assignDefaultValues()
        
        self.transformation = ('SyN', (0.15,))  # (str, (float, [float, ... ]))
        self.regularization = ('Gauss', (3,1))  # (str,(float,float)
        
        # Load setting provided by the user
        self.dimension = dimension       #
        self.outputNaming = outputNaming #
        
        # Load metrics
        self.metrics = metrics
        
        # Update parameters when the custom parameters
        # dictionary is provided. This will override default parameters
        # values with the custom one.
        if parameters != None:
            self.updateParameters(parameters)
    
    def _assignDefaultValues(self):
        for parameterSet in [self._boolParams, self._filenameParams, self._vectorParams]:
            for parameter, data in parameterSet.iteritems():
                setattr(self, parameter, data.defValue)
    
    def updateParameters(self, parameters):
        for (name, value) in parameters:
            setattr(self, name, value)
     
    def generateWrapCommand(self):
        pass
    
    def getParametricPrefix(self):
        pass
    
    def _getReguralizationString(self):
        """
        """
        regType = self.regularization[0]
        regParams =  self.regularization[1]
        
        retStr = " -r " + regType + "["
        retStr+= ",".join(map(str, regParams))
        retStr+="] "
        return retStr
    
    def _getTransformationString(self):
        """
        """
        # Split transformation attribute into
        # transformation type
        # and transformation properties
        transfType = self.transformation[0]
        transfParameters = self.transformation[1]
        
        retStr = " -t " + transfType + "["
        retStr+= ",".join(map(str, transfParameters))
        retStr+="] "
        
        return retStr
    
    def __str__(self):
        # Initialize the command"
        retStr = "ANTS " + str(self.dimension) + " "
        
        # Handle the parameters with a complex structure:
        retStr+= self._getTransformationString() 
        retStr+= self._getReguralizationString() 
        
        # Append all metrics that the registration framework
        # image to image metrics
        retStr += " ".join(map(str, self.metrics))
        
        # Now, append all vector arguments
        parameters = [(self._vectorParams,  getVectorString),
                      (self._boolParams,    str),
                      (self._filenameParams,str)]
        
        for parameterSet, serial in parameters:
            for parameter, data in parameterSet.iteritems():
                parameterValue = getattr(self, parameter)
                if parameterValue != None:
                    retStr += " --" + data.antsName + " " \
                            + serial(getattr(self, parameter)) \
                            + " "
        # Now support all the other parameter:
        
        return retStr
     
    def __call__(self):
        command = str(self)
        p = sub.Popen(command.split(), stdout=sub.PIPE, stderr=sub.PIPE)
        output, errors = p.communicate()
        print  output, errors
     

"""
r = antsLinearRegistrationWrapper(outPrefix, metrics)
r.

"""


class LinearRegressionTestCase(unittest.TestCase):

    def test_check_valid_data(self):
        # Given
        vec = (10,-20,30)
        # Then
        # When
        self.assertEqual(getVectorString(vec),'10x-20x30')
    
    def test_check_value_error(self):
        # Given
        vec = ('sdf',[], 4)
        # Then
        # When
        self.assertRaises(ValueError, getVectorString, vec)
    
    def test_check_type_error(self):
        # Given
        vec = 5
        # Then
        # When
        self.assertRaises(TypeError, getVectorString, vec)

class TestAntsMetric(unittest.TestCase):
    def test_simple_run(self):
        cases = [ \
                (('fi.nii.gz','mi.nii.gz'), {}),
                (('fi.nii.gz','mi.nii.gz'), {'metric': 'CC'}),
                (('fi.nii.gz','mi.nii.gz'), {'metric': 'MI'}),
                (('fi.nii.gz','mi.nii.gz'), {'metric': 'MSQ'}),
                (('fi.nii.gz','mi.nii.gz'), {'weight': 2}),
                (('fi.nii.gz','mi.nii.gz'), {'param' :16})
                ]
        desired = [ \
                "-m CC[fi.nii.gz,mi.nii.gz,1,4]", \
                "-m CC[fi.nii.gz,mi.nii.gz,1,4]", \
                "-m MI[fi.nii.gz,mi.nii.gz,1,4]", \
                "-m MSQ[fi.nii.gz,mi.nii.gz,1,4]", \
                "-m CC[fi.nii.gz,mi.nii.gz,2,4]" ,\
                "-m CC[fi.nii.gz,mi.nii.gz,1,16]" \
                ]
        
        for ((args, kwargs), result) in zip(cases,desired):
            metric = str(antsIntensityMetric(*args, **kwargs))
            self.assertEqual(metric, result)
    
#   def test_simple_run(self):
#       cases = [ \
#               (('fi.nii.gz','mi.nii.gz'), {}),
#               (('fi.nii.gz','mi.nii.gz'), {})
#               ]
#       
#       desired = [AssertionError,AssertionError]
#       
#       for ((args, kwargs), exception) in zip(cases, desired):
#           self.assertRaises(exception, antsIntensityMetric, args, kwargs)

        
if __name__ == '__main__':
    #unittest.main()
    a = antsLinearRegistrationWrapper("out", [antsIntensityMetric('f.nii.gz','m.nii.gz')])
    print a()
