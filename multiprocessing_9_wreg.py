import multiprocessing
import logging
import sys
import os
import subprocess as sub
import numpy as np

import networkx as nx
import json
import unittest

def listToChain(listToSplit):
    if len(listToSplit) == 1:
        return [(listToSplit[0], listToSplit[0])]
    else:
        return zip(listToSplit[:-1], listToSplit[1:])

def getVectorString(iterable):
    #TODO: Assert checking if the argument is
    # iterable
    return "x".join(map(str, map(int,iterable)))

class antsWrapper(object):
    pass

class antsIntensityMetric(antsWrapper):
    def __init__(self, fixedImage, movingImage, name='CC', weight = 1, param = 4):
        self.name = name
        self.fixedImage = fixedImage
        self.movingImage = movingImage
        self.weight = weight
        self.param = param
    
    def __str__(self):
        retStr = "-m " + self.name 
        retStr+= "[" + self.fixedImage + "," + self.movingImage + "," + str(self.weight)
        retStr+= "," + str(self.param) + "]"
        return retStr

class antsLinearRegistrationWrapper(antsWrapper):
    booleanSwitches = []
    
    def __init__(self, outputNaming, metrics, dimension = 2):
        self.metrics = []
        self.dimension = dimension        #
        self.outputNaming  = outputNaming #
        
        self.regularization = None        # (str,(float,float)
        self.transformation = None        # (str, (float, [float, ... ]))
        
        self.iterations = None            # iterable of ints
        self.affineIterations = None      # 
        
        self.affineGradientDescent = None
        self.initialAffine = None           #
        self.fixedImageInitialAffine = None #
        self.affineMetricType = None
        
        self.rigidAffine = None
        self.continueAffine = None #
        self.geodesic = None 
        self.useHistogramMatching = None
        self.useAllMetricsForConvergence = None #
        self.useNN = None
        self.verbose = None                 #
    
    def updateParameters(self, parameters):
        for (name, value) in parameters:
            setattr(self, name, value)
    
    def generateWrapCommand(self):
        pass
    
    def getParametricPrefix(self):
        pass
    
    def __str__(self):
        retStr = "-m " + self.name 
        retStr+= "[" + self.fixedImage + "," + self.movingImage + "," + str(self.weight)
        retStr+= "," + str(self.param) + "]"
        return retStr
     
    def __str__(self):
        boolParams = ['verbose', 'geodesic', 'continueAffine', 'useNN', 'useHistogramMatching',
                      'rigidAffine', 'useAllMetricsForConvergence']
        pass

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
        # Given
        metric = str(antsIntensityMetric('fixed.nii.gz','moving.nii.gz'))
        desired   
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

        
if __name__ == '__main__':
    unittest.main()
