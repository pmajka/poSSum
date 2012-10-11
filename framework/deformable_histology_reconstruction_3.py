#!/usr/bin/python

import sys, os
import multiprocessing
import subprocess as sub
import numpy as np

import time, datetime
from optparse import OptionParser, OptionGroup
import copy

from pos_parameters import mkdir_wrapper, rmdir_wrapper, images_weighted_average, \
        ants_intensity_meric, ants_registration, ants_reslice, stack_slices_gray_wrapper

from pos_deformable_wrappers import preprocess_slice_volume, blank_slice_deformation_wrapper
from pos_filenames import filename
from pos_wrapper_skel import generic_workflow

def execute_callable(callable):
    return callable()

class deformable_reconstruction_iteration(generic_workflow):
    _f = { \
        'src_slice'  : filename('src_slice',  work_dir = '00_src_slices',      str_template =  '{idx:04d}.nii.gz'),
        'processed'  : filename('processed',  work_dir = '01_process_slices',  str_template =  '{idx:04d}.nii.gz'),
        'outline'    : filename('outline',    work_dir = '02_outline',         str_template =  '{idx:04d}.nii.gz'),
        'transform'  : filename('transform',  work_dir = '11_transformations', str_template =  '{idx:04d}Warp.nii.gz'),
        'out_naming' : filename('out_naming', work_dir = '11_transformations', str_template = '{idx:04d}'),
        'resliced'   : filename('resliced',   work_dir = '21_resliced',        str_template = '{idx:04d}.nii.gz'),
        'resliced_outline' : filename('resliced', work_dir = '22_resliced_outline', str_template = '{idx:04d}.nii.gz')
        }
    
    _usage = ""
    
    def __init__(self, options, args, pool = None):
        super(self.__class__, self).__init__(options, args, pool)
        
        start, end, eps = self._get_edges()
        self.slice_range = range(start, end +1)
        
        self._load_subset_file()
       
        # Convert the number of iterations string to list of integers
        self.options.antsIterations = \
                map(int, self.options.antsIterations.strip().split("x"))
    
    def _get_edges(self):
        """
        Convenience function for returning frequently used numbers
        """
        return (self.options.startSlice,
                self.options.endSlice,
                self.options.neighbourhood)

    def _load_subset_file(self):
        if self.options.registerSubset:
            subset = np.loadtxt(self.options.registerSubset)
            self.subset = list(subset)
        else:
            self.subset = self.slice_range
    
    def _assign_weights_from_func(self):
        start, end, eps = self._get_edges()
        
        self.weights = {}
        for i in self.slice_range:
            for j in range(i - eps, i + eps+1):
                if j!=i and j<=end and j>=start:
                    self.weights[(i,j)] = 1
    
    def get_weight(self, i, j):
        if self.options.weightsFile:
            return self.weights_from_file[j]
        else:
            return self.weights[(i,j)]
    
    def _assign_weights_from_file(self):
        """
        """
        # File is constructed as follows:
        # Col(0) slice no.
        # Col(1) - Col(n) weight for slice in col 0 for iteration j
        # But for the first time we use constant weights for
        # every iteration
        weights = np.loadtxt(self.options.weightsFile)
        self.weights_from_file = dict(map(lambda x: (int(x[0]), x[1]), weights))
    
    def _assign_weights(self):
        if self.options.weightsFile:
            self._assign_weights_from_file()
        else:
            self._assign_weights_from_func()
    
    def _average_images(self):
        start, end, eps = self._get_edges()
        
        commands = []
        
        for i in self.slice_range:
            files_to_average = []
            weights = []
            
            for j in range(i - eps, i + eps+1):
                if j!=i and j<=end and j>=start:
                   files_to_average.append(self.f['src_slice'](idx=j))
                   weights.append(self.get_weight(i,j))
            
            command = images_weighted_average(\
                        dimension = 2,
                        input_images = files_to_average,
                        weights = weights,
                        output_type = 'float',
                        output_image = self.f['processed'](idx=i))
            commands.append(copy.deepcopy(command))
        
        self.execute(commands)
    
    def _calculate_transformations(self):
        start, end, eps = self._get_edges()
        
        commands = []
        metrics  = []
        
        for i in self.slice_range:
            metric = ants_intensity_meric(
                        fixed_image  = self.f['processed'](idx=i),
                        moving_image = self.f['src_slice'](idx=i),
                        metric = self.options.antsImageMetric,
                        weight = 1,
                        parameter = self.options.antsImageMetricOpt)
            
            if i in self.subset:
                registration = ants_registration(
                            dimension = 2,
                            outputNaming = self.f['out_naming'](idx=i),
                            iterations = self.options.antsIterations,
                            transformation = ('SyN', [self.options.antsTransformation]),
                            regularization = (self.options.antsRegularizationType, self.options.antsRegularization),
                            affineIterations = [0],
                            continueAffine = False,
                            rigidAffine = False,
                            imageMetrics = [metric])
            else:
                registration = blank_slice_deformation_wrapper(\
                        input_image = self.f['src_slice'](idx=i),
                        output_image = self.f['transform'](idx=i)
                        )
            
            commands.append(copy.deepcopy(registration))
        
        self.execute(commands)
    
    def launch(self):
        self._assign_weights()
        self._average_images()
        self._calculate_transformations()
     
    def __call__(self, *args, **kwargs):
        return self.launch()
    
