#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys
import copy
import logging
import json
from optparse import OptionParser, OptionGroup

import pos_common
from pos_wrapper_skel import generic_workflow
from pos_mdt_iteration import minimum_deformation_template_iteration
import pos_parameters
import pos_wrappers
import pos_mdt_wrappers


class minimum_deformation_template_wrokflow(generic_workflow):
    """
    """
    _f = { \
        'raw_images' : pos_parameters.filename('raw_images', work_dir = '00_raw_images', str_template = '{idx:04d}.nii.gz'),
        'init_slice' : pos_parameters.filename('init_slice', work_dir = '01_init_slices', str_template = '{idx:04d}.nii.gz'),
        # Iteration
        'iteration'  : pos_parameters.filename('iteraltion', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_resliced_avg'   : pos_parameters.filename('iteration_resliced_slice_avg' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/average.nii.gz'),
        # Building the template
        'template_transf_f'   : pos_parameters.filename('template_transf_f',   work_dir = '12_transf_f', str_template = '{idx:04d}.nii.gz'),
        'template_jacobian_naming'   : pos_parameters.filename('template_jacobian_naming',   work_dir = '12_transf_f', str_template = '{idx:04d}'),
        'template_jacobian'   : pos_parameters.filename('template_jacobian',   work_dir = '12_transf_f', str_template = '{idx:04d}jacobian.nii.gz'),
        'template_jacobian_avg'   : pos_parameters.filename('template_jacobian_avg',   work_dir = '12_transf_f', str_template = 'jacobian_average.nii.gz'),
        'template_transf_f_msq'   : pos_parameters.filename('template_transf_f_msq',   work_dir = '12_transf_f', str_template = 'msq{idx:04d}.nii.gz'),
        'sddm'   : pos_parameters.filename('sddm',   work_dir = '12_transf_f', str_template = 'sddm{iter:04d}.nii.gz'),
        'sddm_convergence'   : pos_parameters.filename('sddm_convergence',   work_dir = '12_transf_f', str_template = 'sddm_convergence.txt'),
        }

    _usage = ""

    def _validate_options(self):
        # Handling situation when no volume is provided
        assert self.options.inputVolume, \
            self._logger.error("No input directory provided. Please provide input directory (-i) and try again.")

        # Handling the situation when no image span is provided.
        assert self.options.firstImageIndex != None and \
               self.options.lastImageIndex != None, \
            self._logger.error("No image span provided. Please provide --firstImageIndex and --lastImageIndex.")

    def _overrideDefaults(self):
        # Override default raw_images directory (which, in fact, is just a
        # stub) with the directory with actual images.
        self.f['raw_images'].override_dir = self.options.inputVolume

        # If custom registration settings file is provided, the number of
        # iterations passed via command line should be overriden by the
        # number of iterations defined by the custom registration settings
        # file.
        if self.options.settingsFile:
            self._logger.debug("Custom registration settings file provided. Overriding number of iterations.")

            self.options.custom_registration_settings = \
                    json.load(open(self.options.settingsFile))

            self.options.iterations = \
                    len(self.options.custom_registration_settings.keys())

            self._logger.debug("%d iteration will be performed.", self.options.iterations)

    def _prepare_input_images(self):
        """
        The images constituting the template are not the raw images but the
        processed :) images. Currently, the processing is only N4 bias
        correction but in the future, other steps may be involved.
        """
        commands = []

        for i in self.slice_range:
            command = pos_mdt_wrappers.bias_correction( \
                            dimension = self.options.antsDimension,
                            input_image  = self.f['raw_images'](idx=i),
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

            self._logger.info("-------------------------------------------------")
            self._logger.info("Staring iteration: %d of %d", \
                              iteration, self.options.iterations)
            self._logger.info("-------------------------------------------------")

            self.current_iteration = iteration

            # Make hard copy of the setting dictionaries. Hard copy is made as
            # it is passed to the 'minimum_deformation_template_iteration' class
            # and is is customized within this class. Because of that reason a
            # hard copy has to be made.
            self._logger.debug("Cloning the command line options and passing to the child workflow.")
            step_options = copy.deepcopy(self.options)
            step_args = copy.deepcopy(self.args)

            # Assign working directory to the individual iteration workflow.
            # The working directory is a subdir of the parent workflow.
            self._logger.debug("Initializing the individual interation step workflow.")
            step_options.workdir = os.path.join(self.f['iteration'](iter=iteration))
            single_step = minimum_deformation_template_iteration(step_options, step_args)
            single_step.parent = self

            # In the first iteration the moving images are the initial images
            # of the workflow. In all the next iterations, the images resliced
            # during the previous iteration are used.
            self._logger.debug("Setting the source of the moving images for iteration %d.", iteration)
            single_step.f['src_slice'].override_dir = self.f['init_slice'].base_dir
            if iteration != 0:
                single_step.f['processed'].override_path = self.f['iteration_resliced_avg'](iter=iteration-1)

            # Do registration if proper switches are provided
            # (there is a possibility to run the reconstruction process without
            # actually calculationg the transfomations.
            if self.options.skipTransformations:
                self._logger.debug("skipTransformations option enabled - skipping iteration %d", iteration)
            else:
                single_step()

        self._logger.info("Calculating template convergence.")
        self.calculate_convergence()
        self._create_smoothed_jacobian()
        self._print_results_path()

    def _print_results_path(self):
        """
        """
        self._logger.info("Workflow done!.")
        self._logger.info("SDDM map: %s",
                self.f['sddm'](iter=self.iterations[-1]))
        self._logger.info("Average JAC: %s:", self.f['template_jacobian_avg']())
        self._logger.info("Template: %s",
                self.f['iteration_resliced_avg'](iter=self.iterations[-1]))

    def _create_smoothed_jacobian(self):
        """
        Creates jacobian of the final deformation fields. If needed, the
        jacobian might be smoothed with gaussian blur as well as resampled.
        """
        dims = self.options.antsDimension
        if self.options.jacobianSmoothResample is None:
            jacobian_resample_settings = None
            jacobian_smoothing_settings = None
        else:
            jacobian_resample_settings = \
                self.options.jacobianSmoothResample[3:3+dims]
            jacobian_smoothing_settings =\
                self.options.jacobianSmoothResample[0:0+dims]

        commands = []

        for i in self.slice_range:
            command = pos_mdt_wrappers.ants_smoothed_jacobian(
                dimension = self.options.antsDimension,
                input_image = self.f['template_transf_f'](idx=i),
                output_naming = self.f['template_jacobian_naming'](idx=i),
                resample = jacobian_resample_settings,
                smooth = jacobian_smoothing_settings)
            commands.append(copy.deepcopy(command))
        self.execute(commands)

        input_images_list = \
            map(lambda x: self.f['template_jacobian'](idx=x), self.slice_range)
        command = pos_wrappers.average_images(
            dimension = self.options.antsDimension,
            input_images = input_images_list,
            output_image = self.f['template_jacobian_avg']())
        self.execute(command)


    def calculate_convergence(self):
        """
        Calculate the template convergence. The convergence is calculated by
        substracting mean square difference of image j and i. This helps to
        determine if the template converges over consecutive iterations or not.
        """

        pairs = zip(self.iterations[:-1], self.iterations[1:])

        for (i, j) in pairs:
            command = pos_mdt_wrappers.sddm_convergence( \
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
        parser.add_option('--settingsFile', default=None,
                dest='settingsFile', action='store', type='str',
                help='Use a file to provide registration settings.')
        parser.add_option('--jacobianSmoothResample', default=None,
                dest='jacobianSmoothResample', action='store', type='float',
                nargs=6,
                help='6 floats: smoothing in vox, resampling in %. third and sixth values are for padding purposes for 2d images. default: 1 1 1 100 100 100')

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

