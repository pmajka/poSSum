#!/usr/bin/python
import os,sys
import numpy as np

from optparse import OptionParser, OptionGroup
import copy

from pos_deformable_wrappers import preprocess_slice_volume
from pos_wrapper_skel import generic_workflow
from minimum_deformation_template_iterations import deformable_reconstruction_iteration
import pos_wrappers
import pos_parameters


class test_msq_2(pos_wrappers.generic_wrapper):
    """
    """
    _template = """c{dimension}d -mcs {input_image} -popas x -popas y -push x -dup -times -popas xx -push y  -dup -times -popas yy -push xx -push yy -add -o {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class test_msq_3(pos_wrappers.generic_wrapper):
    """
    """
    _template = """c{dimension}d -mcs {input_image} -popas x -popas y -popas z -push x -dup -times -popas xx -push y  -dup -times -popas yy -push z  -dup -times  -popas zz -push xx -push yy -push zz -add -o {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 3),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class calculate_sddm(pos_wrappers.average_images):
    """
    """
    _template = """c{dimension}d  {input_images} -mean -sqrt -o {output_image}"""



class ants_multiply_images(pos_wrappers.generic_wrapper):
    """
    """
    _template = """MultiplyImages {dimension} {input_image} {multiplier} {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'multiplier': pos_parameters.value_parameter('multiplier', 1.0),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }



class bias_correction(pos_wrappers.generic_wrapper):
    _template= """N4BiasFieldCorrection -d {dimension} -i {input_image} -o {output_image} -b [200] -s 3 -c [50x50x30x20,1e-6]"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class minimum_deformation_template_wrokflow(generic_workflow):
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
    slices.

    """
    _f = { \
        'raw_slices' : pos_parameters.filename('raw_slices', work_dir = '00_raw_slices', str_template = '{idx:04d}.nii.gz'),
         # Initial grayscale slices
        'init_slice' : pos_parameters.filename('init_slice', work_dir = '01_init_slices', str_template = '{idx:04d}.nii.gz'),
        'init_slice_mask' : pos_parameters.filename('init_slice_mask', work_dir = '01_init_slices', str_template = '????.png'),
        'init_slice_naming' : pos_parameters.filename('init_slice_naming', work_dir = '01_init_slices', str_template = '%04d.png'),
        # Initial outline mask
        'init_outline' : pos_parameters.filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '{idx:04d}.nii.gz'),
        'init_outline_mask' : pos_parameters.filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '????.png'),
        'init_outline_naming' : pos_parameters.filename('init_outline_naming', work_dir = '02_outline_slices', str_template = '%04d.png'),
        # Iteration
        'iteration'  : pos_parameters.filename('iteraltion', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_out_naming' : pos_parameters.filename('iteration_out_naming', work_dir = '05_iterations', str_template = '{iter:04d}/11_transformations/{idx:04d}'),
        'iteration_affine_transform'  : pos_parameters.filename('iteration_affine_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{idx:04d}Affine.txt'),
        'iteration_affine_transform_avg'  : pos_parameters.filename('iteration_affine_transform_avg', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/averageAffine.txt'),
        'iteration_transform'  : pos_parameters.filename('iteration_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{idx:04d}Warp.nii.gz'),
        'iteration_transform_avg'  : pos_parameters.filename('iteration_transform_avg', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/averageWarp.nii.gz'),
        'iteration_transform_inverse'  : pos_parameters.filename('iteration_transform_inverse', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{idx:04d}InverseWarp.nii.gz'),
        'iteration_transform_inverse_avg'  : pos_parameters.filename('iteration_transform_inverse_avg', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/averageInverseWarp.nii.gz'),
        'iteration_resliced'   : pos_parameters.filename('iteration_resliced' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/'),
        'iteration_resliced_slice' : pos_parameters.filename('iteration_resliced_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/{idx:04d}.nii.gz'),
        'iteration_resliced_avg'   : pos_parameters.filename('iteration_resliced_slice_avg' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/average.nii.gz'),
        'iteration_resliced_outline'   : pos_parameters.filename('iteration_resliced_outline' , work_dir = '05_iterations', str_template  = '{iter:04d}/22_resliced_outline/'),
        'iteration_resliced_outline_slice' : pos_parameters.filename('iteration_resliced_outline_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/22_resliced_outline/{idx:04d}.nii.gz'),
        # After completing iterations
        'final_deformations'   : pos_parameters.filename('final_deformations',   work_dir = '09_final_deformation', str_template = '{idx:04d}.nii.gz'),
        'final_deformations_inversed'   : pos_parameters.filename('final_deformations_inversed',   work_dir = '10_final_deformation_inversed', str_template = '{idx:04d}.nii.gz'),
        'final_deformations_inv_avg'   : pos_parameters.filename('final_deformations_inv_avg',   work_dir = '10_final_deformation_inversed', str_template = 'average.nii.gz'),
        # Building the template
        'template_indiv'   : pos_parameters.filename('template_indiv',   work_dir = '11_template', str_template = '{idx:04d}.nii.gz'),
        'template_average'   : pos_parameters.filename('template_average',   work_dir = '11_template', str_template = 'average.nii.gz'),
        'template_transf_f'   : pos_parameters.filename('template_transf_f',   work_dir = '12_transf_f', str_template = '{idx:04d}.nii.gz'),
        'template_transf_f_msq'   : pos_parameters.filename('template_transf_f_msq',   work_dir = '12_transf_f', str_template = 'msq{idx:04d}.nii.gz'),
        'sddm'   : pos_parameters.filename('sddm',   work_dir = '12_transf_f', str_template = 'sddm.nii.gz'),
        }

    _usage = ""

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

        # Handling situation when no volume is provided
        if not any([self.options.inputVolume, \
                   self.options.outlineVolume]):
            print >> sys.stderr, "No input volumes provided. Exiting."
            sys.exit(1)

        if self.options.inputVolume:
            self.f['raw_slices'].override_dir = self.options.inputVolume

        if self.options.outlineVolume:
            self.f['init_outline'].override_dir = self.options.outlineVolume

        # Just to be sure :)
        self.current_iteration = 0

    def _prepare_input_images(self):
        """
        """
        commands = []

        for i in self.slice_range:
            command = bias_correction( \
                            dimension = self.options.antsDimension,
                            input_image  = self.f['raw_slices'](idx=i),
                            output_image = self.f['init_slice'](idx=i))
            commands.append(copy.deepcopy(command))
        self.execute(commands)

    def launch(self):
        """
        Launch the process.
        """

        start, end, iteration = self._get_edges()
        self.slice_range = range(start, end +1)

        self._prepare_input_images()

        # If 'startFromIteration' switch is enabled,
        # the reconstruction starts from a given iteration
        # instead of starting from the beginning - iteration 0
        for iteration in range(self.options.startFromIteration,\
                               self.options.iterations):

            print >> sys.stderr, "-------------------------------------------------"
            print >> sys.stderr, "Staring iteration: %d of %d" \
                                        % (iteration, self.options.iterations)
            print >> sys.stderr, "-------------------------------------------------"

            self.current_iteration = iteration

            # Make hard copy of the setting dictionaries. Hard copy is made as
            # it is passed to the 'deformable_reconstruction_iteration' class
            # and is is customized within this class. Because of that reason a
            # hard copy has to be made.
            step_options = copy.deepcopy(self.options)
            step_args = copy.deepcopy(self.args)

            # TODO: Provide some comment here
            step_options.workdir = os.path.join(self.f['iteration'](iter=iteration))
            single_step = deformable_reconstruction_iteration(step_options, step_args)
            single_step.parent_process = self

            #TODO: Provide some comment here
            single_step.f['src_slice'].override_dir = self.f['init_slice'].base_dir
            if iteration == 0:
                pass
            else:
                single_step.f['processed'].override_path = self.f['iteration_resliced_avg'](iter=iteration-1)

            # Do registration if proper switches are provided
            # (there is a possibility to run the reconstruction process without
            # actually calculationg the transfomations.
            if not self.options.skipTransformations:
                single_step()

            # Generate volume holding the intermediate results
            # and prepare images for the next iteration
            self._reslice()

    def _get_edges(self):
        """
        Convenience function for returning frequently used numbers
        """
        return (self.options.startSlice,
                self.options.endSlice,
                self.current_iteration)

    def _reslice(self):
        """
        Launch reslicing for each type of the input volume. If the volume of the
        given type is provided, it will be reslided, otherwise it is not
        resliced. Simple.
        """
        self._reslice_images_forward()
        self._update_template_shape()
        self._average_forward_warps()
        self._update_average_fwd_wrap()
        self._update_average_inverse_wrap()
        self._update_warp_variance()

    def _update_warp_variance(self):
        start, end, iteration = self._get_edges()
        commands = []
        for i in self.slice_range:
            deformable_list = [
                self.f['iteration_transform_inverse_avg'](iter=iteration),
                self.f['iteration_transform'](iter=iteration,idx=i)]

            command = pos_wrappers.ants_compose_multi_transform(
                    dimension = self.options.antsDimension,
                    output_image = self.f['template_transf_f'](idx=i),
                    reference_image = self.f['init_slice'](idx=i),
                    deformable_list = deformable_list,
                    affine_list = [])
            commands.append(copy.deepcopy(command))
        self.execute(commands)

        commands = []
        meth ={2:test_msq_2, 3: test_msq_3}
        for i in self.slice_range:
            command = meth[self.options.antsDimension](
                    dimension = self.options.antsDimension,
                    input_image = self.f['template_transf_f'](idx=i),
                    output_image = self.f['template_transf_f_msq'](idx=i))
            commands.append(copy.deepcopy(command))
        self.execute(commands)

        commands = []
        files_to_average = \
                map(lambda j: self.f['template_transf_f_msq'](idx=j), self.slice_range)
        command = calculate_sddm( \
                        dimension = self.options.antsDimension,
                        output_image = self.f['sddm'](),
                        input_images = files_to_average)
        commands.append(copy.deepcopy(command))
        self.execute(commands)

    def _update_average_inverse_wrap(self):
        start, end, iteration = self._get_edges()
        #-----------------------------------------------------------------
        # INVERSE!!!!!!!!!!!!!
        # /opt/ANTs-1.9.x-Linux/bin/AverageImages 2 testtemplatewarp.nii.gz 0
        # test0000Warp.nii.gz test0001Warp.nii.gz test0002Warp.nii.gz
        # test0003Warp.nii.gz test0004Warp.nii.gz
        #
        commands = []
        files_to_average = \
                map(lambda j: self.f['iteration_transform_inverse'](iter=iteration,idx=j), self.slice_range)
        command = pos_wrappers.ants_average_images( \
                        dimension = self.options.antsDimension,
                        normalize = int(False),
                        output_image = self.f['iteration_transform_inverse_avg'](iter=iteration),
                        input_images = files_to_average)
        commands.append(copy.deepcopy(command))
        self.execute(commands)

        #  /opt/ANTs-1.9.x-Linux/bin/WarpImageMultiTransform 2
        #  testtemplatewarp.nii.gz
        #  testtemplatewarp.nii.gz
        #  -i
        #  testtemplateAffine.txt
        #  -R
        #  testtemplate.nii.gz
        commands = []
        mul_avg_aff = self.f['iteration_transform_inverse_avg'](iter=iteration)
        inv_aff = self.f['iteration_affine_transform_avg'](iter=iteration)

        command = pos_wrappers.ants_reslice(
            dimension = self.options.antsDimension,
            moving_image = mul_avg_aff,
            output_image = mul_avg_aff,
            reference_image = mul_avg_aff,
            deformable_list = [mul_avg_aff, inv_aff] ,
            affine_list = [])
        commands.append(copy.deepcopy(command))
        self.execute(commands)

    def _update_average_fwd_wrap(self):
        start, end, iteration = self._get_edges()
        # /opt/ANTs-1.9.x-Linux/bin/MultiplyImages 2 testtemplatewarp.nii.gz\
        #                                      -0.25 testtemplatewarp.nii.gz
        commands = []
        command = ants_multiply_images( \
                        dimension = self.options.antsDimension,
                        multiplier = -0.25,
                        output_image = self.f['iteration_transform_avg'](iter=iteration),
                        input_image  = self.f['iteration_transform_avg'](iter=iteration))
        commands.append(copy.deepcopy(command))
        self.execute(commands)

        #  /opt/ANTs-1.9.x-Linux/bin/AverageAffineTransform 2
        #  testtemplateAffine.txt test0000Affine.txt test0001Affine.txt
        #  test0002Affine.txt test0003Affine.txt test0004Affine.txt
        commands = []
        files_to_average = \
                map(lambda j: self.f['iteration_affine_transform'](iter=iteration,idx=j), self.slice_range)
        command = pos_wrappers.ants_average_affine_transform( \
                        dimension = self.options.antsDimension,
                        affine_list = files_to_average,
                        output_affine_transform = self.f['iteration_affine_transform_avg'](iter=iteration))
        commands.append(copy.deepcopy(command))
        self.execute(commands)

        #  /opt/ANTs-1.9.x-Linux/bin/WarpImageMultiTransform 2
        #  testtemplatewarp.nii.gz
        #  testtemplatewarp.nii.gz
        #  -i
        #  testtemplateAffine.txt
        #  -R
        #  testtemplate.nii.gz
        #  testtemplatewarp.nii.gz
        #  testtemplatewarp.nii.gz
        #  testtemplatewarp.nii.gz
        #  testtemplatewarp.nii.gz
        commands = []
        inv_aff = ["-i " + self.f['iteration_affine_transform_avg'](iter=iteration)]
        mul_avg_aff = self.f['iteration_transform_avg'](iter=iteration)

        command = pos_wrappers.ants_reslice(
            dimension = self.options.antsDimension,
            moving_image = mul_avg_aff,
            output_image = mul_avg_aff,
            reference_image = mul_avg_aff,
            deformable_list = inv_aff + 4*[mul_avg_aff],
            affine_list = [])
        commands.append(copy.deepcopy(command))
        self.execute(commands)

    def _average_forward_warps(self):
        start, end, iteration = self._get_edges()
        # /opt/ANTs-1.9.x-Linux/bin/AverageImages 2 testtemplatewarp.nii.gz 0
        # test0000Warp.nii.gz test0001Warp.nii.gz test0002Warp.nii.gz
        # test0003Warp.nii.gz test0004Warp.nii.gz
        #
        start, end, iteration = self._get_edges()
        commands = []
        files_to_average = \
                map(lambda j: self.f['iteration_transform'](iter=iteration,idx=j), self.slice_range)
        command = pos_wrappers.ants_average_images( \
                        dimension = self.options.antsDimension,
                        normalize = int(False),
                        output_image = self.f['iteration_transform_avg'](iter=iteration),
                        input_images = files_to_average)
        commands.append(copy.deepcopy(command))
        self.execute(commands)

    def _update_template_shape(self):
        start, end, iteration = self._get_edges()
        # /opt/ANTs-1.9.x-Linux/bin/AverageImages 2 testtemplate.nii.gz 1
        # test0000deformed.nii.gz test0001deformed.nii.gz
        # test0002deformed.nii.gz test0003deformed.nii.gz
        # test0004deformed.nii.gz
        commands = []
        files_to_average = \
                map(lambda j: self.f['iteration_resliced_slice'](iter=iteration,idx=j), self.slice_range)
        command = pos_wrappers.ants_average_images( \
                        dimension = self.options.antsDimension,
                        normalize = int(True),
                        output_image = self.f['iteration_resliced_avg'](iter=iteration),
                        input_images = files_to_average)
        commands.append(copy.deepcopy(command))
        self.execute(commands)

    def _reslice_images_forward(self):
        start, end, iteration = self._get_edges()

        #  /opt/ANTs-1.9.x-Linux/bin/WarpImageMultiTransform 2
        #  /home/pmajka/test0004.nii.gz /home/pmajka/test0004deformed.nii.gz
        #  /home/pmajka/test0004Warp.nii.gz /home/pmajka/test0004Affine.txt -R
        #  testtemplate.nii.gz
        commands = []
        for i in self.slice_range:
            deformable_list  = [self.f['iteration_transform'](idx=i,iter=iteration)]
            deformable_list += [self.f['iteration_affine_transform'](idx=i,iter=iteration)]
            moving_image = self.f['init_slice'](idx=i)
            command = pos_wrappers.ants_reslice(
                    dimension = self.options.antsDimension,
                    moving_image = moving_image,
                    output_image = self.f['iteration_resliced_slice'](idx=i,iter=iteration),
                    reference_image = moving_image,
                    deformable_list = deformable_list,
                    affine_list = [])
            commands.append(copy.deepcopy(command))

        self.execute(commands)

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('--startSlice', default=0,
                type='int', dest='startSlice',
                help='Index of the first slice of the stack')
        parser.add_option('--endSlice', default=None,
                type='int', dest='endSlice',
                help='Index of the last slice of the stack')
        parser.add_option('--iterations', default=10,
                type='int', dest='iterations',
                help='Number of iterations')
        parser.add_option('--startFromIteration', default=0,
                type='int', dest='startFromIteration',
                help='Iteration number from which the calculations will start.')
        parser.add_option('--inputVolume','-i', default=None,
                type='str', dest='inputVolume',
                help='Input files dir.')
        parser.add_option('--outlineVolume','-o', default=None,
                type='str', dest='outlineVolume',
                help='Outline files dir.')
        parser.add_option('--skipTransformations', default=False,
                dest='skipTransformations', action='store_const', const=True,
                help='Skip transformations.')
        parser.add_option('--stackFinalDeformation', default=False, const=True,
                dest='stackFinalDeformation', action='store_const',
                help='Stack filnal deformation fileld.')

        regSettings = \
                OptionGroup(parser, 'Registration setttings.')

        regSettings.add_option('--antsDimension', default=2,
                type='int', dest='antsDimension',
                help='Dimensionality of the image')
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
        regSettings.add_option('--antsAffineIterations', default="10000x10000",
                type='str', dest='antsAffineIterations',
                help='Number of afffine registration iterations.')

        parser.add_option_group(regSettings)

        return parser

if __name__ == '__main__':
    options, args = minimum_deformation_template_wrokflow.parseArgs()
    d = minimum_deformation_template_wrokflow(options, args)
    d.launch()

