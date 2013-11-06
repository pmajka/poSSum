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

import string
import datetime
import sys, os
from optparse import OptionParser, OptionGroup

# Defining some fixed directoties names:

DIR_TEMPLATE = {
        'sharedbf' : '/dev/shm/blockface/registration/',
        'specimen_dir' : 'data',
        'bf_bitmap' : '51_blockface_bitmap',
        'bf_reg_test' : '54_blockface_registration_attempts',
        }

DIR_TEMPLATE_REG = {
        'src_gray'  : '00_source_gray',
        'src_color' : '01_source_color',
        'transformsDir'     : '02_transforms',
        'reslicedGray' : '04_gray_resliced',
        'reslicedColor'  : '05_color_resliced'
        }

IM_RGB = 'rgb_image_mode'
IM_GRAY ='grayscale_image_mode'
IM_RAW = 'raw_image_type'
IM_SRC = 'source_image_type'
IM_RSL = 'resliced_image_type'

# -------------------------------------------------------------------
# Defining external commands templates:
# -------------------------------------------------------------------

FN_TPL_PARTIAL_TRANSFORM_PREFIX ="tr_m%(movingImageIdx)04d_f%(fixedImageIdx)04d_"
FN_TPL_MULTI_TRANSFORM_PREFIX = "ct_m%(movingImageIdx)04d_f%(fixedImageIdx)04d_"
FN_TPL_PARTIAL_TRANSFORM = FN_TPL_PARTIAL_TRANSFORM_PREFIX + "Affine.txt"
FN_TPL_MULTI_TRANSFORM = FN_TPL_MULTI_TRANSFORM_PREFIX + "Affine.txt"

FN_TPL_SOURCE = '%04d.png'
FN_TPL_GRAYSCALE_SRC = '%04d.png'
FN_TPL_COLOR_SRC = '%04d.png'
FN_TPL_COLOR_RESLICED = '%04d.nii.gz'
FN_TPL_GRAYSCALE_RESLICED = '%04d.nii.gz'

COMMAND_MKDIR = """mkdir -p %(path)s #0000DIRECTORIES"""

COMMAND_RMDIR = """rm -rfv %(path)s #0010CLEANUP """

COMMAND_EXTRACT_GRAYSCALE = \
        """convert %(inputImage)s %(crop)s \
        %(invertSourceImage)s \
        -channel %(colorChannel)s -separate \
        %(unsharpMaskFilter)s \
        %(medianFilterRadius)s \
        %(outputImage)s #0001SOURCEGRAY"""

COMMAND_EXTRACT_RGB = \
        """convert %(inputImage)s %(invertSourceImage)s %(crop)s \
        %(outputImage)s #0002SOURCECOLOR"""

COMMAND_ANTS_GENERATE_TRANSFORM = \
    """ANTS 2 -v -m %(metric)s[%(fixedImage)s,%(movingImage)s,1,%(mp)s] \
        -o %(outputPartialTransformFn)s \
        -i 0 \
        --use-Histogram-Matching \
        --number-of-affine-iterations 10000x10000x10000x10000x10000 \
        --rigid-affine %(rigidAffineSetting)s \
        --affine-metric-type %(metric)s \
        %(addAntsParam)s \
        #0003ANTSTRANSFORM"""

COMMAND_WARP_RGB_SLICE = """c2d -verbose %(referenceImgFilename)s -as ref -clear \
       -mcs %(movingImageFilename)s\
       -as b \
       -pop -as g \
       -pop -as r \
       -push ref -push r -reslice-itk %(transformFilename)s %(region)s %(invertImage)s -as rr -clear \
       -push ref -push g -reslice-itk %(transformFilename)s %(region)s %(invertImage)s -as rg -clear \
       -push ref -push b -reslice-itk %(transformFilename)s %(region)s %(invertImage)s -as rb -clear \
       -push rr -push rg -push rb -omc 3 %(outImageFilename)s \
       #0006WRAPRGB"""

COMMAND_COMPOSE_MULTI_TRANSFORM = \
    """ComposeMultiTransform 2 %(outputTransformFilename)s \
    %(inputTransformsFilenamesList)s #0004COMPOSETRANSFORM"""

COMMAND_WARP_GRAYSCALE_SLICE = \
"""c2d -verbose\
        %(referenceImgFilename)s  -as ref -clear \
        %(movingImageFilename)s -as moving \
        -push ref -push moving -reslice-itk %(transformFilename)s \
        %(region)s \
        -o %(outImageFilename)s #0005WRAPGRAY"""

