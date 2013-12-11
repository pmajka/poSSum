#!/usr/bin/python
# -*- coding: utf-8 -*
###############################################################################
#                                                                             #
#    This file is part of Multimodal Atlas of Monodelphis Domestica           #
#                                                                             #
#    Copyright (C) 2011-2012 Piotr Majka                                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is free software: you can redistribute      #
#    it and/or modify it under the terms of the GNU General Public License    #
#    as published by the Free Software Foundation, either version 3 of        #
#    the License, or (at your option) any later version.                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is distributed in the hope that it          #
#    will be useful, but WITHOUT ANY WARRANTY; without even the implied       #
#    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.         #
#    See the GNU General Public License for more details.                     #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along  with  3d  Brain  Atlas  Reconstructor.   If  not,  see            #
#    http://www.gnu.org/licenses/.                                            #
#                                                                             #
###############################################################################

import os, sys
import copy
from optparse import OptionParser, OptionGroup
from pos_wrapper_skel import generic_workflow
import pos_wrappers, pos_parameters

import numpy
from scipy.ndimage.filters import gaussian_filter1d

# -----------------------------------------------
# Directory template update
# -----------------------------------------------

CLASS_SPECIFC_DIR_TEMPLATES = {
            'processing_group_dir'  : '70_blockface_to_histology_registration',
            'fine_transf'    : '01_fine_transformations',
            'smooth_transf' : '02_smoothed_transformations',
            'final_transf'  : '03_final_transformations',
            'reports'       : '04_reports'}

CLASS_SPECIFC_LOCAL_DIRS = []

CLASS_SPECIFC_PROCESS_DIRS = ['fine_transf', 'smooth_transf', 'final_transf', 'reports']

# -----------------------------------------------
# Command templates
# -----------------------------------------------
COMMAND_GENERATE_PREPROCESS = ""

COMMAND_COPY = """cp -rfv %(inputFileMask)s %(target)s"""

COMMAND_GENERATE_FINAL_TRANSFORM = """ComposeMultiTransform 2 \
         %(outputFilename)s -i %(inputFilename)s"""

