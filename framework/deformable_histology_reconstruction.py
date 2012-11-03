#!/usr/bin/python

import os,sys
import numpy as np

from optparse import OptionParser, OptionGroup
import copy

from pos_parameters import ants_reslice, stack_slices_gray_wrapper, \
                           ants_compose_multi_transform

from pos_deformable_wrappers import preprocess_slice_volume
from pos_filenames import filename
from pos_wrapper_skel import generic_workflow
from deformable_histology_iterations import deformable_reconstruction_iteration

class deformable_reconstruction_workflow(generic_workflow):
    """
    A framework for performing deformable reconstruction of histological volumes
    based on histological slices. The framework combines:
       * Advanced Normalization Tools (ANTS, http://www.picsl.upenn.edu/ANTS/)
       * ImageMagick (http://www.imagemagick.org/script/index.php)
       * Insight Segmentation and Registration Toolkit (ITK, http://www.itk.org/)
       * ITKSnap and Convert3d (http://www.itksnap.org/)
       * Visualization Toolkit (VTK, http://www.vtk.org/)
       * and a number of homemade software
    
    in order to generate smooth and acurate volumetric reconstructions from 2d
    sliced.
    
    """
    _f = { \
         # Initial grayscale slices
        'init_slice' : filename('init_slice', work_dir = '01_init_slices', str_template = '{idx:04d}.nii.gz'),
        'init_slice_mask' : filename('init_slice_mask', work_dir = '01_init_slices', str_template = '????.png'),
        'init_slice_naming' : filename('init_slice_naming', work_dir = '01_init_slices', str_template = '%04d.png'),
        # Initial outline mask
        'init_outline' : filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '{idx:04d}.nii.gz'),
        'init_outline_mask' : filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '????.png'),
        'init_outline_naming' : filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '%04d.png'),
        # Initial custom outlier mask
        'init_custom' : filename('init_custom_naming', work_dir = '04_custom_slices', str_template = '{idx:04d}.nii.gz'),
        'init_custom_mask' : filename('init_custom_mask', work_dir = '04_custom_slices', str_template = '????.png'),
        'init_custom_naming' : filename('init_custom_naming', work_dir = '04_custom_slices', str_template = '%04d.png'),
        # Iteration
        'iteration'  : filename('iteraltion', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_out_naming' : filename('iteration_out_naming', work_dir = '05_iterations', str_template = '{iter:04d}/11_transformations/{idx:04d}'),
        'iteration_transform'  : filename('iteration_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{idx:04d}Warp.nii.gz'),
        'iteration_resliced'   : filename('iteration_resliced' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/'),
        'iteration_resliced_slice' : filename('iteration_resliced_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/{idx:04d}.nii.gz'),
        'iteration_resliced_outline'   : filename('iteration_resliced_outline' , work_dir = '05_iterations', str_template  = '{iter:04d}/22_resliced_outline/'),
        'iteration_resliced_outline_slice' : filename('iteration_resliced_outline_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/22_resliced_outline/{idx:04d}.nii.gz'),
        'iteration_resliced_custom'   : filename('iteration_resliced_custom' , work_dir = '05_iterations', str_template  = '{iter:04d}/24_resliced_custom/'),
        'iteration_resliced_custom_slice' : filename('iteration_resliced_custom_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/24_resliced_custom/{idx:04d}.nii.gz'),
        'inter_res'  : filename('inter_res',  work_dir = '08_intermediate_results', str_template = ''),
        'tmp_gray_vol' : filename('tmp_gray_vol', work_dir = '08_intermediate_results', str_template = '__temp__vol__gray.vtk'),
        'inter_res_gray_vol'   : filename('inter_res_gray_vol',   work_dir = '08_intermediate_results', str_template = 'intermediate_{output_naming}_{iter:04d}.nii.gz'),
        'inter_res_outline_vol'   : filename('inter_res_outline_vol',   work_dir = '08_intermediate_results', str_template = 'intermediate_{output_naming}_outline_{iter:04d}.nii.gz'),
        'inter_res_custom_vol'   : filename('inter_res_custom_vol',   work_dir = '08_intermediate_results', str_template = 'intermediate_{output_naming}_cmask_{iter:04d}.nii.gz'),
        'final_deformations'   : filename('final_deformations',   work_dir = '09_final_deformation', str_template = '{idx:04d}.nii.gz'),
        'iteration_stack_mask' : filename('iteration_stack_mask', work_dir = '05_iterations', str_template = '{iter:04d}/21_resliced/????.nii.gz'),
        'iteration_stack_outline' : filename('iteration_stack_outline', work_dir = '05_iterations', str_template = '{iter:04d}/22_resliced_outline/????.nii.gz'),
        'iteration_stack_cmask' : filename('iteration_stack_cmask', work_dir = '05_iterations', str_template = '{iter:04d}/24_resliced_custom/????.nii.gz')
        }
    
    _usage = ""
    
    def __init__(self, options, args, pool = None):
        super(self.__class__, self).__init__(options, args, pool)
        
        # Handling situation when no volume is provided
        if not any([self.options.inputVolume, \
                   self.options.outlineVolume, \
                   self.options.maskedVolume]):
            print >> sys.stderr, "No input volumes provided. Exiting."
            sys.exit(1)
        
        # Process each type of the input volume. Currently there are three types
        # of input volumes supported: The input grayscale volume (the actual
        # imaege to be registared), the outline volume (volume pointing wihch
        # part of the image belongs to the slice and which part not).
        # The third type of the volume is a volume for outlier removal (so
        # called masked volume).
        if self.options.inputVolume:
            self.options.inputVolumeWeight = float(self.options.inputVolume[0])
            self.options.inputVolume = self.options.inputVolume[1]
        
        if self.options.outlineVolume:
            self.options.outlineVolumeWeight = float(self.options.outlineVolume[0])
            self.options.outlineVolume = self.options.outlineVolume[1]
        
        if self.options.maskedVolume:
            self.options.maskedVolumeWeight = float(self.options.maskedVolume[0])
            self.options.maskedVolume = self.options.maskedVolume[1]
    
    def _get_prepare_volume_command_template(self):
        """
        :return: template for processing the input volumes.
        
        The templte has to be customized to process a particular type of volume. 
        """
        preprocess_slices = preprocess_slice_volume(\
                input_image = self.options.inputVolume,
                output_naming = self.f['init_slice_naming'](), \
                start_slice = self.options.startSlice, \
                end_slice = self.options.endSlice + 1, \
                shift_indexes = self.options.shiftIndexes, \
                slice_mask = self.f['init_slice_mask'](),
                output_dir = self.f['init_slice'].base_dir)
        
        return preprocess_slices
    
    def prepare_slices(self):
        """
        Split provided input volumes into slices. The proceure requires the
        prvided volumes to be in grayscale mode (it's gonna work also with rgb
        volumes but the further registration process will collapse). 
        
        Volumes are sectioned separately. If the swich for given volume is
        provided, the sections `startSlice` to `endSlice` are extracted. The
        process is repeated separately for each volume (grayscale, outline,
        custom mask volume, segmentation volume, etc...)
        """
        
        # Handle inputVolume (grayscale volume, aka THE registereg image volume)
        if self.options.inputVolume:
            preprocess_grayscale_slices = \
                    self._get_prepare_volume_command_template()
            
            preprocess_grayscale_slices.updateParameters({
                'input_image' : self.options.inputVolume,
                'output_naming' : self.f['init_slice_naming'](), \
                'slice_mask' : self.f['init_slice_mask'](),
                'output_dir' : self.f['init_slice'].base_dir})
            preprocess_grayscale_slices()
        
        # Handle the outline volume. This volume is a binary volume (it can
        # contain only 0 and 1 values).
        if self.options.outlineVolume:
            prepare_outline_volume = \
                    self._get_prepare_volume_command_template()
            
            prepare_outline_volume.updateParameters({ 
                'input_image' : self.options.outlineVolume, 
                'output_naming' : self.f['init_outline_naming'](),
                'slice_mask' : self.f['init_outline_mask'],
                'output_dir' : self.f['init_outline_naming'].base_dir})
            prepare_outline_volume()
        
        # Handling custom mask volume. This volume is a mask volume which means
        # that it is a binary volume and contains only 0 and 1 values.
        if self.options.maskedVolume:
            prepare_masked_volume = \
                    self._get_prepare_volume_command_template()
            
            prepare_masked_volume.updateParameters({ 
                'input_image' : self.options.maskedVolume, 
                'output_naming' : self.f['init_custom_naming'](),
                'slice_mask' : self.f['init_custom_mask'],
                'output_dir' : self.f['init_custom_naming'].base_dir,
                'leave_overflows': True})
                   
            prepare_masked_volume()
    
    def launch(self):
        """
        Launch the deformable registration process.
        """
        
        # Preprocessing the input sliced can be supressed by issuing a command
        # line parameter
        if not self.options.skipSlicePreprocess:
            self.prepare_slices()
        
        # If 'startFromIteration' switch is enabled,
        # the reconstruction starts from a given iteration
        # instead of starting from the beginning - iteration 0
        for iteration in range(self.options.startFromIteration,\
                               self.options.iterations):
            
            print >> sys.stderr, "-------------------------------------------------"
            print >> sys.stderr, "Staring iteration: %d of %d" \
                                        % (iteration +1, self.options.iterations)
            print >> sys.stderr, "-------------------------------------------------"
            
            self.current_iteration = iteration
            
            # Make hard copy of the setting dictionaries. Hard copy is made as
            # it is passed to the 'deformable_reconstruction_iteration' class
            # and is is customized within this class. Because of that reason a
            # hard copy has to be made.
            step_options = copy.deepcopy(self.options)
            step_args = copy.deepcopy(self.args)
            
            step_options.workdir = os.path.join(self.f['iteration'](iter=iteration))
            single_step = deformable_reconstruction_iteration(step_options, step_args, pool = self.pool)
            single_step.parent_process = self
            
            # Settings for the first iteration has to be tweaked up a little as
            # they use slightly different image sources. Iteration 'zero' uses
            # the source images (images that were not processed at all) while
            # images for all the other iterations are processed by the previous
            # iterations.
            if iteration == 0:
                single_step.f['src_slice'].override_dir = self.f['init_slice'].base_dir
                single_step.f['outline'].override_dir = self.f['init_outline'].base_dir
                single_step.f['cmask'].override_dir = self.f['init_custom'].base_dir
            else:
                single_step.f['src_slice'].override_dir = self.f['iteration_resliced'](iter=iteration-1)
                single_step.f['outline'].override_dir = self.f['iteration_resliced_outline'](iter=iteration-1)
                single_step.f['cmask'].override_dir = self.f['iteration_resliced_custom'](iter=iteration-1)
            
            # Do registration if proper switches are provided
            # (there is a possibility to run the reconstruction process without 
            # actually calculationg the transfomations.
            if not self.options.skipTransformations:
                single_step()
            
            # Generate volume holding the intermediate results
            # and prepare images for the next iteration
            self._reslice() 
            self._stack_intermediate()
        
        # At the end of the processing the calculated deformation fields can be
        # composed togeather to form the final deformation field.
        if self.options.stackFinalDeformation:
            self._generate_final_transforms()
    
    def _get_edges(self):
        """
        Convenience function for returning frequently used numbers
        """
        return (self.options.startSlice,
                self.options.endSlice,
                self.options.neighbourhood,
                self.current_iteration)
    
    def _reslice(self):
        """
        Launch reslicing for each type of the input volume. If the volume of the
        given type is provided, it will be reslided, otherwise it is not
        resliced. Simple.
        """
        if self.options.inputVolume:
            self._reslice_input_volume()
        
        if self.options.outlineVolume:
            self._reslice_outline()
        
        if self.options.maskedVolume:
            self._reslice_custom_masks()
    
    def _get_reslice_command(self, slice_number, slice_type, output_slice_type, method = ants_reslice):
        """
        Helper for generating reslicing command for different slices, reslicing
        with different types, etc.
        
        :return: Command for reslicing given slice according to provided
                 parameters
        """
        
        start, end, eps, iteration = self._get_edges()
        
        i = slice_number # Just an alias
        
        # Define a list of deformation fields file
        deformable_list = map(lambda j: self.f['iteration_transform'](idx=i,iter=j), range(iteration+1))
        moving_image = self.f[slice_type](idx=i)
        
        # Use 'ants_reslice' when a regular reslicing is done. A regular
        # reslicing occur after each iteration.
        if method == ants_reslice:
            command = method(
                    dimension = 2,
                    moving_image = moving_image,
                    output_image = self.f[output_slice_type](idx=i,iter=iteration),
                    reference_image = moving_image,
                    deformable_list = deformable_list,
                    affine_list = [])
            return command
        
        # Use 'ants_compose_multi_transform' for composing individual
        # deformation fields into a single deformation fiels.
        if method == ants_compose_multi_transform:
            command = method(
                    dimension = 2,
                    output_image = self.f[output_slice_type](idx=i,iter=iteration),
                    reference_image = moving_image,
                    deformable_list = deformable_list,
                    affine_list = [])
            return command
    
    def _reslice_input_volume(self):
        start, end, eps, iteration = self._get_edges()
        
        commands = []
        for i in range(start, end +1):
            command = self._get_reslice_command(i, 'init_slice', 'iteration_resliced_slice')
            command.updateParameters({'useBspline':True, 'useNN':None})
            commands.append(copy.deepcopy(command))
        
        self.execute(commands)
    
    def _reslice_outline(self):
        start, end, eps, iteration = self._get_edges()
        
        commands = []
        for i in range(start, end +1):
            command = self._get_reslice_command(i, 'init_outline', 'iteration_resliced_outline_slice')
            command.updateParameters({'useNN':None, 'useBspline':None})
            commands.append(copy.deepcopy(command))
         
        self.execute(commands)
    
    def _reslice_custom_masks(self):
        start, end, eps, iteration = self._get_edges()
        
        commands = []
        for i in range(start, end +1):
            command = self._get_reslice_command(i, 'init_custom', 'iteration_resliced_custom_slice')
            command.updateParameters({'useBspline':None, 'useNN':True})
            commands.append(copy.deepcopy(command))
        
        self.execute(commands)
    
    def _generate_final_transforms(self):
        """
        Compose the individual deformation fields calculated in each iteration
        into a single deformation field that can be analysed. In other words,
        this procedure just sums up all the individual deformation filelds.
        """
         
        # As usually, get the slice range:
        start, end, eps, iteration = self._get_edges()
        
        # For each slice, compose all the separated deformation fields:
        commands = []
        for i in range(start, end +1):
            command = self._get_reslice_command(i, 'init_slice', 'iteration_resliced_slice', 
                                                method = ants_compose_multi_transform)
            command.updateParameters({\
                    'output_image': self.f['final_deformations'](idx=i)
                    })
            commands.append(copy.deepcopy(command))
         
        self.execute(commands)
    
    def _get_stack_intermediate_command(self):
        """
        Helper function for stakcing resliced slices from intermediate stages of
        processing.
        """
        iteration = self.current_iteration
        
        stack_grayscale =  stack_slices_gray_wrapper(
                temp_volume_fn = self.f['tmp_gray_vol'](),
                stack_mask = self.f['iteration_stack_mask'](iter=iteration),
                permutation_order = self.options.outputVolumePermutationOrder,
                orientation_code = self.options.outputVolumeOrientationCode,
                output_type = self.options.outputVolumeScalarType,
                spacing = self.options.outputVolumeSpacing,
                origin = self.options.outputVolumeOrigin,
                interpolation = self.options.setInterpolation,
                resample = self.options.outputVolumeResample)
        
        return stack_grayscale
    
    def _stack_intermediate(self):
        iteration = self.current_iteration
        
        commands = []
        
        if self.options.inputVolume:
            stack_input_volume = self._get_stack_intermediate_command()
            stack_input_volume.updateParameters({
                'stack_mask' : self.f['iteration_stack_mask'](iter=iteration),
                'output_volume_fn': self.f['inter_res_gray_vol'](\
                                    iter=iteration,
                                    output_naming=self.options.outputNaming)
                                    })
            stack_input_volume()
        
        if self.options.outlineVolume:
            stack_outline_volume = self._get_stack_intermediate_command()
            stack_outline_volume.updateParameters({
                'stack_mask' : self.f['iteration_stack_outline'](iter=iteration),
                'output_volume_fn': self.f['inter_res_outline_vol'](\
                                    iter=iteration,
                                    output_naming=self.options.outputNaming)
                                    })
            stack_outline_volume()
        
        if self.options.maskedVolume:
            stack_masked_volume = self._get_stack_intermediate_command()
            stack_masked_volume.updateParameters({
                'stack_mask' : self.f['iteration_stack_cmask'](iter=iteration),
                'output_volume_fn': self.f['inter_res_custom_vol'](\
                                    iter=iteration,
                                    output_naming=self.options.outputNaming)
                                    })
            stack_masked_volume()
    
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
    d.pool.close()
    d.pool.join()