COMMAND_STACK_SLICES_GRAY = \
        """StackSlices %(volumeTempFn)s -1 -1 0 %(stackMask)s ;\
        reorientImage.py -i %(volumeTempFn)s \
             --permutationOrder %(permutationOrder)s \
             --orientationCode %(orientationCode)s \
             --outputVolumeScalarType %(outputVolumeScalarType)s \
             --setSpacing %(spacing)s \
             --setOrigin %(origin)s \
             -o %(volumeOutputFn)s \
             --cleanup | bash -xe ;\
            rm %(volumeTempFn)s; #0007STACKGRAY"""

COMMAND_STACK_SLICES_RGB = \
        """stack_rgb_slices.py -f %(stackMask)s \
        -b %(sliceStart)d -e %(sliceEnd)d \
        -o %(volumeTempFn)s ;\
        reorientImage.py -i %(volumeTempFn)s \
             --permutationOrder %(permutationOrder)s \
             --orientationCode %(orientationCode)s \
             --outputVolumeScalarType %(outputVolumeScalarType)s \
             --setSpacing %(spacing)s \
             --multichannelImage \
             --setOrigin %(origin)s \
             -o %(volumeOutputFn)s \
             | bash -xe ;\
            rm %(volumeTempFn)s; #0008STACKRGB"""

COMMAND_ANALYZE_TRANSFORM = \
        """transformationAnalyzer.py %(inputTransformationList)s \
        --graphTitleString %(graphTitleString)s \
        --outputFile %(outputFile)s \
        --disableSharedMemory \
        --cleanup #0007STACKGRAY"""

COMMAND_DUMP_TRANSFORMATIONS = \
        """cp -v %(transformationFilesMask)s %(targetDirectory)s \
        #0007STACKGRAY"""

def ensureDir(path):
    cmdDict = {'path':path}
    command = COMMAND_MKDIR % cmdDict
    executeSystem(command)

def rmdir(path):
    cmdDict = {'path':path}
    command = COMMAND_RMDIR % cmdDict
    executeSystem(command)

def executeSystem(commandString):
    """
    'Safely' executes given C{commandString} raising exception when nonzero value is returned from shell.
    """

#    print "Executing: ", commandString
    print commandString
    #if os.system(commandString):
    #    raise ValueError, "Nonzero status reutrned."