COMMAND_GRAPH_REPORT = """#!/usr/bin/gnuplot -persist
set macros

set terminal pngcairo enhanced color notransparent size 800,600  font 'Verdana,8'
set output '%(outputGraphFilename)s'

POS = "at graph 0.5,0.95 font ',8' center"

NOXTICS = "set xtics; unset xlabel; set format x '';"
XTICS   = "set xtics; set xlabel 'Slice index' font ',8'; set format x '%%g';"

NOYTICS = "set format y ''; unset ylabel"
YTICS = "set format y '%%g'; set ylabel ''"

TMARGIN = "set tmargin at screen 0.90; set bmargin at screen 0.55"
BMARGIN = "set tmargin at screen 0.50; set bmargin at screen 0.15"
LMARGIN = "set lmargin at screen 0.10; set rmargin at screen 0.50"
RMARGIN = "set lmargin at screen 0.55; set rmargin at screen 0.95"

FN_SMOOTH = "'%(smoothedTransformFname)s'"
FN_RAW = "'%(fineTransformFname)s'"
FN_DIFF = "'%(diffTransformFname)s'"

set style line 1 lc rgb '#031A49' lt 1 lw 1 # --- blue
set style line 2 lc rgb '#1D4599' lt 1 lw 1 # --- lblue
set style line 3 lc rgb '#025214' lt 1 lw 1 # --- blue
set style line 4 lc rgb '#11AD34' lt 1 lw 1 # --- red
set style line 5 lc rgb '#E62B17' lt 1 lw 1 # --- blue
set style line 6 lc rgb '#6D0D03' lt 1 lw 1 # --- red
set style line 7 lc rgb '#E69F17' lt 1 lw 1 # --- blue
set style line 8 lc rgb '#6D4903' lt 1 lw 1 # --- red

STYLE_RAW_1    = "w l ls 1 notitle"
STYLE_SMOOTH_1 = "w l ls 2 notitle"
STYLE_RAW_2    = "w l ls 3 notitle"
STYLE_SMOOTH_2 = "w l ls 4 notitle"
STYLE_RAW_3    = "w l ls 5 notitle"
STYLE_SMOOTH_3 = "w l ls 6 notitle"
STYLE_RAW_4    = "w l ls 7 notitle"
STYLE_SMOOTH_4 = "w l ls 8 notitle"

set multiplot layout 2,2 rowsfirst title "Fine - coarse : %(outputGraphFilename)s"

set label 1 'Offset (translation) [pixels]' @POS
@NOXTICS; @YTICS
@TMARGIN; @LMARGIN
plot @FN_RAW  u 0:5 @STYLE_RAW_1, @FN_SMOOTH u 0:5 @STYLE_SMOOTH_1 , \
     @FN_RAW  u 0:6 @STYLE_RAW_2, @FN_SMOOTH u 0:6 @STYLE_SMOOTH_2

set label 1 'Horizontal and vertical scaling' @POS
@NOXTICS; @YTICS
@TMARGIN; @RMARGIN
set yrange [0.95:1.05]
plot @FN_RAW u 0:1 @STYLE_RAW_3, @FN_SMOOTH u 0:1 @STYLE_SMOOTH_3 , \
     @FN_RAW u 0:4 @STYLE_RAW_4, @FN_SMOOTH u 0:4 @STYLE_SMOOTH_4

set label 1 'Slice rotation [degrees]' @POS
@XTICS; @YTICS
@BMARGIN; @LMARGIN
set nokey
set yrange [-20:20]
plot @FN_RAW  u 0:(90-acos($2)*180./pi) @STYLE_RAW_3, @FN_SMOOTH u 0:(90-acos($2)*180./pi) @STYLE_SMOOTH_3

set label 1 'Fixed parameters [pixels]' @POS
@XTICS; @YTICS
@BMARGIN; @RMARGIN
set auto y
plot @FN_RAW  u 0:7 @STYLE_RAW_3, @FN_SMOOTH u 0:7 @STYLE_SMOOTH_3 , \
     @FN_RAW  u 0:8 @STYLE_RAW_4, @FN_SMOOTH u 0:8 @STYLE_SMOOTH_4

unset multiplot
"""

COMMAND_GENERATE_GRAPH = """gnuplot %(plotFilename)s; rm -fv %(plotFilename)s;"""


