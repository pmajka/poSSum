#!/usr/bin/python
import os,sys
import numpy as np

from optparse import OptionParser, OptionGroup
import copy

from pos_deformable_wrappers import preprocess_slice_volume
from pos_wrapper_skel import generic_workflow
from deformable_histology_iterations import deformable_reconstruction_iteration
import pos_wrappers
import pos_parameters

#TODO: return copy.deepcopy(registration) => return registration.get_command(), registration.command(), registration.command

class deformable_reconstruction_workflow(generic_workflow):
    """
    """
    _f = { \
        'init_images' : pos_parameters.filename('init_slice', work_dir = '01_init_slices', str_template = '/home/pmajka/Downloads/a/ANTS/trunk/Examples/Data/B{idx:01d}.tiff'),
        'init_avarage' : pos_parameters.filename('init_avarage', work_dir = '01_init_slices', str_template = '/home/pmajka/Downloads/a/ANTS/trunk/Examples/Data/average.nii.gz'),
        'average_affine_transformations' : pos_parameters.filename('average_affine_transformations',  work_dir = '03_average_affine_transformations', str_template = '{idx:04d}Affine.txt'),
        'average_affine_transformations_naming' : pos_parameters.filename('average_affine_transformations_naming',  work_dir = '03_average_affine_transformations', str_template = '{idx:04d}'),
        'init_resliced_affine' : pos_parameters.filename('init_resliced_affine',  work_dir = '04_init_resliced_affine', str_template = '{idx:04d}.nii.gz')
        }

    _usage = ""

    def __init__(self, options, args, pool = None):
        super(self.__class__, self).__init__(options, args)
        self.samples=5

    def launch(self):
        commands = []

        commands.append(self._prepare_average_for_affine())
        self.execute(commands)

        for fixd in range(self.samples):
            registration = self._get_ants_affine_transformation_command(fixd)
            commands.append(registration)
        self.execute(commands)

        commands = []
        for fixd in range(self.samples):
            commands.append(self._reslice_to_average(fixd))
        #print "\n".join(map(str, commands))
        self.execute(commands)

    def _prepare_average_for_affine(self):
        samples = range(self.samples)
        input_list = map(lambda x: self.f['init_images'](idx=x), samples)

        average_command = pos_wrappers.average_images(
                dimension = 2,
                input_images = input_list,
                output_image = self.f['init_avarage']())

        return copy.deepcopy(average_command)


    def _get_ants_affine_transformation_command(self, i):
        metrics  = []

        affine_metric = pos_wrappers.ants_intensity_meric(
                    fixed_image  = self.f['init_avarage'](),
                    moving_image = self.f['init_images'](idx=i),
                    metric = "CC",
                    weight = 1,
                    parameter = 32)

        metrics.append(copy.deepcopy(affine_metric))

        registration = pos_wrappers.ants_registration(
                    dimension = 2,
                    outputNaming = self.f['average_affine_transformations_naming'](idx=i),
                    iterations = [0],
                    transformation = ('SyN', [0.5]),
                    regularization = ('Gauss', (3.0,1.0)),
                    affineIterations = [10000, 10000],
                    continueAffine = None,
                    rigidAffine = int(False),
                    imageMetrics = metrics,
                    affineMetricType = 'CC',
                    histogramMatching = int(True),
                    allMetricsConverge = None)

        return copy.deepcopy(registration)

    def _reslice_to_average(self, i):
        reslice = pos_wrappers.ants_reslice(
            dimension = 2,
            moving_image = self.f['init_images'](idx=i),
            output_image = self.f['init_resliced_affine'](idx=i),
            reference_image = self.f['init_images'](idx=i),
            affine_list = [self.f['average_affine_transformations'](idx=i)])
        return copy.deepcopy(reslice)

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('--startSlice', default=0,
                type='int', dest='startSlice',
                help='Index of the first slice of the stack')
        parser.add_option('--endSlice', default=None,
                type='int', dest='endSlice',
                help='Index of the last slice of the stack')
        parser.add_option('--shiftIndexes', default=None,
                type='int', dest='shiftIndexes',
                help='Shift indexes of the sliced by provided number.')
        parser.add_option('--neighbourhood', default=1, type='int',
                dest='neighbourhood',  help='Neighbourhood radius to which given slices will be aligned.')
        parser.add_option('--iterations', default=10,
                type='int', dest='iterations',
                help='Number of iterations')
        parser.add_option('--startFromIteration', default=0,
                type='int', dest='startFromIteration',
                help='Iteration number from which the calculations will start.')
        parser.add_option('--inputVolume','-i', default=None,
                type='str', dest='inputVolume', nargs = 2,
                help='Input volume which undergoes smooth nonlinear reconstruction.')
        parser.add_option('--outlineVolume','-o', default=None,
                type='str', dest='outlineVolume', nargs = 2,
                help='Outline label driving the registration')
        parser.add_option('--maskedVolume','-m', default=None,
                type='str', dest='maskedVolume', nargs = 2,
                help='Custom slice mask for driving the registration')
        parser.add_option('--maskedVolumeFile', default=None,
                type='str', dest='maskedVolumeFile',
                help='File determining fixed and moving slices for custom registration.')
        parser.add_option('--registerSubset', default=None, type='str',
                dest='registerSubset',  help='registerSubset')
        parser.add_option('--outputNaming', default="_", type='str',
                dest='outputNaming', help="Ouput naming scheme for all the results")
        parser.add_option('--skipTransformations', default=False,
                dest='skipTransformations', action='store_const', const=True,
                help='Skip transformations.')
        parser.add_option('--skipSlicePreprocess', default=False,
                dest='skipSlicePreprocess', action='store_const', const=True,
                help='Skip slice preprocessing.')
        parser.add_option('--stackFinalDeformation', default=False, const=True,
                dest='stackFinalDeformation', action='store_const',
                help='Stack filnal deformation fileld.')

        regSettings = \
                OptionGroup(parser, 'Registration setttings.')

        regSettings.add_option('--antsImageMetric', default='CC',
                type='str', dest='antsImageMetric',
                help='ANTS image to image metric. See ANTS documentation.')
        regSettings.add_option('--antsImageMetricOpt', default=8,
                type='int', dest='antsImageMetricOpt',
                help='Parameter of ANTS i2i metric.')
        regSettings.add_option('--antsTransformation', default=0.15, type='float',
                dest='antsTransformation', help='Tranformations gradient step.'),
        regSettings.add_option('--antsRegularizationType', default='Gauss',
                type='str', dest='antsRegularizationType',
                help='Ants regulatization type.')
        regSettings.add_option('--antsRegularization', default=[3.0,1.0],
                type='float', nargs =2, dest='antsRegularization',
                help='Ants regulatization.')
        regSettings.add_option('--antsIterations', default="1000x1000x1000x1000x1000",
                type='str', dest='antsIterations',
                help='Number of deformable registration iterations.')

        outputVolumeSettings = \
                OptionGroup(parser, 'OutputVolumeSettings.')
        outputVolumeSettings.add_option('--outputVolumeOrigin', dest='outputVolumeOrigin',
                default=[0.,0.,0.], action='store', type='float', nargs =3, help='')
        outputVolumeSettings.add_option('--outputVolumeScalarType', default='uchar',
                type='str', dest='outputVolumeScalarType',
                help='Data type for output volume\'s voxels. Allowed values: char | uchar | short | ushort | int | uint | float | double')
        outputVolumeSettings.add_option('--outputVolumeSpacing', default=[1,1,1],
            type='float', nargs=3, dest='outputVolumeSpacing',
            help='Spacing of the output volume in mm (both grayscale and color volume).')
        outputVolumeSettings.add_option('--outputVolumeResample',
                          dest='outputVolumeResample', type='float', nargs=3, default=None,
                          help='Apply additional resampling to the volume')
        outputVolumeSettings.add_option('--outputVolumePermutationOrder', default=[0,1,2],
            type='int', nargs=3, dest='outputVolumePermutationOrder',
            help='Apply axes permutation. Permutation has to be provided as sequence of 3 integers separated by space. Identity (0,1,2) permutation is a default one.')
        outputVolumeSettings.add_option('--outputVolumeOrientationCode',  dest='outputVolumeOrientationCode', type='str',
                default='RAS', help='')
        outputVolumeSettings.add_option('--grayscaleVolumeFilename',  dest='grayscaleVolumeFilename',
                type='str', default=None)
        outputVolumeSettings.add_option('--rgbVolumeFilename',  dest='rgbVolumeFilename',
                type='str', default=None)
        outputVolumeSettings.add_option('--setInterpolation',
                          dest='setInterpolation', type='str', default=None,
                          help='<NearestNeighbor|Linear|Cubic|Sinc|Gaussian>')

        parser.add_option_group(regSettings)
        parser.add_option_group(outputVolumeSettings)

        return parser

if __name__ == '__main__':
    options, args = deformable_reconstruction_workflow.parseArgs()
    d = deformable_reconstruction_workflow(options, args)
    d.launch()
