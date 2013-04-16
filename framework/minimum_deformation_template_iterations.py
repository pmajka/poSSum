#!/usr/bin/python
import copy
import numpy as np

import pos_wrappers
import pos_parameters
from pos_wrapper_skel import generic_workflow

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
    _template = """c{dimension}d  {input_images} -scale {variance_n} -sqrt -o {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'input_images': pos_parameters.list_parameter('input_images', [], str_template='{_list}'),
        'variance_n' : pos_parameters.value_parameter('variance_n', 1),
        'output_image': pos_parameters.filename_parameter('output_image'),
        'output_type': pos_parameters.string_parameter('output_type', 'uchar', str_template='-type {_value}')
    }



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


class deformable_reconstruction_iteration(generic_workflow):
    _f = { \
        'src_slice'  : pos_parameters.filename('src_slice',  work_dir = '00_src_slices',      str_template =  '{idx:04d}.nii.gz'),
        'processed'  : pos_parameters.filename('processed',  work_dir = '01_process_slices',  str_template =  'average.nii.gz'),
        'out_naming' : pos_parameters.filename('out_naming', work_dir = '11_transformations', str_template = '{idx:04d}'),
        'forward'    : pos_parameters.filename('transform',  work_dir = '11_transformations', str_template =  '{idx:04d}Warp.nii.gz'),
        'forward_average'    : pos_parameters.filename('transform_average',    work_dir = '11_transformations', str_template = 'averageWarp.nii.gz'),
        'inverse'    : pos_parameters.filename('inverse',    work_dir = '11_transformations', str_template =  '{idx:04d}InverseWarp.nii.gz'),
        'inverse_average'    : pos_parameters.filename('inverse',    work_dir = '11_transformations', str_template =  'averageInverseWarp.nii.gz'),
        'affine'     : pos_parameters.filename('affine',  work_dir = '11_transformations', str_template =  '{idx:04d}Affine.txt'),
        'affine_average'     : pos_parameters.filename('affine_average',  work_dir = '11_transformations', str_template =  'averageAffine.txt'),
        'resliced'   : pos_parameters.filename('resliced',   work_dir = '21_resliced',        str_template = '{idx:04d}.nii.gz'),
        'resliced_average'   : pos_parameters.filename('resliced_average',   work_dir = '21_resliced',        str_template = 'average.nii.gz'),
        }

    _usage = ""

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

        start = self.options.firstImageIndex
        end = self.options.lastImageIndex
        self.slice_range = range(start, end +1)

        # Convert the number of iterations string to list of integers
        self.options.antsIterations = \
                map(int, self.options.antsIterations.strip().split("x"))

        self.options.antsAffineIterations = \
                map(int, self.options.antsAffineIterations.strip().split("x"))

    def _preprocess_images(self):
        return self._average_images()

    def _average_images(self):
        commands = []
        files_to_average = []

        for j in self.slice_range:
            if self.parent.current_iteration == 0:
                files_to_average.append(self.parent.f['raw_slices'](idx=j))
            else:
                files_to_average.append(self.f['src_slice'](idx=j))

        command = pos_wrappers.ants_average_images(\
                    dimension = self.options.antsDimension,
                    normalize = int(True),
                    input_images = files_to_average,
                    output_image = self.f['processed']())
        commands.append(copy.deepcopy(command))
        self.execute(commands)

    def _get_default_reg_settings(self):
        """
        Fetch the default registration settings (those which were provided from
        command line).
        """
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

            r_metric, parameter, iterations, affine_iterations, \
            transf_grad, reg_type, reg_ammount =\
                    self._get_default_reg_settings()

            metric = pos_wrappers.ants_intensity_meric(
                        fixed_image  = self.f['processed'](),
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
                        rigidAffine = None,
                        imageMetrics = metrics,
                        histogramMatching = " ",
                        miOption = [32, 16000],
                        allMetricsConverge = None)
            commands.append(copy.deepcopy(registration))

        self.execute(commands)

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

    def _reslice_images_forward(self):
        """
        Reslice the source (initial) images towards the current template using
        transformation calculated in corrent iteration.  This method executes
        the following code::

           bash
                /opt/ANTs-1.9.x-Linux/bin/WarpImageMultiTransform 2
                test0004.nii.gz
                test0004deformed.nii.gz
                test0004Warp.nii.gz
                test0004Affine.txt -R
                testtemplate.nii.gz
        """
        # Gather all the commands to be executed in a single array
        commands = []

        for i in self.slice_range:
            command = pos_wrappers.ants_reslice(
                    dimension = self.options.antsDimension,
                    moving_image = self.f['src_slice'](idx=i),
                    output_image = self.f['resliced'](idx=i),
                    reference_image = self.f['processed'](),
                    deformable_list = [self.f['forward'](idx=i)],
                    affine_list = [self.f['affine'](idx=i)])
            commands.append(copy.deepcopy(command))

        # And then execute all the scheduled commands.
        self.execute(commands)

    def _update_template_shape(self):
        """
        Update average template by averaging individual warped images::

          bash
              AverageImages 2 testtemplate.nii.gz 1
              0000deformed.nii.gz 0001deformed.nii.gz
              0002deformed.nii.gz 0003deformed.nii.gz
              0004deformed.nii.gz

        .. note:: The command uses normalization feature of the `AverageImages`
            tool which does some sharpening (see the source of the `AverageImages`)
            which sometimes leads to stragne effects. The uses should be able to
            trun it off on demand (perhaps one day...)
        """

        resliced_images = [self.f['resliced'](idx=i)
                           for i in self.slice_range]

        command = pos_wrappers.ants_average_images( \
                            dimension = self.options.antsDimension,
                            normalize = int(True),
                            input_images = resliced_images,
                            output_image = self.f['resliced_average']())
        self.execute(copy.deepcopy(command))

    def _average_forward_warps(self):
        """
        Averages all forward warps, equivalent of::

            bash AverageImages 2 testtemplatewarp.nii.gz 0
                0000Warp.nii.gz 0001Warp.nii.gz 0002Warp.nii.gz
                0003Warp.nii.gz 0004Warp.nii.gz

        .. note:: This time the normalization is forced to be `0`. We don't want
                to sharpen the deformation fields.
        """
        forward_warps = [self.f['forward'](idx=i)
                         for i in self.slice_range]

        command = pos_wrappers.ants_average_images( \
                        dimension = self.options.antsDimension,
                        normalize = int(False),
                        input_images = forward_warps,
                        output_image = self.f['forward_average']())
        self.execute(copy.deepcopy(command))

    def _update_average_fwd_wrap(self):
        """
        Updates the mean deformation fileld. Equivalent of following series of commands
        Averages all forward warps, equivalent of::

            MultiplyImages 2 templatewarp.nii.gz -0.25 templatewarp.nii.gz
            AverageAffineTransform 2
                templateAffine.txt
                0000Affine.txt 0001Affine.txt 0002Affine.txt 0003Affine.txt 0004Affine.txt
            WarpImageMultiTransform 2
                templatewarp.nii.gz
                templatewarp.nii.gz
                -i templateAffine.txt
                -R template.nii.gz
                templatewarp.nii.gz templatewarp.nii.gz
                templatewarp.nii.gz templatewarp.nii.gz
        """
        command = ants_multiply_images( \
                        dimension = self.options.antsDimension,
                        multiplier = -0.25,
                        output_image = self.f['forward_average'](),
                        input_image  = self.f['forward_average']())
        self.execute(copy.deepcopy(command))

        # Averaging affine transforms:
        forward_affines = [self.f['affine'](idx=i)
                           for i in self.slice_range]

        command = pos_wrappers.ants_average_affine_transform( \
                        dimension = self.options.antsDimension,
                        affine_list = forward_affines,
                        output_affine_transform = self.f['affine_average']())
        self.execute(copy.deepcopy(command))

        # Transforming the average warp using only affine transforms.
        # The warp filed is stacked four times as it was multiplied by 0.25
        # in the previous step, so, overall it would be 1.0 again.
        inverse_affine = ["-i " + self.f['affine_average']()]
        average_warp = self.f['forward_average']()

        command = pos_wrappers.ants_reslice(
            dimension = self.options.antsDimension,
            moving_image = average_warp,
            reference_image = average_warp,
            deformable_list = inverse_affine + 4*[average_warp],
            affine_list = [],
            output_image = average_warp)
        self.execute(copy.deepcopy(command))

    def _update_average_inverse_wrap(self):
        """
        Update the '''INVERSE''' warps::

            AverageImages 2 templateInverseWarp.nii.gz 0
                0000InverseWarp.nii.gz 0001InverseWarp.nii.gz 0002InverseWarp.nii.gz
                0003InverseWarp.nii.gz 0004InverseWarp.nii.gz
            WarpImageMultiTransform 2
                templateInverseWarp.nii.gz
                -R templateInverseWarp.nii.gz
                templateAffine.txt
        """
        # Averaging inverse deformation fields:
        inverse_warps = [self.f['inverse'](idx=i)
                         for i in self.slice_range]

        command = pos_wrappers.ants_average_images( \
                        dimension = self.options.antsDimension,
                        normalize = int(False),
                        input_images = inverse_warps,
                        output_image = self.f['inverse_average']())
        self.execute(copy.deepcopy(command))

        # Shifting the average inverse warp field with the affine transform
        #XXX: There is a bug somewhere here...
        # I guess there should not be average_inverse_warp in deformable_list
        # for warping
        average_inverse_warp = self.f['inverse_average']()
        affine_transform = self.f['affine_average']()

        command = pos_wrappers.ants_reslice(
            dimension = self.options.antsDimension,
            moving_image = average_inverse_warp,
            output_image = average_inverse_warp,
            reference_image = average_inverse_warp,
            deformable_list = [affine_transform],
            affine_list = [])
        self.execute(copy.deepcopy(command))

    def _update_warp_variance(self):
        """
        Update the variance map (the only one, global variance map).

        msq_i = average_inverse * forward_i
        sddm = sqrt ((1/n-1)* sum_i(msq_i) )
        """

        # Compose average inverse wrap with the individual forward wrap for
        # each image.
        commands = []
        for i in self.slice_range:
            deformable_list = [
                self.f['inverse_average'](),
                self.f['forward'](idx=i)]

            command = pos_wrappers.ants_compose_multi_transform(
                    dimension = self.options.antsDimension,
                    output_image = self.parent.f['template_transf_f'](idx=i),
                    reference_image = self.f['src_slice'](idx=i),
                    deformable_list = deformable_list,
                    affine_list = [])
            commands.append(copy.deepcopy(command))
        self.execute(commands)

        # Calculate magnitides of the warp vectors for each individual image
        commands = []
        meth ={2:test_msq_2, 3:test_msq_3}

        for i in self.slice_range:
            command = meth[self.options.antsDimension](
                    dimension = self.options.antsDimension,
                    input_image = self.parent.f['template_transf_f'](idx=i),
                    output_image = self.parent.f['template_transf_f_msq'](idx=i))
            commands.append(copy.deepcopy(command))
        self.execute(commands)

        # Now, calculate the variance of the deformation magnitude maps
        # The way, how it is done is a bit clumsy, but pobably the fastest one.
        # c3d command line is generated: i1 i2 -add i3 -add ... in -add
        # -scale 1/(n-1) -sqrt
        deformation_magnitude_maps = \
            [self.parent.f['template_transf_f_msq'](idx=self.slice_range[0])]
        deformation_magnitude_maps += \
            [self.parent.f['template_transf_f_msq'](idx=i) + " -add "
             for i in self.slice_range[1:]]

        sddm_filename = \
                self.parent.f['sddm'](iter=self.parent.current_iteration)

        command = calculate_sddm( \
                    dimension = self.options.antsDimension,
                    output_image = sddm_filename,
                    variance_n = 1.0/(len(self.slice_range) - 1.0),
                    input_images = deformation_magnitude_maps)
        self.execute(copy.deepcopy(command))

    def launch(self):
        """
        """

        if self.parent.current_iteration == 0:
            self._preprocess_images()
        self._calculate_transformations_masked()
        self._reslice()

    def __call__(self, *args, **kwargs):
        return self.launch()