class coarse_to_fine_transformation_merger(generic_workflow):
    """
    Coarse to fine transformation merger.
    """
            'FN_FINE_TR'    : '%04d.txt',
            'FN_SMOOTH_TR'  : '%04d.txt',
            'FN_FINAL_TR'   : '%04d.txt',
            'FN_FINE_CSV'   : '%s_fine_transformations.csv',
            'FN_SMOOTH_CSV' : '%s_smoothed_transformations.csv',
            'FN_DIFF_CSV'   : '%s_difference_transformations.csv',
            'FN_FINAL_CSV'  : '%s_final_transformations.csv',
            'FN_GRAPH'    : '%s_transformations_graph.png'}

    _f = {
        'fine_transf' : pos_parameters.filename('fine_transf', work_dir = '01_fine_transformation', str_template = '{idx:04d}.txt'),
        'coarse_transf' : pos_parameters.filename('coarse_transf', work_dir = '02_coarse_transformation', str_template = '{idx:04d}.txt'),
        'final_transf' : pos_parameters.filename('final_transf', work_dir = '03_final_transformation', str_template = '{idx:04d}.txt'),

        'fine_report' : pos_parameters.filename('fine_report', work_dir = '05_reports', str_template='fine_transformations.csv'),
        'smooth_report' : pos_parameters.filename('smooth_report', work_dir = '05_reports', str_template='smooth_transformations.csv'),
        'difference_report' : pos_parameters.filename('difference_report', work_dir = '05_reports', str_template='difference_trasnformations.csv'),
        'final_report' : pos_parameters.filename('final_report', work_dir = '05_reports', str_template='final_transformations.csv'),
        'graph' : pos_parameters.filename('graph', work_dir = '05_reports', str_template='graph.png'),
        'graph_source' : pos_parameters.filename('graph_source', work_dir = '05_reports', str_template='graph_source.plt'),
         }

    def _validate_options(self):
        super(self.__class__, self)._initializeOptions()

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # At the very beginning override the default dummy input images
        # directory by the actual images directory.
        self.f['fixed_raw_image'].override_dir = self.options.fixedImagesDir
        self.f['moving_raw_image'].override_dir = self.options.movingImagesDir

        # Override transformation directory
        if self.options.transformationsDirectory is not False:
            self.f['transf_naming'].override_dir = \
                self.options.transformationsDirectory
            self.f['transf_file'].override_dir = \
                self.options.transformationsDirectory

    @classmethod
    def _getCommandLineParser(cls):
        parser = output_volume_workflow._getCommandLineParser()

        preprocessingSettings = \
                OptionGroup(parser, 'Processing settings')

        preprocessingSettings.add_option('--startSliceIndex', default=0,
                type='int', dest='startSliceIndex',
                help='Index of the first slice of the stack')
        preprocessingSettings.add_option('--endSliceIndex', default=None,
                type='int', dest='endSliceIndex',
                help='Index of the last slice of the stack')
        preprocessingSettings.add_option('--smoothingSimga', default=5,
                type='float', dest='smoothingSimga',
                help='General smoothing simga. Can be customized for specific parameters.')
        preprocessingSettings.add_option('--smoothingSimgaRotation', default=None,
                type='float', dest='smoothingSimgaRotation', help='')
        preprocessingSettings.add_option('--smoothingSimgaScaling', default=None,
                type='float', dest='smoothingSimgaScaling', help='')
        preprocessingSettings.add_option('--smoothingSimgaOffset', default=None,
                type='float', dest='smoothingSimgaOffset', help='')
        preprocessingSettings.add_option('--smoothingSimgaFixed', default=None,
                type='float', dest='smoothingSimgaFixed', help='')
        preprocessingSettings.add_option('--transformationsFilenameTemplate', default=None,
                    type='str', dest='transformationsFilenameTemplate', help='')

        workflowSettings = \
                OptionGroup(parser, 'Workflow settings')
        workflowSettings.add_option('--outputTransformationsDirectory', default=None,
                dest='outputTransformationsDirectory', action='store',
                help='Store transformations in given directory instead of using default one.')
        workflowSettings.add_option('--reportsDirectory', default=None,
                dest='reportsDirectory', action='store',
                help='Use custom reports directory instead of using default one.')
        workflowSettings.add_option('--skipTransformsGeneration', default=False,
                dest='skipTransformsGeneration', action='store_const', const = True,
                help='')

        parser.add_option_group(workflowSettings)
        parser.add_option_group(preprocessingSettings)
        return parser


#   class CoarseFineRegistration(posProcessingElement):
#       posProcessingElement._dirTemplates.update(CLASS_SPECIFC_DIR_TEMPLATES)

#       def _initializeOptions(self):
#           posProcessingElement._initializeOptions(self)

#           # Range of images to register
#           self.options['sliceRange'] = \
#                   range(self.options['startSliceIndex'], self.options['endSliceIndex']+1)

#           # Define default smoothing kernels for different type of parameters:
#           fieldsArr = ['smoothingSimgaRotation', 'smoothingSimgaOffset', \
#                       'smoothingSimgaScaling', 'smoothingSimgaFixed']

#           for field in fieldsArr:
#               if self.options[field] == None:
#                   self.options[field] = self.options['smoothingSimga']

#       def _overrideDefaults(self):

#           # Override default output volumes directory if custom directory is provided
#           if self.options['outputTransformationsDirectory'] != None:
#               self.options['process_final_transf'] = self.options['outputTransformationsDirectory']

