#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys
import numpy as np
import copy
from optparse import OptionParser, OptionGroup

from pos_wrapper_skel import generic_workflow
from minimum_deformation_template_iterations import deformable_reconstruction_iteration
import pos_wrappers
import pos_parameters


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

class sddm_convergence(pos_wrappers.generic_wrapper):
    _template= """c{dimension}d {first_image} {second_image} -msq | cut -f 3 -d" " >> {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'first_image': pos_parameters.filename_parameter('first_image', None),
        'second_image': pos_parameters.filename_parameter('second_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None)
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
        'init_slice' : pos_parameters.filename('init_slice', work_dir = '01_init_slices', str_template = '{idx:04d}.nii.gz'),
        # Iteration
        'iteration'  : pos_parameters.filename('iteraltion', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_resliced_avg'   : pos_parameters.filename('iteration_resliced_slice_avg' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/average.nii.gz'),
        # Building the template
        'template_transf_f'   : pos_parameters.filename('template_transf_f',   work_dir = '12_transf_f', str_template = '{idx:04d}.nii.gz'),
        'template_transf_f_msq'   : pos_parameters.filename('template_transf_f_msq',   work_dir = '12_transf_f', str_template = 'msq{idx:04d}.nii.gz'),
        'sddm'   : pos_parameters.filename('sddm',   work_dir = '12_transf_f', str_template = 'sddm{iter:04d}.nii.gz'),
        'sddm_convergence'   : pos_parameters.filename('sddm_convergence',   work_dir = '12_transf_f', str_template = 'sddm_convergence.txt'),
        }

    _usage = ""

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

        # Handling situation when no volume is provided
        if not self.options.inputVolume:
            print >> sys.stderr, "No input volumes provided. Exiting."
            sys.exit(1)

        #TODO: Input volume required!
        #TODO: image span required!

        self.f['raw_slices'].override_dir = self.options.inputVolume

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

        self.slice_range = range(self.options.firstImageIndex,
                                 self.options.lastImageIndex +1)
        self.iterations = range(self.options.startFromIteration,\
                                self.options.iterations)

        self._prepare_input_images()

        # If 'startFromIteration' switch is enabled,
        # the reconstruction starts from a given iteration
        # instead of starting from the beginning - iteration 0
        for iteration in self.iterations:

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
            single_step.parent = self

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

        self.calculate_convergence()

    def calculate_convergence(self):

        pairs = zip(self.iterations[:-1], self.iterations[1:])

        for (i, j) in pairs:
            command = sddm_convergence( \
                dimension = self.options.antsDimension,
                first_image = self.f['sddm'](iter=i),
                second_image = self.f['sddm'](iter=j),
                output_image = self.f['sddm_convergence']())
            self.execute(copy.deepcopy(command))

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('--firstImageIndex', default=0,
                type='int', dest='firstImageIndex',
                help='Index of the first slice of the stack')
        parser.add_option('--lastImageIndex', default=None,
                type='int', dest='lastImageIndex',
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
        parser.add_option('--skipTransformations', default=False,
                dest='skipTransformations', action='store_const', const=True,
                help='Skip transformations.')

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

