#!/usr/bin/python
import os,sys
import numpy as np

from optparse import OptionParser, OptionGroup
from config import Config
import copy

from pos_deformable_wrappers import preprocess_slice_volume, visualize_wrap_field
from pos_wrapper_skel import generic_workflow
from deformable_histology_iterations import deformable_reconstruction_iteration
import pos_wrappers
import pos_parameters


class replace_values(pos_wrappers.generic_wrapper):
    """
    """

    _template = """ c{dimension}d -verbose \
            {input_image} \
            {replacement} \
            -o {output_image} """

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'replacement' : pos_parameters.list_parameter('replacement', [], str_template = "-replace {_list}"),
        'input_image'  : pos_parameters.filename_parameter('input_image'),
        'output_image' : pos_parameters.filename_parameter('output_image')
        }

class evaluate_reg(pos_wrappers.generic_wrapper):
    """
    """

    _template = """ c{dimension}d {fixed_mask} {deformed_mask} -overlap 1 >> {eval_file}; \
        c{dimension}d {fixed_mask} {deformed_mask} -msq >> {eval_file}; \
        c{dimension}d {fixed_mask} {deformed_mask} -ncor >> {eval_file}; \
        c{dimension}d {fixed_image} {deformed_image} -ncor >> {eval_file}; \
        c{dimension}d {fixed_image} {deformed_image} -nmi >> {eval_file}; \
        LabelOverlapMeasures {dimension} {fixed_segmentation} {deformed_segmentation} {segmentation_file};"""

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
        'raw_images' : pos_parameters.filename('src_images', work_dir = '01_raw_images', str_template = '{id}.nii.gz'),
        'init_affine' : pos_parameters.filename('init_affine', work_dir = '02_init_supp', str_template = 'initial_affine.txt'),
        'init_warp'   : pos_parameters.filename('init_warp', work_dir = '02_init_supp', str_template = 'initial_warp.nii.gz'),
        'constant_images' : pos_parameters.filename('const_images', work_dir = '03_const_images', str_template = '{idx:04d}.nii.gz'),
        'init_images' : pos_parameters.filename('src_images', work_dir = '04_iniit_images', str_template = '{id}.nii.gz'),
        # Iteration
        'iteration'  : pos_parameters.filename('iteration', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_input'  : pos_parameters.filename('iteration_images', work_dir = '05_iterations', str_template = '{iter:04d}/01_images/{id}.nii.gz'),
        'iteration_out_naming' : pos_parameters.filename('iteration_out_naming', work_dir = '05_iterations', str_template = '{iter:04d}/11_transformations/{iter:04d}'),
        'iter_transform'  : pos_parameters.filename('iter_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{iter:04d}Warp.nii.gz'),
        'iter_cum_naming'  : pos_parameters.filename('iter_cum_wrap', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{iter:04d}Cumulative'),
        'iter_cum_wrap'  : pos_parameters.filename('iter_cum_wrap', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{iter:04d}CumulativeWarp.nii.gz'),
        'iter_eval'  : pos_parameters.filename('iter_eval', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{iter:04d}eval.txt'),
        'iter_seg'  : pos_parameters.filename('iter_seg', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{iter:04d}seg.txt'),
        'iteration_resliced'  : pos_parameters.filename('iteration_resliced', work_dir = '05_iterations', str_template = '{iter:04d}/20_resliced/{id}.nii.gz')
        # Final resliced
        }

    def _overrideDefaults(self):
        self.cfg = Config(open(self.options.settingsFile))

    def launch(self):
        for i in range(len(self.cfg.iterations)):
            self._preprocess_images(i)
            self._register(i)
            self._preprocess_images(i, reslice=True)
            self._jacobian(i)
            self._evaluate(i)

    def _preprocess_images(self, iteration, reslice = False):

        target_dir = 'iteration_input'
        if reslice:
            target_dir = 'iteration_resliced'

        for metric in self.cfg.iterations[iteration].metrics:

            if metric.type == "PSE":

                repl_fixed = map(lambda (x, y):
                        "%d %d " % (x, y),
                        metric.fixed_replacement)

                repl_moving = map(lambda (x, y):
                        "%d %d " % (x, y),
                        metric.moving_replacement)

                image_id = metric.fixed_points
                command = replace_values(
                    dimension = 3,
                    input_image = self.cfg.files.get(image_id).path,
                    replacement = repl_fixed,
                    output_image = self.f[target_dir](iter=iteration,id=image_id))
                print command
               #self.execute(command)

                deformable_list = map(lambda j: self.f['iter_transform'](idx=0,iter=j), range(iteration+1))
                if iteration == 0:
                    deformable_list = []
                deformable_list = [self.f['init_warp']] + deformable_list

                command = pos_wrappers.ants_reslice(
                    dimension = 3,
                    moving_image = self.f[target_dir](iter=iteration,id=image_id),
                    output_image = self.f[target_dir](iter=iteration,id=image_id),
                    reference_image = self.cfg.files.get(image_id).path,
                    useNN = None,
                    useBspline = None,
                    deformable_list = deformable_list,
                    affine_list = [self.f['init_affine']()])
                print command
               #self.execute(command)

                image_id = metric.moving_points
                command = replace_values(
                    dimension = 3,
                    input_image = self.cfg.files.get(image_id).path,
                    replacement = repl_moving,
                    output_image = self.f[target_dir](iter=iteration,id=image_id))
                print command
               #self.execute(command)

                command = pos_wrappers.ants_reslice(
                    dimension = 3,
                    moving_image = self.f[target_dir](iter=iteration,id=image_id),
                    output_image = self.f[target_dir](iter=iteration,id=image_id),
                    reference_image = self.cfg.files.get(image_id).path,
                    useNN = None,
                    useBspline = None,
                    deformable_list = deformable_list,
                    affine_list = [self.f['init_affine']()])
                print command
               #self.execute(command)

            image_id = metric.fixed_image
            command = pos_wrappers.ants_reslice(
                dimension = 3,
                moving_image = self.cfg.files.get(image_id).path,
                output_image = self.f[target_dir](iter=iteration,id=image_id),
                reference_image = self.cfg.files.get(image_id).path,
                useNN = None,
                useBspline = None,
                deformable_list = deformable_list,
                affine_list = [self.f['init_affine']()])
            print command
            #self.execute(command)

            image_id = metric.moving_image
            command = pos_wrappers.ants_reslice(
                dimension = 3,
                moving_image = self.cfg.files.get(image_id).path,
                output_image = self.f['iteration_input'](iter=iteration,id=image_id),
                reference_image = self.cfg.files.get(image_id).path,
                useNN = None,
                useBspline = None,
                deformable_list = deformable_list,
                affine_list = [self.f['init_affine']()])
            #self.execute(command)
            print command

    def _register(self, iteration):
        iterdata = self.cfg.iterations[iteration]

        metrics = []
        for me in iterdata.metrics:
            if me.type == "PSE":
                metric = pos_wrappers.ants_point_set_estimation_metric(
                    fixed_image = self.f['iteration_input'](iter=iteration,id=me.fixed_image),
                    moving_image = self.f['iteration_input'](iter=iteration,id=me.moving_image),
                    fixed_points = self.f['iteration_input'](iter=iteration,id=me.fixed_points),
                    moving_points = self.f['iteration_input'](iter=iteration,id=me.moving_points),
                    weight = me.weight,
                    point_set_percentage = me.point_set_percentage,
                    point_set_sigma = me.point_set_sigma,
                    boundary_points_only = me.boundary_points_only)
            if me.type == "I":
                metric = pos_wrappers.ants_intensity_meric(
                    metric = me.kind,
                    fixed_image = self.f['iteration_input'](iter=iteration,id=me.fixed_image),
                    moving_image = self.f['iteration_input'](iter=iteration,id=me.moving_image),
                    weight =  me.weight,
                    parameter = me.parameter)
            metrics.append(metric)

        command = pos_wrappers.ants_registration(
            dimension = 3,
            transformation = tuple(iterdata.transformation),
            regularization = tuple(iterdata.regularization),
            outputNaming = self.f['iteration_out_naming'](iter=iteration,idx=0),
            imageMetrics = metrics,
            iterations = iterdata.iterations,
            affineIterations = [0],
            rigidAffine = int(False),
            histogramMatching = int(True),
            continueAffine = int(False),
            allMetricsConverge = int(iterdata.all_metrics_converge),
            affineMetricType = "CC",
            maskImage = self.cfg.files.get(iterdata.fixed_image_mask).path,
            miOption = [32, 1600])
        print command

    def _jacobian(self, iteration):
        deformable_list = map(lambda j: self.f['iter_transform'](idx=0,iter=j), range(iteration+1))
        deformable_list = [self.f['init_warp']] + deformable_list

        command = pos_wrappers.ants_jacobian(
            dimension = 3,
            input_image = self.f['iter_transform'](iter=iteration),
            output_naming =self.f['iteration_out_naming'](iter=iteration,idx=0))
        print command

        command = pos_wrappers.ants_compose_multi_transform(
            dimension = 3,
            output_image = self.f['iter_cum_wrap'](iter=iteration),
            reference_image = self.cfg.files.fixed.path,
            deformable_list = deformable_list,
            affine_list = [self.f['init_affine']()])
        print command

        command = pos_wrappers.ants_jacobian(
            dimension = 3,
            input_image = self.f['iter_cum_wrap'](iter=iteration),
            output_naming =self.f['iter_cum_naming'](iter=iteration))
        print command

    def _evaluate(self, iteration):

        command = evaluate_reg(
            dimension = 3,
            fixed_mask = self.f['iteration_resliced'](iter=iteration,id='fixed_mask'),
            deformed_mask = self.f['iteration_resliced'](iter=iteration,id='moving_mask'),
            fixed_image = self.f['iteration_resliced'](iter=iteration,id='fixed'),
            deformed_image = self.f['iteration_resliced'](iter=iteration,id='moving'),
            fixed_segmentation =  self.f['iteration_resliced'](iter=iteration,id='fixed_seg'),
            deformed_segmentation =  self.f['iteration_resliced'](iter=iteration,id='moving_seg'),
            eval_file = self.f['iter_eval'](iter=iteration),
            segmentation_file =self.f['iter_seg'](iter=iteration))
        print command


    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('--settingsFile', default=None,
                dest='settingsFile', action='store', type='str',
                help='Use a file to provide registration settings.')

        return parser

if __name__ == '__main__':
    options, args = multimodal_coregistration.parseArgs()
    d = multimodal_coregistration(options, args)
    d.launch()

