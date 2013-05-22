#!/usr/bin/python
import os

from optparse import OptionParser, OptionGroup
from config import Config
import copy

import pos_wrappers
import pos_parameters
from pos_wrapper_skel import generic_workflow


class evaluate_registration_results(pos_wrappers.generic_wrapper):
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


class archive_registration_results(pos_wrappers.generic_wrapper):
    """
    """

    _template = """tar -cvvzf  {archive_filename}.tgz {job_working_dir}/. ; \
            mv -fv {archive_filename}.tgz {backup_directory}"""

    _parameters = {
        'job_working_dir' : pos_parameters.filename_parameter('job_working_dir'),
        'archive_filename' : pos_parameters.filename_parameter('archive_filename'),
        'backup_directory' : pos_parameters.filename_parameter('backup_directory')
    }


class multimodal_coregistration(generic_workflow):
    """
    """

    _f = { \
         # Initial grayscale slices
        'raw_images' : pos_parameters.filename('raw_images', work_dir = '01_raw_images', str_template = '{id}.nii.gz'),
        'init_affine' : pos_parameters.filename('init_affine', work_dir = '02_init_supp', str_template = 'initial_affine.txt'),
        'init_warp'   : pos_parameters.filename('init_warp', work_dir = '02_init_supp', str_template = 'initial_warp.nii.gz'),
        'init_images' : pos_parameters.filename('src_images', work_dir = '04_init_images', str_template = '{id}.nii.gz'),
        # Iteration
        'iteration'  : pos_parameters.filename('iteration', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_transform' : pos_parameters.filename('iteration_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/resultWarp.nii.gz'),
        'iteration_resliced'  : pos_parameters.filename('iteration_resliced', work_dir = '05_iterations', str_template = '{iter:04d}/20_resliced/{id}.nii.gz')
        }

    def _overrideDefaults(self):
        # Load the registration setting from the provided file.
        self.cfg = Config(open(self.options.settingsFile))

    def launch(self):
        """
        Execute the registration process. The registration consists of several
        steps.:

            * Copying the initial files (e.g. images to be used, initial
              ransfomrations, etc.) to the working directory of the process.
            * Executing consecutive iteration step.
            * Compression if the results and backing them up.
        """

        # Copy the images, initial adffine and deformable registration and the
        # configuration file to the working directory.
        self._copy_initial_files()

        for i in range(len(self.cfg.iterations)):
            # Gradb the current iteration index:
            self.iteration = i

            # Deep copy the arguments and options passed via the command line.
            # We use deep copy as the setting may be changed by the child
            # process and we don't want them to backpropagate.
            step_options = copy.deepcopy(self.options)
            step_args = copy.deepcopy(self.args)

            # Override working directory of the child process. Instead of having
            # the default wokring directory we will nest it within the directory
            # of the parent process (pretty cool, isin't it?).
            step_options.workdir = os.path.join(self.f['iteration'](iter=i))
            single_step = multimodal_coregistration_iteration(step_options, step_args)

            # Pass the current iteration index and configuration to the child
            # process (they are passed by reference as they will not be
            # changed).
            single_step.parent = self
            single_step.iteration = i
            single_step.cfg = self.cfg

            # The we need to set up the input directory of the child process to
            # be (in the first iteration) the input of the whole process, and
            # (in case of all the other iterations) the output of the previous
            # iteration.
            if i!= 0:
                single_step.f['input'].override_dir = \
                    os.path.dirname(self.f['iteration_resliced'](iter=i-1,id=0))

            # Then just execute the calculations.
            single_step()

        # Do some cleanup, compress the results and copy the compressed file to
        # the backup directory. Ten, copy the final resliced image to the
        # provided directory.
        self._tidy_up()
        self._backup_results()
        self._propagate_results()

    def _copy_initial_files(self):
        """
        """
        # Generate the start tag - a file created at the beginning of the
        # calculations (according to its timestamp).
        start_file = os.path.join(self.options.workdir,"start")
        self._logger.debug("Touching 'start' file: %s", start_file)
        command = pos_wrappers.touch_wrapper(files=[start_file])
        self.execute(command)

        # Copy all files enumerated in the "files" section of the configuration
        # file into the working directory.
        commands = []
        for image_id in self.cfg.files:
            source_file_path = self.cfg.files.get(image_id).path
            self._logger.debug("Copying source image file %s: %s",
                    image_id, source_file_path)

            command = pos_wrappers.copy_wrapper(
                source = [source_file_path],
                target = self.f['raw_images'](id=image_id))
            commands.append(copy.deepcopy(command))

        # Then copy the initial affine tranformation and the iniial deformation
        # field to the working directory of the process.
        for f,t in [(self.cfg.parameters.initial_deformable, 'init_warp'),
                    (self.cfg.parameters.initial_affine, 'init_affine')]:
            if os.path.isfile(f):
                command = pos_wrappers.copy_wrapper(
                    source = [f],
                    target = self.f[t]())
                commands.append(copy.deepcopy(command))

        # Copy the configuration file itself to the working directory.
        command = pos_wrappers.copy_wrapper(
                source = [self.options.settingsFile],
                target = self.options.workdir)
        commands.append(copy.deepcopy(command))

        # Copy the script file itself to the working directory in order
        # to be able to reproduce the results
        command = pos_wrappers.copy_wrapper(
                source = [os.path.abspath(__file__)],
                target = self.options.workdir)
        commands.append(copy.deepcopy(command))

        self.execute(commands)

    def _tidy_up(self):
        """
        """
        # Touch a file to mark the end of the calculations:
        stop_file = os.path.join(self.options.workdir,"stop")
        self._logger.debug("Touching 'stop' file: %s", stop_file)
        command = pos_wrappers.touch_wrapper(files=[stop_file])
        self.execute(command)

    def _backup_results(self):
        """
        Compress and copy the results to the backup directory if the backup
        directory is provided in the configuration file. In the other case, this
        step is not executed.
        """
        if self.cfg.parameters.backup_dir:
            command = archive_registration_results(
                job_working_dir = self.options.workdir,
                archive_filename = self.options.jobId,
                backup_directory = self.cfg.parameters.backup_dir)
            self.execute(command)

    def _propagate_results(self):
        """
        Copy the resliced moving image (result from the last iteration) to a
        directory provided in the configuration file. If the directory is not
        provided, this step is not executed.
        """

        if self.cfg.parameters.propagation:
            i = self.iteration # just an alias
            target_file = os.path.join(self.cfg.parameters.propagation,
                                       self.options.jobId + ".nii.gz")
            command = pos_wrappers.copy_wrapper(
                source = [self.f['iteration_resliced'](iter=i,id='moving')],
                target = target_file)
            self.execute(command)

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

        commands = []
        for metric in self.cfg.iterations[i].metrics:

            if metric.type == "PSE":
                image_id = metric.moving_points
                command = self._reslice(image_id, nn=True)
                commands.append(copy.deepcopy(command))

            image_id = metric.moving_image
            command = self._reslice(image_id)
            commands.append(copy.deepcopy(command))

        self.execute(commands)

    def _get_file(self, image_id):
        """
        Get the source image according to its image_id as provided in the
        configuration file.
        """
        return self.parent.f['raw_images'](id=image_id)

    def _reslice(self, image_id, nn=False):
        """
        """
        affine_list, deformable_list = \
            self._get_transformation_list()

        command = pos_wrappers.ants_reslice(
            dimension = 3,
            moving_image = self._get_file(image_id),
            output_image = self.f['resliced'](id=image_id),
            reference_image = self._get_file('fixed'),
            useNN = [None,bool(nn)][int(nn)],
            useBspline = None,
            deformable_list = deformable_list,
            affine_list = affine_list)
        return command

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
            if me.type in ["PSE"]:
                metric = pos_wrappers.ants_point_set_estimation_metric(
                    fixed_image = self.parent.f['raw_images'](id=me.fixed_image),
                    moving_image = self.f['input'](id=me.moving_image),
                    fixed_points = self.parent.f['raw_images'](id=me.fixed_points),
                    moving_points = self.f['input'](id=me.moving_points),
                    weight = me.weight,
                    point_set_percentage = me.point_set_percentage,
                    point_set_sigma = me.point_set_sigma,
                    boundary_points_only = me.boundary_points_only)

            if me.type in ["CC", "MSQ"]:
                metric = pos_wrappers.ants_intensity_meric(
                    metric = me.type,
                    fixed_image = self.parent.f['raw_images'](id=me.fixed_image),
                    moving_image = self.f['input'](id=me.moving_image),
                    weight =  me.weight,
                    parameter = me.parameter)
            metrics.append(metric)

        mask_image = None
        if iterdata.fixed_image_mask:
            mask_image = self.parent.f['raw_images'](id='fixed_mask')

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

        command = evaluate_registration_results(
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