class registerBlockfaceFilter():
    """
    This class handles the linear (either affine or rigid) registration of 2-D
    bitmap inages and merging the registared images into a volume. The process
    is complex and multistep and involves preparing the source bitmap,
    extracting particular color channels, resiging assigning orientation,
    registering and merging into volumes (both grayscale and rgb).

    The registration process is firmly connected with the possum atlas data
    architecture and organization including specimen id's and directory
    structure.
    """
    def __init__(self, options, args):
        """
        """
        # Store filter configuration withing the class instance
        if type(options) != type({}):
            self.options = eval(str(options))
        else:
            self.options = options

        self.options['specimenId'] = args[0]
        self._initializeOptions()
        self._initializeDirectories()

    def _initializeOptions(self):
        """
        Initialize processing options and registration parameters. Fill out the
        parameters that were not provided resulting in complete processing
        configuration.
        """

        # Job ID is the (not necessarily uniqe but rather rare) identifier of
        # the calcualtion's instance
        if self.options['jobId'] == None:
            self.options['jobId'] = datetime.datetime.now().strftime("%Y-%m-%d-%H_%M-%S_")

        # Range of images to register
        self.options['sliceRange'] = \
                range(self.options['startSliceIndex'], self.options['endSliceIndex']+1)

        # If true, the grayscale image processing will be disregarded
        if self.options['skipGrayReslice'] == True:
            self.resliceGrayscale = False
        else:
            self.resliceGrayscale = True

        # If true, the multichannel image processing workflow will be
        # disregarded
        if self.options['skipColorReslice'] == True:
            self.resliceColor = False
        else:
            self.resliceColor = True

        # Provide reference slice index. The reference slice is the slice to
        # which all the other slices are registered.
        if self.options['referenceSliceIndex'] == None:
            self.options['referenceSliceIndex'] = self.options['startSliceIndex']

    def _initializeDirectories(self):
        """
        Create directory structure. The calculation may be performed either
        using Lunix shared memory area (RAM disk) or temponary directory.
        """

        if self.options['disableSharedMemory']:
            self.options['jobdir'] = \
                    os.path.join(DIR_TEMPLATE['specimen_dir'], \
                                 self.options['specimenId'], \
                                 DIR_TEMPLATE['bf_reg_test'], \
                                 self.options['jobId'])
            self.options['jobdirhd'] = self.options['jobdir']
        else:
            self.options['jobdir'] = \
                    os.path.join(DIR_TEMPLATE['sharedbf'], \
                                 self.options['specimenId'], \
                                 DIR_TEMPLATE['bf_reg_test'], \
                                 self.options['jobId'])
            self.options['jobdirhd'] = \
                    os.path.join(DIR_TEMPLATE['specimen_dir'], \
                                 self.options['specimenId'], \
                                 DIR_TEMPLATE['bf_reg_test'], \
                                 self.options['jobId'])

        ensureDir(self.options['jobdir'])
        ensureDir(self.options['jobdirhd'])

        # Define directory for the registration output and evaluation
        # (if custom output directory name is provided), otherwise
        # use default values.
        if self.options['outputVolumesDirectory']:
            self.options['jobdirhd'] = \
                    self.options['outputVolumesDirectory']

        # Define directory with the source data
        if self.options['sourceSlicesDirectory']:
            self.options['sourceSlicesDir'] = \
                    self.options['sourceSlicesDirectory']
        else:
            self.options['sourceSlicesDir'] = \
                    os.path.join(\
                        DIR_TEMPLATE['specimen_dir'], \
                        self.options['specimenId'], \
                        DIR_TEMPLATE['bf_bitmap'])

        self._jobDirList = ['src_gray', 'src_color', 'transformsDir', 'reslicedGray', 'reslicedColor']
        for jobDir in self._jobDirList:
            self.options[jobDir] = \
                os.path.join(self.options['jobdir'], DIR_TEMPLATE_REG[jobDir])
            ensureDir(self.options[jobDir])

        # Override default transformation directory with the custom one if
        # custom directory name is provided
        if self.options['transformationsDirectory']:
            self.options['transformsDir'] = self.options['transformationsDirectory']
            ensureDir(self.options['transformsDir'])

    def _generateSourceSlices(self):
        self._generateSourceGrayscaleSlices()
        if self.resliceColor: self._generateSourceColorSlices()

    def _generateSourceGrayscaleSlices(self):
        for sliceNumber in self.options['sliceRange']:
            self._getSingleGrayscaleSlice(sliceNumber)

    def _generateSourceColorSlices(self):
        for sliceNumber in self.options['sliceRange']:
            self._getSingleColorSlice(sliceNumber)

    def _calculateTransforms(self):
        """
        """
        # The two loops below have to stay separated

        # Calculate partial transforms;
        for movingSliceNumber in self.options['sliceRange']:
            self._calculateSinglePartialTransform(movingSliceNumber)

        # Calculatce composite transforms
        for movingSliceNumber in self.options['sliceRange']:
            self._calculateSingleComposedTransform(movingSliceNumber)

    def _reslice(self):
        for sliceNumber in self.options['sliceRange']:
            if self.resliceGrayscale: self._resliceGrayscale(sliceNumber)
            if self.resliceColor: self._resliceColor(sliceNumber)

    def _resliceGrayscale(self, sliceNumber):
        movingImageFilename = self._getImagePath(sliceNumber, IM_SRC, IM_GRAY)
        reslicedImageFilename = self._getImagePath(sliceNumber, IM_RSL, IM_GRAY)
        referenceImageFilename = self._getImagePath(self.options['referenceSliceIndex'], IM_SRC, IM_GRAY)
        cTransformOutputFn = self._getCompositeTransformFn(sliceNumber)

        cmdDict = {}
        cmdDict['movingImageFilename'] = movingImageFilename
        cmdDict['outImageFilename']    = reslicedImageFilename
        cmdDict['referenceImgFilename']= referenceImageFilename
        cmdDict['transformFilename']   = cTransformOutputFn
        cmdDict['region'] = self._getOutputVolumeROIstr(strType = 'c2d')

        command = COMMAND_WARP_GRAYSCALE_SLICE % cmdDict
        executeSystem(command)

    def _resliceColor(self, sliceNumber):
        movingImageFilename = self._getImagePath(sliceNumber, IM_SRC, IM_RGB)
        reslicedImageFilename = self._getImagePath(sliceNumber, IM_RSL, IM_RGB)
        referenceImageFilename = self._getImagePath(self.options['referenceSliceIndex'], IM_SRC, IM_GRAY)
        cTransformOutputFn = self._getCompositeTransformFn(sliceNumber)

        cmdDict = {}
        cmdDict['movingImageFilename']  = movingImageFilename
        cmdDict['outImageFilename']     = reslicedImageFilename
        cmdDict['referenceImgFilename'] = referenceImageFilename
        cmdDict['transformFilename']    = cTransformOutputFn
        cmdDict['region'] = self._getOutputVolumeROIstr(strType = 'c2d')
        cmdDict['spacing'] = " "

        if self.options['invertMultichannelImage']:
            cmdDict['invertImage'] = \
                    ' -scale -1 -shift 255 -type uchar'
        else:
             cmdDict['invertImage'] = ''

        command = COMMAND_WARP_RGB_SLICE % cmdDict
        executeSystem(command)

    def _getGenericTransformFn(self,  movingSliceIdx, fixedSliceIdx, nameTplt):
        transformsDirectory = self.options['transformsDir']
        transformFnameDict = {}
        transformFnameDict['movingImageIdx'] = movingSliceIdx
        transformFnameDict['fixedImageIdx']  = fixedSliceIdx
        transformFn = nameTplt % transformFnameDict
        return os.path.join(transformsDirectory, transformFn)

    def _getCompositeTransformFn(self, sliceNumber):
        moving = sliceNumber
        fixed  = self.options['referenceSliceIndex']
        fnTemplate = FN_TPL_MULTI_TRANSFORM
        return self._getGenericTransformFn(moving, fixed, fnTemplate)

    def _getPartialTransformFn(self, movingSliceIdx, fixedSliceIdx):
        moving = movingSliceIdx
        fixed  = fixedSliceIdx
        fnTemplate = FN_TPL_PARTIAL_TRANSFORM
        return self._getGenericTransformFn(moving, fixed, fnTemplate)

    def _getPartialTransformFnPrefix(self, movingSliceIdx, fixedSliceIdx):
        moving = movingSliceIdx
        fixed  = fixedSliceIdx
        fnTemplate = FN_TPL_PARTIAL_TRANSFORM_PREFIX
        return self._getGenericTransformFn(moving, fixed, fnTemplate)

    def _getImagePath(self, sliceNumber, imageType = IM_SRC, imageMode = IM_GRAY):
        if imageType == IM_RAW:
            filename = FN_TPL_SOURCE % sliceNumber
            directory = self.options['sourceSlicesDir']
            return os.path.join(directory, filename)

        if imageType == IM_SRC and imageMode == IM_GRAY:
            filename = FN_TPL_GRAYSCALE_SRC % sliceNumber
            directory = self.options['src_gray']
            return os.path.join(directory, filename)

        if imageType == IM_SRC and imageMode == IM_RGB:
            filename = FN_TPL_COLOR_SRC % sliceNumber
            directory = self.options['src_color']
            return os.path.join(directory, filename)

        if imageType == IM_RSL and imageMode == IM_GRAY:
            filename = FN_TPL_GRAYSCALE_RESLICED % sliceNumber
            directory = self.options['reslicedGray']
            return os.path.join(directory, filename)

        if imageType == IM_RSL and imageMode == IM_RGB:
            filename = FN_TPL_COLOR_RESLICED % sliceNumber
            directory = self.options['reslicedColor']
            return os.path.join(directory, filename)

    def _getSingleGrayscaleSlice(self, sliceNumber):
        inputFilename = self._getImagePath(sliceNumber, IM_RAW)
        outputFilename =  self._getImagePath(sliceNumber, IM_SRC, IM_GRAY)

        cmdDict = {}
        cmdDict['crop']   = self._getRegistrationROIstr()
        cmdDict['colorChannel'] = self.options['registrationColorChannel']
        cmdDict['inputImage']  = inputFilename
        cmdDict['outputImage'] = outputFilename

        if self.options['unsharpMaskFilterString']:
            cmdDict['unsharpMaskFilter'] = \
             ' -unsharp ' + self.options['unsharpMaskFilterString']
        else:
             cmdDict['unsharpMaskFilter'] = ''

        if self.options['medianFilterRadius']:
            cmdDict['medianFilterRadius'] = \
             ' -median ' + self.options['medianFilterRadius']
        else:
             cmdDict['medianFilterRadius'] = ''

        if self.options['invertSourceImage']:
            cmdDict['invertSourceImage'] = \
             ' -negate '
        else:
             cmdDict['invertSourceImage'] = ''

        command = COMMAND_EXTRACT_GRAYSCALE % cmdDict
        executeSystem(command)

    def _getSingleColorSlice(self, sliceNumber):
        inputFilename = self._getImagePath(sliceNumber, IM_RAW)
        outputFilename=self._getImagePath(sliceNumber, IM_SRC, IM_RGB)

        cmdDict = {}
        cmdDict['crop']   = self._getRegistrationROIstr()
        cmdDict['inputImage']  = inputFilename
        cmdDict['outputImage'] = outputFilename

        if self.options['invertSourceImage']:
            cmdDict['invertSourceImage'] = \
             ' -negate '
        else:
             cmdDict['invertSourceImage'] = ''

        command = COMMAND_EXTRACT_RGB % cmdDict
        executeSystem(command)

    def _getPartialTransform(self, movingSliceNumber):
        i = movingSliceNumber
        s = self.options['startSliceIndex']
        e = self.options['endSliceIndex']
        r = self.options['referenceSliceIndex']

        retDict= []
        if i==r:
            j=i
            retDict.append((i, j))
        if i > r:
            j = i-1
            retDict.append((i, j))
        if i < r:
            j = i+1
            retDict.append((i, j))
        return retDict

    def _calculateSinglePartialTransform(self, movingSliceNumber):
        tChain = self._getPartialTransform(movingSliceNumber)
        movingSliceNumber, fixedSliceNumber = tChain[0]

        fixedImageFilename = self._getImagePath(fixedSliceNumber, IM_SRC, IM_GRAY)
        movingImageFilename = self._getImagePath(movingSliceNumber, IM_SRC, IM_GRAY)
        partialTransformFilename = \
               self._getPartialTransformFnPrefix(movingSliceNumber, fixedSliceNumber)

        cmdDict = {}
        cmdDict['fixedImage'] = fixedImageFilename
        cmdDict['movingImage'] = movingImageFilename
        cmdDict['outputPartialTransformFn'] = partialTransformFilename
        cmdDict['mp']     = self.options['antsImageMetricOpt']
        cmdDict['metric'] = self.options['antsImageMetric']
        cmdDict['rigidAffineSetting'] = \
                str(self.options['useRigidAffine']).lower()

        # Pass additional ANTS registration parameters (if provided). The string
        # is initialized as empty.
        cmdDict['addAntsParam'] = ""
        if self.options['additionalAntsParameters']:
            cmdDict['addAntsParam'] = self.options['additionalAntsParameters']

        command = COMMAND_ANTS_GENERATE_TRANSFORM % cmdDict
        executeSystem(command)

    def _getComposedTransformationChain(self, movingSliceNumber):
        i = movingSliceNumber
        s = self.options['startSliceIndex']
        e = self.options['endSliceIndex']
        r = self.options['referenceSliceIndex']

        retDict = []

        if i==r:
            retDict.append((i, i))
        if i > r:
            for j in list(reversed([j  for j in range(r, i) ])):
                retDict.append((j+1, j))
        if i < r:
            for j in range(i, r):
                retDict.append((j, j+1))
        return retDict

    def _calculateSingleComposedTransform(self, movingSliceNumber):
        tChain = self._getComposedTransformationChain(movingSliceNumber)
        transformationListString = ""

        for (mSlice, rSlice) in tChain:
           transformationListString += \
                   " " +self._getPartialTransformFn(mSlice, rSlice)

        cTransformOutputFn = self._getCompositeTransformFn(movingSliceNumber)

        cTransformationCommandStr = {}
        cTransformationCommandStr['outputTransformFilename'] = cTransformOutputFn
        cTransformationCommandStr['inputTransformsFilenamesList'] = transformationListString

        command = COMMAND_COMPOSE_MULTI_TRANSFORM % cTransformationCommandStr
        executeSystem(command)

    def _getOutputVolumeROIstr(self, strType = 'imagemagic'):
        return self._getRegionDescriptionString(\
                self.options['outputVolumeROI'],
                self.options['outputVolumeResize'],
                strType)

    def _getRegistrationROIstr(self, strType = 'imagemagic'):
        return self._getRegionDescriptionString(\
                self.options['registrationROI'],
                self.options['registrationResize'],
                strType)

    def _getRegionDescriptionString(self, regionROI, regionResize, strType = 'imagemagic'):
        """
        regionROI: (x1, y1, x2, y2)
        regionResize: 0.xx
        """
        if regionROI != None:
            ox, oy, sx, sy = regionROI

        if regionResize != None:
            resize = int(regionResize * 100.)
        else:
            resize = None

        retStr=" "
        if strType == 'imagemagic':
            if regionROI != None:
                retStr = ' -crop %dx%d+%d+%d ' % (sx, sy, ox, oy)
            if resize != None:
                retStr+= "-resize %d%% " % resize

        if strType == 'c2d':
            if regionROI != None:
                retStr = ' -region %dx%dvox %dx%dvox ' % (ox, oy, sx, sy)
            if resize != None:
                retStr+= "-interpolation Cubic -resample %d%% " % resize

        return retStr

    def _getOutputVolumeName(self, volumeType=IM_GRAY, extension='.nii.gz'):
        retName = "out_vol_"
        if volumeType==IM_GRAY: retName+="gray"
        if volumeType==IM_RGB:  retName+="rgb"
        retName+= "_rC_" + self.options['registrationColorChannel']
        try:
            retName+= "_rROI_" + "x".join(map(str, self.options['registrationROI']))
        except:
            retName+= "_rROI_" + str(self.options['registrationROI'])
        retName+= "_rS_" + str(self.options['registrationResize'])
        retName+= "_rM_" + self.options['antsImageMetric']
        retName+= "_rMP_" + str(self.options['antsImageMetricOpt'])
        retName+= "_rRS_" + str(self.options['referenceSliceIndex'])
        try:
            retName+= "_oROI_" + "x".join(map(str, self.options['outputVolumeROI']))
        except:
            retName+= "_oROI_" + str(self.options['outputVolumeROI'])
        retName+= "_oS_" + str(self.options['outputVolumeResize'])
        retName+= "_med" + str(self.options['medianFilterRadius'])
        retName+= extension

        return retName

    def _generateTransformationReportChart(self):
        """
        Generate a chart illustrating translations and rotations for a given
        transformation chain using extranal python script.
        """
        # Get list of names of all files containing composed transforms
        composedTransformsList = \
                map(lambda x: self._getCompositeTransformFn(x), \
                              self.options['sliceRange'])
        transfomrationChainFilemask = " ".join(composedTransformsList)

        # Define title of the plot and the resulting plot filename
        reportPlotTitle = self._getOutputVolumeName(extension='.png')
        hdDir = self.options['jobdirhd']
        reportPlotOutFilename = os.path.join(hdDir, reportPlotTitle)

        cmdDict = {}
        cmdDict['inputTransformationList'] = transfomrationChainFilemask
        cmdDict['graphTitleString'] = reportPlotTitle
        cmdDict['outputFile'] = reportPlotOutFilename

        command = COMMAND_ANALYZE_TRANSFORM % cmdDict
        executeSystem(command)

    def _dumpTransformations(self):

        pass

    def _mergeOutput(self):
        """
        Merge registered and resliced images into consitent volume with assigned
        voxel spacing. Grayscale as well as multichannel volumes are created.
        """

        # Generate names of the output volume. The names are combination of the
        # processing options.
        grayVolumeName = self._getOutputVolumeName()
        colorVolumeName= self._getOutputVolumeName(volumeType=IM_RGB)

        # Override default output volume names with the custom names:
        if self.options['grayscaleVolumeFilename'] != None:
            grayVolumeName = self.options['grayscaleVolumeFilename']

        if self.options['rgbVolumeFilename'] != None:
            colorVolumeName = self.options['rgbVolumeFilename']

        # Directory on the hard drive where volumes are to be stored.
        hdDir = self.options['jobdirhd']

        cmdDict = {}
        cmdDict['stackMask']      = os.path.join(self.options['reslicedColor'],FN_TPL_COLOR_RESLICED)
        cmdDict['sliceStart']     = self.options['startSliceIndex']
        cmdDict['sliceEnd']       = self.options['endSliceIndex']
        cmdDict['spacing']        = " ".join(map(str, self.options['outputVolumeSpacing']))
        cmdDict['origin']         = " ".join(map(str, self.options['outputVolumeOrigin']))
        cmdDict['volumeTempFn']   =  os.path.join(self.options['jobdir'],'__temp__rgbvol.vtk')
        cmdDict['volumeOutputFn'] =  os.path.join(hdDir, colorVolumeName)
        cmdDict['permutationOrder'] = " ".join(map(str, self.options['outputVolumePermutationOrder']))
        cmdDict['orientationCode'] = self.options['outputVolumeOrientationCode']
        cmdDict['outputVolumeScalarType'] = self.options['outputVolumeScalarType']

        if not self.options['skipColorReslice']:
            command = COMMAND_STACK_SLICES_RGB % cmdDict
            executeSystem(command)

        # There is no need to rebuild the command dictionary for the grayscale
        # volume
        cmdDict['stackMask']      = os.path.join(self.options['reslicedGray'],"*")
        cmdDict['volumeOutputFn'] = os.path.join(hdDir, grayVolumeName)

        if not self.options['skipGrayReslice']:
            command = COMMAND_STACK_SLICES_GRAY % cmdDict
            executeSystem(command)

    def _cleanUp(self):
        if self.options['disableSharedMemory']:
            map(lambda x: rmdir(self.options[x]), self._jobDirList)
        else:
            rmdir(self.options['jobdir'])

    def launchFilter(self):
        """
        Launch the filter and do all the processing according to provided
        processing directives. Briefly, the implemented workflow is following:

           1. Process the raw, source bitmap into images ready to registration.
              This incorporates cropping, rescaling, extracting single color
              channel for registration and preparing color slices as well.
           2. Calculate transforms using prepared grayscale slices. Chainlike
              registration paradigm is incorporated. Merge the transformation
              chain to establish final transformation every individual image.
           3. Reslice source grayscale and multichannel images according to
              calculated transforms.
           4. Stack the grayscale and multichannel images into volumes, assing
              spacing and copy to their final location. Then, do a cleanup.
        """

        if not self.options['skipSourceSlicesGeneration']:
            self._generateSourceSlices()

        if not self.options['skipTransformations']:
            self._calculateTransforms()

        self._reslice()
        self._mergeOutput()
        self._generateTransformationReportChart()
        if self.options['cleanup']:
            self._cleanUp()

