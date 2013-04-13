#!/usr/bin/python
import copy
import numpy as np
from pos_deformable_wrappers import blank_slice_deformation_wrapper
from pos_wrapper_skel import generic_workflow
import pos_wrappers
import pos_parameters

class deformable_reconstruction_iteration(generic_workflow):
    _f = { \
        'src_slice'  : pos_parameters.filename('src_slice',  work_dir = '00_src_slices',      str_template =  '{idx:04d}.nii.gz'),
        'processed'  : pos_parameters.filename('processed',  work_dir = '01_process_slices',  str_template =  'average.nii.gz'),
        'outline'    : pos_parameters.filename('outline',    work_dir = '02_outline',         str_template =  '{idx:04d}.nii.gz'),
        'poutline'   : pos_parameters.filename('poutline',   work_dir = '03_poutline',        str_template =  '{idx:04d}.nii.gz'),
        'transform'  : pos_parameters.filename('transform',  work_dir = '11_transformations', str_template =  '{idx:04d}Warp.nii.gz'),
        'inverse'    : pos_parameters.filename('inverse',    work_dir = '11_transformations', str_template =  '{idx:04d}InverseWarp.nii.gz'),
        'affine'     : pos_parameters.filename('transform',  work_dir = '11_transformations', str_template =  '{idx:04d}Affine.txt'),
        'out_naming' : pos_parameters.filename('out_naming', work_dir = '11_transformations', str_template = '{idx:04d}'),
        'resliced'   : pos_parameters.filename('resliced',   work_dir = '21_resliced',        str_template = '{idx:04d}.nii.gz'),
        'resliced_outline' : pos_parameters.filename('resliced_outline', work_dir = '22_resliced_outline', str_template = '{idx:04d}.nii.gz'),
        }

    _usage = ""

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

        start, end = self._get_edges()
        self.slice_range = range(start, end +1)

        # Convert the number of iterations string to list of integers
        self.options.antsIterations = \
                map(int, self.options.antsIterations.strip().split("x"))

        self.options.antsAffineIterations = \
                map(int, self.options.antsAffineIterations.strip().split("x"))

    def _get_edges(self):
        """
        Convenience function for returning frequently used numbers
        """
        return (self.options.startSlice,
                self.options.endSlice)

    def _preprocess_images(self):
        return self._average_images()

    def _average_images(self):
        commands = []
        files_to_average = []
        weights = []

        for j in self.slice_range:
            files_to_average.append(self.f['src_slice'](idx=j))
            weights.append(1.0)

        command = pos_wrappers.images_weighted_average(\
                    dimension = self.options.antsDimension,
                    input_images = files_to_average,
                    weights = weights,
                    output_type = 'float',
                    output_image = self.f['processed']())
        commands.append(copy.deepcopy(command))
        self.execute(commands)

    def _get_default_reg_settings(self):
        return (self.options.antsImageMetric,
                self.options.antsImageMetricOpt,
                self.options.antsIterations,
                self.options.antsAffineIterations,
                self.options.antsTransformation,
                self.options.antsRegularizationType,
                self.options.antsRegularization)

    def _calculate_transformations_masked(self):
        """
        Generate and invoke commands for generating deformation fields. Commands
        are generated based on a number of factors. The actual dependencies
        what is registered to what and how its quite complicated and it is my
        sweet secret how it is actually calculated.
        """

        commands = []

        for i in self.slice_range:
            metrics  = []

            fixed_image_type = 'processed'
            fixed_outline_type='poutline'
            mask_image = None

            r_metric, parameter, iterations, affine_iterations, \
            transf_grad, reg_type, reg_ammount =\
                    self._get_default_reg_settings()

            if self.parent_process.current_iteration == 0:
                iterations = [0]
                allMetricsConverge = None
            else:
                affine_iterations = [0]
                allMetricsConverge = int(True)

            metric = pos_wrappers.ants_intensity_meric(
                        fixed_image  = self.f[fixed_image_type](),
                        moving_image = self.f['src_slice'](idx=i),
                        metric = r_metric,
                        weight = 1.0,
                        parameter = parameter)
            metrics.append(copy.deepcopy(metric))

            registration = pos_wrappers.ants_registration(
                        dimension = self.options.antsDimension,
                        outputNaming = self.f['out_naming'](idx=i),
                        iterations = iterations,
                        transformation = ('SyN', [transf_grad]),
                        regularization = (reg_type, reg_ammount),
                        affineIterations = affine_iterations,
                        continueAffine = None,
                        rigidAffine = int(False),
                        imageMetrics = metrics,
                        histogramMatching = int(True),
                        maskImage = mask_image,
                        allMetricsConverge = allMetricsConverge)
            commands.append(copy.deepcopy(registration))

        self.execute(commands)

    def launch(self):
        """
        Launching a deformable registration iteration means:

            * Assigning weights for the images by reading them from files or
              applying weighting functions.
            * Preprocessing images: calculating images that will be used to
              perform registration based on the resliced images from previous
              iteration.
            * Launching actual registration process and calculating deformation
              fields.
        """

        self._preprocess_images()
        self._calculate_transformations_masked()

    def __call__(self, *args, **kwargs):
        return self.launch()