#           # Override default transformations directory if custom directory is provided
#           if self.options['reportsDirectory'] != None:
#               self.options['process_reports'] = self.options['reportsDirectory']

#       def launchFilter(self):
#           self._copyFineTransforms()
#           self._extractFineTransformationParamaters()
#           self._calculateSmoothedTransforms()

#           if self.options['skipTransformsGeneration'] == False :
#               self._storeSmoothedTransformations()
#               self._generateFinalTransformations()

#           self._generateReport()

#           if self.options['cleanup']:
#               logging.info(' ---> Entering cleanup.')
#               self._cleanUp(immediate = True)

#       def _copyFineTransforms(self):
#           for sliceNumber in self.options['sliceRange']:
#               self._getSingleFineTransform(sliceNumber)

#       def _getSingleFineTransform(self, sliceNumber):
#           sourceFname = self.options['transformationsFilenameTemplate'] % sliceNumber
#           targetFname = self._getImagePath(self.__c.FINE_TR, sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['inputFileMask']  = sourceFname
#           cmdDict['target'] = targetFname

#           command = COMMAND_COPY % cmdDict
#           self._executeSystem(command)

#       def _extractFineTransformationParamaters(self):
#           transformationParameters = []
#           for sliceNumber in self.options['sliceRange']:
#               transformationParameters.append(self._getSingleFineTransformationParams(sliceNumber))

#           self.parametersArray = numpy.array(transformationParameters).T

#       def _getSingleFineTransformationParams(self, sliceNumber):
#           transformationFilename = self._getImagePath(self.__c.FINE_TR, \
#                                                       sliceNumber = sliceNumber)
#           transformationString = self._loadTransformationFile(transformationFilename)
#           parameters = self._extractRigidTransformationParameters(transformationString)
#           return parameters

#       def _extractRigidTransformationParameters(self, transformationString):
#           """
#           This function assumes that itk rigid transformation file has a following structure:
#           ....
#           """
#           # Check if the string really contains a itk transformation:
#           if not transformationString[2].strip().split(':')[0] == 'Transform':
#               isTransformationStringValid = False

#           if not transformationString[3].strip().split(':')[0] == 'Parameters':
#               isTransformationStringValid = False

#           parametersString = transformationString[3].strip().split(':')[1].strip().split(' ')
#           fixed = transformationString[4].strip().split(':')[1].strip().split(' ')

#           transformationParams =  tuple(map(float, parametersString))
#           fixesParams =  tuple(map(float, fixed))
#           allParams = list(transformationParams) + list(fixesParams)

#           return allParams

#       def _loadTransformationFile(self, transformationFilename):
#           transformationFileString = open(transformationFilename).readlines()
#           return transformationFileString

#       def _calculateSmoothedTransforms(self):
#           """
#           """
#           # Just create aliases:
#           k = self.parametersArray
#           l = k.copy()

#           # Save initial transformation parameters before processing :)
#           rawParametersArrayFname = self._getImagePath(self.__c.FN_FINE_CSV)
#           self._saveParametersArray(k, rawParametersArrayFname)

#           # Smooth the initial transformation. There are three types of parameters,
#           # each of them may recieve different ammount of smoothing if required.
#           # The parameter types are: scaling (no unit), offset and fixed parametes (physical units)
#           # and translation (no unit). By default all types of parameters are smoothed
#           # with the same kernel. Using command line parameters one can customize this behaviour.

#           paramsIdx = {'fixed'    : ([6,7], self.options['smoothingSimgaFixed']   ), \
#                       'offset'   : ([4,5], self.options['smoothingSimgaOffset']  ), \
#                       'rotation' : ([1,2], self.options['smoothingSimgaRotation']), \
#                       'scaling'  : ([0,3], self.options['smoothingSimgaScaling'] ) }

#           # Apply smoothing
#           for paramIdx, sigma in paramsIdx.values():
#               for i in paramIdx:
#                   l[i,:]=gaussian_filter1d(k[i], sigma)[0:k.shape[1]]