def parseArgs():
    usage = "register_blockface.sh [options] specimenId"

    parser = OptionParser(usage = usage)

    registrationOptions = OptionGroup(parser, 'Registration options')
    registrationOptions.add_option('--startSliceIndex', '-s', default=0,
                        type='int', dest='startSliceIndex',
                        help='Index of the first slice of the stack')
    registrationOptions.add_option('--referenceSliceIndex', '-r', default=None,
                        type='int', dest='referenceSliceIndex',
                        help='Index of slice to which all slices will be aligned.')
    registrationOptions.add_option('--endSliceIndex', '-e', default=None,
                        type='int', dest='endSliceIndex',
                        help='Index of the last slice of the stack')
    registrationOptions.add_option('--registrationROI', default=None,
                        type='int', dest='registrationROI',  nargs=4,
                        help='ROI of the input image used for registration')
    registrationOptions.add_option('--registrationResize', default=None,
                        type='float', dest='registrationResize',
                        help='Scaling factor for the source image used for registration. Float between 0 and 1.')
    registrationOptions.add_option('--registrationColorChannel', default='blue',
                        type='str', dest='registrationColorChannel',
                        help='In rgb images - color channel on which \
                        registration will be performed. Has no meaning for \
                        grayscale input images. Possible values: r/red, g/green, b/blue.')
    registrationOptions.add_option('--antsImageMetric', default='MI',
                        type='str', dest='antsImageMetric',
                        help='ANTS image to image metric. See ANTS documentation.')
    registrationOptions.add_option('--antsImageMetricOpt', default=32,
                        type='int', dest='antsImageMetricOpt',
                        help='Parameter of ANTS i2i metric.')
    registrationOptions.add_option('--additionalAntsParameters', default=None,
                        type='str', dest='additionalAntsParameters',  help='Addidtional ANTS command line parameters (provide within quote: "")')
    registrationOptions.add_option('--useRigidAffine', default=False,
            dest='useRigidAffine', action='store_const', const=True,
            help='Use rigid affine transformation.')

    outputOptions = OptionGroup(parser, 'Output results options')
    outputOptions.add_option('--outputVolumeSpacing', default=[1,1,1],
            type='float', nargs=3, dest='outputVolumeSpacing',
            help='Spacing of the output volume in mm (both grayscale and color volume).')
    outputOptions.add_option('--outputVolumeOrigin', default=[0,0,0],
            type='float', nargs=3, dest='outputVolumeOrigin',
            help='Origin of the output volume in mm (both grayscale and color volume).')
    outputOptions.add_option('--outputVolumeROI', default=None,
            type='int', dest='outputVolumeROI',  nargs=4,
            help='ROI of the output volume - in respect to registration ROI.')
    outputOptions.add_option('--outputVolumeResize', default=None,
            type='float', dest='outputVolumeResize',
            help='Scaling of the output volume - in respect to registration ROI. Float between 0 and 1.')
    outputOptions.add_option('--outputVolumeScalarType', default=None,
            type='str', dest='outputVolumeScalarType',
            help='Data type for output volume\'s voxels. Allowed values: char | uchar | short | ushort | int | uint | float | double')
    outputOptions.add_option('--grayscaleVolumeFilename',  dest='grayscaleVolumeFilename',
            type='str', default=None)
    outputOptions.add_option('--rgbVolumeFilename',  dest='rgbVolumeFilename',
            type='str', default=None)
    outputOptions.add_option('--outputVolumePermutationOrder', default=[0,1,2],
            type='int', nargs=3, dest='outputVolumePermutationOrder',
            help='Apply axes permutation. Permutation has to be provided as sequence of 3 integers separated by space. Identity (0,1,2) permutation is a default one.')
    outputOptions.add_option('--outputVolumeOrientationCode',  dest='outputVolumeOrientationCode', type='str',
            default='RAS', help='')

    dataPreparationOptions= OptionGroup(parser, 'Source data preprocessing options')

    dataPreparationOptions.add_option('--unsharpMaskFilterString', default=None,
            dest='unsharpMaskFilterString', type='str',
            help='Unsharp mask filter properties according to ImageMagick syntax.')
    dataPreparationOptions.add_option('--medianFilterRadius', default=None,
            dest='medianFilterRadius', type='str',
            help='Median filter radius according to ImageMagick syntax.')
    dataPreparationOptions.add_option('--invertSourceImage', default=False,
            dest='invertSourceImage',  action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
    dataPreparationOptions.add_option('--invertMultichannelImage', default=False,
            dest='invertMultichannelImage',  action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')

    generalOptions = OptionGroup(parser, 'General workflow options')

    generalOptions.add_option('--sourceSlicesDirectory', default=False,
            dest='sourceSlicesDirectory', type="str",
            help='Use custom souce slices dictionay instead uf using defailt one.')
    generalOptions.add_option('--outputVolumesDirectory', default=False,
            dest='outputVolumesDirectory', type="str",
            help='Directory to which registration results will be sored.')
    generalOptions.add_option('--transformationsDirectory', default=False,
            dest='transformationsDirectory', type="str",
            help='Use provided transformation directory instead of the default one.')
    generalOptions.add_option('--skipTransformations', default=False,
            dest='skipTransformations', action='store_const', const=True,
            help='Supress transformation calculation')
    generalOptions.add_option('--skipSourceSlicesGeneration', default=False,
            dest='skipSourceSlicesGeneration', action='store_const', const=True,
            help='Supress generation source slices')
    generalOptions.add_option('--skipGrayReslice', default=False,
            dest='skipGrayReslice', action='store_const', const=True,
            help='Supress generating grayscale volume')
    generalOptions.add_option('--skipColorReslice', default=False,
            dest='skipColorReslice', action='store_const', const=True,
            help='Supress generating color volume')
    generalOptions.add_option('--cleanup', default=False,
            dest='cleanup', action='store_const', const=True,
            help='Remove all temporary direcotries.')
    generalOptions.add_option('--jobId', '-j', default=None,
            dest='jobId',
            help='Job name. Any reasonable string will work')
    generalOptions.add_option('--disableSharedMemory', default=False,
            dest='disableSharedMemory', action='store_const', const=True,
            help='Forces script to write data on the hard drive instaed of using shared memory')

    parser.add_option_group(generalOptions)
    parser.add_option_group(outputOptions)
    parser.add_option_group(registrationOptions)
    parser.add_option_group(dataPreparationOptions)

    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.print_help()
        exit()
    return (options, args)


if __name__ == '__main__':
    options, args = parseArgs()
    reg = registerBlockfaceFilter(options, args)
    reg.launchFilter()