class deformable_reconstruction_workflow(generic_workflow):
    _f = { \
         # Initial grayscale slices
        'init_slice' : filename('init_slice', work_dir = '01_init_slices', str_template = '{idx:04d}.nii.gz'),
        'init_slice_mask' : filename('init_slice_mask', work_dir = '01_init_slices', str_template = '????.png'),
        'init_slice_naming' : filename('init_slice_naming', work_dir = '01_init_slices', str_template = '%04d.png'),
        # Initial outline mask
        'init_outline' : filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '{idx:04d}.nii.gz'),
        'init_outline_mask' : filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '????.png'),
        'init_outline_naming' : filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '%04d.png'),
        # Iteration
        'iteration'  : filename('iteraltion', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_out_naming' : filename('iteration_out_naming', work_dir = '05_iterations', str_template = '{iter:04d}/11_transformations/{idx:04d}'),
        'iteration_transform'  : filename('iteration_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{idx:04d}Warp.nii.gz'),
        'iteration_resliced'   : filename('iteration_resliced' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/'),
        'iteration_resliced_slice' : filename('iteration_resliced_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/{idx:04d}.nii.gz'),
        'iteration_resliced_outline'   : filename('iteration_resliced_outline' , work_dir = '05_iterations', str_template  = '{iter:04d}/22_resliced_outline/'),
        'iteration_resliced_outline_slice' : filename('iteration_resliced_outline_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/22_resliced_outline/{idx:04d}.nii.gz'),
        'inter_res'  : filename('inter_res',  work_dir = '08_intermediate_results', str_template = ''),
        'tmp_gray_vol' : filename('tmp_gray_vol', work_dir = '08_intermediate_results', str_template = '__temp__vol__gray.vtk'),
        'inter_res_gray_vol'   : filename('inter_res_gray_vol',   work_dir = '08_intermediate_results', str_template = 'intermediate_{output_naming}_{iter:04d}.nii.gz'),
        'iteration_stack_mask' : filename('iteration_stack_mask', work_dir = '05_iterations', str_template = '{iter:04d}/21_resliced/????.nii.gz')
        }
    
    _usage = ""
    
    def prepare_slices(self):
        preprocess_grayscale_slices = preprocess_slice_volume(\
                input_image = self.options.inputGrayscaleVolume,
                output_naming = self.f['init_slice_naming'](), \
                start_slice = self.options.startSlice, \
                end_slice = self.options.endSlice +1, \
                shift_indexes = self.options.shiftIndexes, \
                slice_mask = self.f['init_slice_mask'](),
                output_dir = self.f['init_slice'].base_dir)
        
        preprocess_grayscale_slices()
         
        if self.options.outlineVolume:
            prepare_outline_volume = preprocess_slice_volume(\
                    input_image = self.options.outlineVolume,
                    output_naming = self.f['init_outline_naming'](),\
                    start_slice = self.options.startSlice, \
                    end_slice = self.options.endSlice, \
                    shift_indexes = self.options.shiftIndexes,\
                    slice_mask = self.f['init_outline_mask'],\
                    output_dir = self['init_outline_naming'].base_dir)
            
            prepare_outline_volume()
    
    def transform(self):
        pass
    
    def launch(self):
        """
        """
        if self.options.inputGrayscaleVolume:
            self.prepare_slices()
        
        for iteration in range(self.options.startFromIteration,\
                               self.options.iterations):
            self.current_iteration = iteration
            
            step_options = copy.deepcopy(self.options)
            step_args = copy.deepcopy(self.args)
            
            step_options.workdir = os.path.join(self.f['iteration'](iter=iteration))
            single_step = deformable_reconstruction_iteration(step_options, step_args, pool = self.pool)
            
            if iteration == 0:
                single_step.f['src_slice'].override_dir = self.f['init_slice'].base_dir
            else:
                single_step.f['src_slice'].override_dir = self.f['iteration_resliced'](iter=iteration-1)
            
            # Do registration 
            if not self.options.skipTransformations:
                single_step()
            
            # Generate volume holding the intermediate results
            # and prepare images for the next iteration
            self._reslice() 
            self._stack_intermediate()
    
    def _get_edges(self):
        """
        Convenience function for returning frequently used numbers
        """
        return (self.options.startSlice,
                self.options.endSlice,
                self.options.neighbourhood,
                self.current_iteration)
    
    def _reslice(self):
        start, end, eps, iteration = self._get_edges()
        
        commands = []
        for i in range(start, end +1):
            deformable_list = map(lambda j: self.f['iteration_transform'](idx=i,iter=j), range(iteration+1))
            moving_image = self.f['init_slice'](idx=i)
            
            command = ants_reslice(
                    dimension = 2,
                    moving_image = moving_image,
                    output_image = self.f['iteration_resliced_slice'](idx=i,iter=iteration),
                    reference_image = moving_image,
                    deformable_list = deformable_list,
                    affine_list = [])
            commands.append(copy.deepcopy(command))
        
        self.execute(commands)
    
    def _stack_intermediate(self):
        iteration = self.current_iteration
        
        stack_grayscale =  stack_slices_gray_wrapper(
                temp_volume_fn = self.f['tmp_gray_vol'](),
                output_volume_fn = self.f['inter_res_gray_vol'](\
                                        iter=iteration,
                                        output_naming=self.options.outputNaming),
                stack_mask = self.f['iteration_stack_mask'](iter=iteration),
                permutation_order = self.options.outputVolumePermutationOrder,
                orientation_code = self.options.outputVolumeOrientationCode,
                output_type = self.options.outputVolumeScalarType,
                spacing = self.options.outputVolumeSpacing,
                origin = self.options.outputVolumeOrigin,
                interpolation = self.options.setInterpolation,
                resample = self.options.outputVolumeResample)
        
        self.execute(stack_grayscale)
    
    def prepare_calculations(self):
        pass
    
    def process_results(self):
        pass
    
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
                help='Shift indexes')
        parser.add_option('--neighbourhood', default=1, type='int',
                dest='neighbourhood',  help='Epsilon')
        parser.add_option('--iterations', default=10,
                type='int', dest='iterations',
                help='Number of iterations')
        parser.add_option('--startFromIteration', default=0,
                type='int', dest='startFromIteration',
                help='startFromIteration')
        parser.add_option('--inputGrayscaleVolume','-i', default=None,
                type='str', dest='inputGrayscaleVolume',
                help='Input grayscale volume to be reconstructed')
        parser.add_option('--outlineVolume','-o', default=None,
                type='str', dest='outlineVolume',
                help='Labels for driving the registration')
        parser.add_option('--weightsFile', default=None, type='str',
                dest='weightsFile', help="Include weights during the reconstruction")
        parser.add_option('--registerSubset', default=None, type='str',
                dest='registerSubset',  help='registerSubset')
#       parser.add_option('--labelledVolume','-l', default=None,
#               type='str', dest='labelledVolume',
#               help='Labels for driving the registration')
#       parser.add_option('--maskedVolume','-m', default=None,
#               type='str', dest='maskedVolume',
#               help='Slice mask for driving the registration')
        parser.add_option('--outputNaming', default="_", type='str',
                dest='outputNaming', help="Ouput naming scheme for all the results")
        parser.add_option('--skipTransformations', default=False,
                dest='skipTransformations', action='store_const', const=True,
                help='Skip transformations.')
        
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
    d.pool.close()
    d.pool.join()
