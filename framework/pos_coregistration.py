#!/usr/bin/python
import os,sys
import numpy as np

from optparse import OptionParser, OptionGroup
from config import Config
import copy

import pos_wrappers
import pos_parameters
from pos_wrapper_skel import generic_workflow


class evaluate_reg(pos_wrappers.generic_wrapper):
    """
    """

    _template = """ c{dimension}d {fixed_mask} {deformed_mask} -overlap 1 >> {eval_file}; \
        c{dimension}d {fixed_mask} {deformed_mask} -msq >> {eval_file}; \
        c{dimension}d {fixed_mask} {deformed_mask} -ncor >> {eval_file}; \
        c{dimension}d {fixed_image} {deformed_image} -ncor >> {eval_file}; \
        c{dimension}d {fixed_image} {deformed_image} -nmi >> {eval_file}; \
        LabelOverlapMeasures {dimension} {fixed_segmentation} {deformed_segmentation} >> {segmentation_file};"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'fixed_mask'  : pos_parameters.filename_parameter('fixed_mask'),
        'deformed_mask'  : pos_parameters.filename_parameter('deformed_mask'),
        'fixed_image'  : pos_parameters.filename_parameter('fixed_image'),
        'deformed_image'  : pos_parameters.filename_parameter('deformed_image'),
        'fixed_segmentation'  : pos_parameters.filename_parameter('fixed_segmentation'),
        'deformed_segmentation'  : pos_parameters.filename_parameter('deformed_segmentation'),
        'eval_file'  : pos_parameters.filename_parameter('eval_file'),
        'segmentation_file'  : pos_parameters.filename_parameter('segmentation_file')
    }


class multimodal_coregistration(generic_workflow):
    """
    """

    _f = { \
         # Initial grayscale slices
        'raw_images' : pos_parameters.filename('raw_images', work_dir = '01_raw_images', str_template = '{id}.nii.gz'),
        'init_affine' : pos_parameters.filename('init_affine', work_dir = '02_init_supp', str_template = 'initial_affine.txt'),
        'init_warp'   : pos_parameters.filename('init_warp', work_dir = '02_init_supp', str_template = 'initial_warp.nii.gz'),
        'init_images' : pos_parameters.filename('src_images', work_dir = '04_iniit_images', str_template = '{id}.nii.gz'),
        # Iteration
        'iteration'  : pos_parameters.filename('iteration', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_transform'  : pos_parameters.filename('iteration_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/resultWarp.nii.gz'),
        'iteration_resliced'  : pos_parameters.filename('iteration_resliced', work_dir = '05_iterations', str_template = '{iter:04d}/20_resliced/{id}.nii.gz')
        }

    def _overrideDefaults(self):
        self.cfg = Config(open(self.options.settingsFile))

    def launch(self):
        self._copy_initial_files()

        for i in range(len(self.cfg.iterations)):
            self.iteration = i

            step_options = copy.deepcopy(self.options)
            step_args = copy.deepcopy(self.args)

            step_options.workdir = os.path.join(self.f['iteration'](iter=i))
            single_step = multimodal_coregistration_iteration(step_options, step_args)
            single_step.parent = self
            single_step.iteration = i
            single_step.cfg = self.cfg

            if i!= 0:
                single_step.f['input'].override_dir = \
                    os.path.dirname(self.f['iteration_resliced'](iter=i-1,id=0))

            single_step()

    def _copy_initial_files(self):
        """
        """
        commands = []
        for image_id in self.cfg.files:
            command = pos_wrappers.copy_wrapper(
                source = [self.cfg.files.get(image_id).path],
                target = self.f['raw_images'](id=image_id))
            commands.append(copy.deepcopy(command))

        for f,t in [(self.cfg.parameters.initial_deformable, 'init_warp'),
                    (self.cfg.parameters.initial_affine, 'init_affine')]:
            if os.path.isfile(f):
                command = pos_wrappers.copy_wrapper(
                    source = [f],
                    target = self.f[t]())
                commands.append(copy.deepcopy(command))

        command = pos_wrappers.copy_wrapper(
                source = [self.options.settingsFile],
                target = self.options.workdir)
        commands.append(copy.deepcopy(command))

        self.execute(commands)

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('--settingsFile', default=None,
                dest='settingsFile', action='store', type='str',
                help='Use a file to provide registration settings.')

        return parser

class multimodal_coregistration_iteration(generic_workflow):
    _f = { \
        'input'      : pos_parameters.filename('images', work_dir = '01_images', str_template = '{id}.nii.gz'),
        'out_naming' : pos_parameters.filename('out_naming', work_dir = '11_transformations', str_template = 'result'),
        'transform'  : pos_parameters.filename('transform', work_dir = '11_transformations', str_template =  'resultWarp.nii.gz'),
        'transform_inverse'  : pos_parameters.filename('transform_inverse', work_dir = '11_transformations', str_template = 'resultInverseWarp.nii.gz'),
        'cum_naming'         : pos_parameters.filename('cum_wrap', work_dir = '11_transformations', str_template = 'resultCumulative'),
        'cum_wrap' : pos_parameters.filename('cum_wrap', work_dir = '11_transformations', str_template = 'resultCumulativeWarp.nii.gz'),
        'eval'     : pos_parameters.filename('eval', work_dir = '11_transformations', str_template = 'eval.txt'),
        'seg'      : pos_parameters.filename('seg', work_dir = '11_transformations', str_template = 'seg.txt'),
        'resliced' : pos_parameters.filename('resliced', work_dir = '20_resliced', str_template = '{id}.nii.gz')
        }

    def _get_file(self, image_id):
        return self.parent.f['raw_images'](id=image_id)

    def _get_transformation_list(self):
        iteration = self.iteration
        deformable_list = []
        affine_list = []

        for j in range(iteration+1):
            iter_deformable = self.parent.f['iteration_transform'](iter=j)
            deformable_list.append(iter_deformable)

        if os.path.isfile(self.cfg.parameters.initial_deformable):
            deformable_list = [self.parent.f['init_warp']()] + deformable_list

        if os.path.isfile(self.cfg.parameters.initial_affine):
            affine_list.append(self.parent.f['init_affine']())

        return affine_list, deformable_list

    def _preprocess_images(self):
        i = self.iteration

        commands = []
        for metric in self.cfg.iterations[i].metrics:

            if metric.type == "PSE":
                image_id = metric.moving_points
                command = self._prepare_image(image_id)
                commands.append(copy.deepcopy(command))

            image_id = metric.moving_image
            command = self._prepare_image(image_id)
            commands.append(copy.deepcopy(command))

        self.execute(commands)

    def _reslice_images(self):
        i = self.iteration

        target_dir = 'resliced'

        for metric in self.cfg.iterations[i].metrics:

            if metric.type == "PSE":
                image_id = metric.moving_points
                self._reslice(image_id, target_dir, nn=True)

            image_id = metric.moving_image
            self._reslice(image_id, target_dir)

    def _reslice(self, image_id, target_dir, nn=False):
        """
        """
        affine_list, deformable_list = \
            self._get_transformation_list()

        command = pos_wrappers.ants_reslice(
            dimension = 3,
            moving_image = self._get_file(image_id),
            output_image = self.f[target_dir](id=image_id),
            reference_image = self._get_file('fixed'),
            useNN = bool(nn),
            useBspline = None,
            deformable_list = deformable_list,
            affine_list = affine_list)
        self.execute(command)

    def _prepare_image(self, image_id):
        """
        """
        command = pos_wrappers.copy_wrapper(
            source = [self._get_file(image_id)],
            target = self.f['input'](id=image_id))
        return command

    def _register(self):
        i = self.iteration
        iterdata = self.cfg.iterations[i]

        metrics = []

        for me in iterdata.metrics:
            if me.type == "PSE":
                metric = pos_wrappers.ants_point_set_estimation_metric(
                    fixed_image = self.parent.f['raw_images'](id=me.fixed_image),
                    moving_image = self.f['input'](id=me.moving_image),
                    fixed_points = self.parent.f['raw_images'](id=me.fixed_points),
                    moving_points = self.f['input'](id=me.moving_points),
                    weight = me.weight,
                    point_set_percentage = me.point_set_percentage,
                    point_set_sigma = me.point_set_sigma,
                    boundary_points_only = me.boundary_points_only)

            if me.type == "I":
                metric = pos_wrappers.ants_intensity_meric(
                    metric = me.kind,
                    fixed_image = self.parent.f['raw_images'](id=me.fixed_image),
                    moving_image = self.f['input'](id=me.moving_image),
                    weight =  me.weight,
                    parameter = me.parameter)
            metrics.append(metric)

        mask_image = None
        if iterdata.fixed_image_mask:
            mask_image = self.parent.f['raw_images'](id='fixed_mask')
        print "--------------------", mask_image

        command = pos_wrappers.ants_registration(
            dimension = 3,
            transformation = tuple(iterdata.transformation),
            regularization = tuple(iterdata.regularization),
            outputNaming = self.f['out_naming'](),
            imageMetrics = metrics,
            iterations = iterdata.iterations,
            affineIterations = [0],
            rigidAffine = int(False),
            histogramMatching = int(True),
            continueAffine = int(False),
            allMetricsConverge = int(iterdata.all_metrics_converge),
            affineMetricType = "CC",
            maskImage = mask_image,
            miOption = [32, 1600])
        self.execute(command)

    def _jacobian(self):
        affine_list, deformable_list = \
            self._get_transformation_list()

        command = pos_wrappers.ants_jacobian(
            dimension = 3,
            input_image = self.f['transform'](),
            output_naming =self.f['out_naming']())
        self.execute(command)

        command = pos_wrappers.ants_compose_multi_transform(
            dimension = 3,
            output_image = self.f['cum_wrap'](),
            reference_image = self.cfg.files.fixed.path,
            deformable_list = deformable_list,
            affine_list = affine_list)
        self.execute(command)

        command = pos_wrappers.ants_jacobian(
            dimension = 3,
            input_image = self.f['cum_wrap'](),
            output_naming =self.f['cum_naming']())
        self.execute(command)

    def _evaluate(self):
        i = self.iteration

        command = evaluate_reg(
            dimension = 3,
            fixed_mask = self.parent.f['raw_images'](id='fixed_mask'),
            deformed_mask = self.f['resliced'](id='moving_mask'),
            fixed_image = self.parent.f['raw_images'](id='fixed'),
            deformed_image = self.f['resliced'](id='moving'),
            fixed_segmentation =  self.parent.f['raw_images'](id='fixed_seg'),
            deformed_segmentation =  self.f['resliced'](id='moving_seg'),
            eval_file = self.f['eval'](),
            segmentation_file =self.f['seg']())
        self.execute(command)

    def launch(self):
        if self.iteration == 0:
            self._preprocess_images()
        self._register()
        self._reslice_images()
        self._jacobian()
        self._evaluate()

    def __call__(self, *args, **kwargs):
        return self.launch()


if __name__ == '__main__':
    options, args = multimodal_coregistration.parseArgs()
    d = multimodal_coregistration(options, args)
    d.launch()