#           # Save smoothed parameters array:
#           smoothedParametersArrayFname = self._getImagePath(self.__c.SMOOTH_CSV)
#           self._saveParametersArray(l, smoothedParametersArrayFname)

#           # Store a set of new (smoothes) transformations
#           self.smoothedParametersArray = l

#           # Store difference of two sets of transformations as well:
#           differenceParametersArrayFname = self._getImagePath(self.__c.DIFF_CSV)
#           self._saveParametersArray(k-l, differenceParametersArrayFname)

#       def _storeSmoothedTransformations(self):
#           """
#           """
#           # Just an alias:
#           l = self.smoothedParametersArray

#           for i in range(l.shape[1]):
#               sliceNumber = i + self.options['startSliceIndex']
#               outputFilename = self._getImagePath(self.__c.SMOOTH_TR,\
#                                                   sliceNumber = sliceNumber)
#               self._saveTransformationFromParams(list(l[:,i]), outputFilename)

#       def _saveParametersArray(self, parametersArray, filename):
#           numpy.savetxt(filename, parametersArray.T)

#       def _saveTransformationFromParams(self,  parameters, filename):
#           p = parameters

#           tstr =""
#           tstr += "#Insight Transform File V1.0\n"
#           tstr += "#Transform 0\n"
#           tstr += "Transform: MatrixOffsetTransformBase_double_2_2\n"
#           tstr += "Parameters: %f %f %f %f %f %f\n" % (p[0], p[1], p[2], p[3], p[4], p[5])
#           tstr += "FixedParameters: %f %f\n" % (p[6], p[7])
#           open(filename, 'w').write(tstr)

#       def _getNameSpacePrefix(self):
#           retName = "out_"

#           retName+= "_start_" + str(self.options['startSliceIndex'])
#           retName+= "_end_"   + str(self.options['endSliceIndex'])

#           retName+= "_s_" + str(self.options['smoothingSimga'])
#           retName+= "_sR_" + str(self.options['smoothingSimgaRotation'])
#           retName+= "_sO_" + str(self.options['smoothingSimgaOffset'])
#           retName+= "_sS_" + str(self.options['smoothingSimgaScaling'])
#           retName+= "_sF_" + str(self.options['smoothingSimgaFixed'])

#           return retName

#       def _generateFinalTransformations(self):
#           for sliceNumber in self.options['sliceRange']:
#               self._storeFinalTransformation(sliceNumber)

#       def _storeFinalTransformation(self, sliceNumber):
#           inputFilename = self._getImagePath(self.__c.SMOOTH_TR,\
#                                               sliceNumber = sliceNumber)

#           outputFilename= self._getImagePath(self.__c.FINAL_TR,\
#                                           sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['inputFilename']  = inputFilename
#           cmdDict['outputFilename'] = outputFilename

#           command = COMMAND_GENERATE_FINAL_TRANSFORM % cmdDict
#           self._executeSystem(command)

#       def _generateReport(self):
#           outputGraphFilename = self._getImagePath(self.__c.GRAPH)

#           differenceParametersArrayFname = self._getImagePath(self.__c.DIFF_CSV)
#           rawParametersArrayFname = self._getImagePath(self.__c.FN_FINE_CSV)
#           smoothedParametersArrayFname = self._getImagePath(self.__c.SMOOTH_CSV)

#           plotTempFilename = os.path.join(self.options['process_reports'], "tempGraph.gp")

#           cmdDict = {}
#           cmdDict['outputGraphFilename']    = outputGraphFilename
#           cmdDict['smoothedTransformFname'] = smoothedParametersArrayFname
#           cmdDict['fineTransformFname'] = rawParametersArrayFname
#           cmdDict['diffTransformFname'] = differenceParametersArrayFname

#           # Save the plot file
#           plotFileContents = COMMAND_GRAPH_REPORT % cmdDict
#           open(plotTempFilename, 'w').write(plotFileContents)

#           # Execute proviouslu generated plot file
#           cmdDict = {}
#           cmdDict['plotFilename']    = plotTempFilename

#           command = COMMAND_GENERATE_GRAPH % cmdDict
#           self._executeSystem(command)

#       def _getImagePath(self, imageType = None, **kwargs):
#           """
#           Return full path for the given file depending on its purpose.
#           """

#           if imageType == self.__c.FN_FINE_CSV:
#               directory = self.options['process_reports']
#               filename  = self.__c.FN_FINE_CSV % self._getNameSpacePrefix()
#               return os.path.join(directory, filename)

#           if imageType == self.__c.SMOOTH_CSV:
#               directory = self.options['process_reports']
#               filename  = self.__c.FN_SMOOTH_CSV % self._getNameSpacePrefix()
#               return os.path.join(directory, filename)

#           if imageType == self.__c.DIFF_CSV:
#               directory = self.options['process_reports']
#               filename  = self.__c.FN_DIFF_CSV % self._getNameSpacePrefix()
#               return os.path.join(directory, filename)

#           if imageType == self.__c.FINE_TR:
#               directory = self.options['process_fine_transf']
#               filename  = self.__c.FN_FINE_TR % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.SMOOTH_TR:
#               directory = self.options['process_smooth_transf']
#               filename  = self.__c.FN_SMOOTH_TR % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.FINAL_TR:
#               directory = self.options['process_final_transf']
#               filename  = self.__c.FN_FINAL_TR % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.GRAPH:
#               directory = self.options['process_reports']
#               filename  = self.__c.FN_GRAPH % self._getNameSpacePrefix()
#               return os.path.join(directory, filename)

#       @classmethod
#       def _getCommandLineParser(cls):
#           parser = posProcessingElement._getCommandLineParser()

#           preprocessingSettings = \
#                   OptionGroup(parser, 'Processing settings')

#           preprocessingSettings.add_option('--startSliceIndex', default=0,
#                   type='int', dest='startSliceIndex',
#                   help='Index of the first slice of the stack')
#           preprocessingSettings.add_option('--endSliceIndex', default=None,
#                   type='int', dest='endSliceIndex',
#                   help='Index of the last slice of the stack')
#           preprocessingSettings.add_option('--smoothingSimga', default=5,
#                   type='float', dest='smoothingSimga',
#                   help='General smoothing simga. Can be customized for specific parameters.')
#           preprocessingSettings.add_option('--smoothingSimgaRotation', default=None,
#                   type='float', dest='smoothingSimgaRotation', help='')
#           preprocessingSettings.add_option('--smoothingSimgaScaling', default=None,
#                   type='float', dest='smoothingSimgaScaling', help='')
#           preprocessingSettings.add_option('--smoothingSimgaOffset', default=None,
#                   type='float', dest='smoothingSimgaOffset', help='')
#           preprocessingSettings.add_option('--smoothingSimgaFixed', default=None,
#                   type='float', dest='smoothingSimgaFixed', help='')
#           preprocessingSettings.add_option('--transformationsFilenameTemplate', default=None,
#                       type='str', dest='transformationsFilenameTemplate', help='')

#           workflowSettings = \
#                   OptionGroup(parser, 'Workflow settings')
#           workflowSettings.add_option('--outputTransformationsDirectory', default=None,
#                   dest='outputTransformationsDirectory', action='store',
#                   help='Store transformations in given directory instead of using default one.')
#           workflowSettings.add_option('--reportsDirectory', default=None,
#                   dest='reportsDirectory', action='store',
#                   help='Use custom reports directory instead of using default one.')
#           workflowSettings.add_option('--skipTransformsGeneration', default=False,
#                   dest='skipTransformsGeneration', action='store_const', const = True,
#                   help='')

#           parser.add_option_group(workflowSettings)
#           parser.add_option_group(preprocessingSettings)
#           return parser

if __name__ == '__main__':
    options, args = coarse_to_fine_transformation_merger.parseArgs()
    se = coarse_to_fine_transformation_merger(options, args)
    se.launchFilter()
