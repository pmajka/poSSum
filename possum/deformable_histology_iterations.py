#!/usr/bin/python

import sys
import copy
import numpy as np

import pos_wrappers
from pos_wrapper_skel import generic_workflow
import pos_parameters
from pos_deformable_wrappers import blank_slice_deformation_wrapper


class deformable_reconstruction_iteration(generic_workflow):
    _f = {
        'src_slice'  : pos_parameters.filename('src_slice',  work_dir = '00_src_slices',      str_template =  '{idx:04d}.nii.gz'),
        'processed'  : pos_parameters.filename('processed',  work_dir = '01_process_slices',  str_template =  '{idx:04d}.nii.gz'),
        'outline'    : pos_parameters.filename('outline',    work_dir = '02_outline',         str_template =  '{idx:04d}.nii.gz'),
        'poutline'   : pos_parameters.filename('poutline',   work_dir = '03_poutline',        str_template =  '{idx:04d}.nii.gz'),
        'cmask'      : pos_parameters.filename('cmask',      work_dir = '04_cmask',           str_template =  '{idx:04d}.nii.gz'),
        'pcmask'     : pos_parameters.filename('pcmask',     work_dir = '05_pcmask',          str_template =  '{idx:04d}.nii.gz'),
        'transform'  : pos_parameters.filename('transform',  work_dir = '11_transformations', str_template =  '{idx:04d}Warp.nii.gz'),
        'out_naming' : pos_parameters.filename('out_naming', work_dir = '11_transformations', str_template = '{idx:04d}'),
        'resliced'   : pos_parameters.filename('resliced',   work_dir = '21_resliced',        str_template = '{idx:04d}.nii.gz'),
        'resliced_outline' : pos_parameters.filename('resliced_outline', work_dir='22_resliced_outline', str_template='{idx:04d}.nii.gz'),
        'resliced_custom' : pos_parameters.filename('resliced_custom', work_dir='24_resliced_custom', str_template='{idx:04d}.nii.gz')
        }

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

        start, end, eps = self._get_edges()
        self.slice_range = range(start, end + 1)

        # Convert the number of iterations string to list of integers
        self.options.antsIterations = \
            map(int, self.options.antsIterations.strip().split("x"))

        # Load data for outlier removal rutines
        self._load_subset_file()
        self._read_custom_registration_assignment()

    def _read_custom_registration_assignment(self):
        """
        Helper method for correcting outlier slices.
        """

        # If custom mask is provided and its weight is more than zero, it means
        # that 'outlier removal mechanism' should be used. This mechanism
        # corrects only a part of the slices indicated by masks to the slices
        # which are enumerated in self.options.maskedVolumeFile.
        if self.options.maskedVolume and \
                self.options.maskedVolumeWeight > 0 and \
                self.options.maskedVolumeFile:

            self.masked_registraion = \
                self._get_outliers_registration_assignment(
                    self.options.maskedVolumeFile)
            self.subset = self.masked_registraion.keys()
        else:
            self.masked_registraion = {}

    def _get_outliers_registration_assignment(self, filename, delimiter=" "):
        """
        :param filename: filename to read the outliers assignment from
        :type filename: str

        :param delimiter: field delimiter
        :type delimiter: str

        :returns: Settings for the coregistration of the given moving section.
        :rtype: dict

        Reads file containing the correction parameters for the outliers
        slices. The registration parameters are used to correct individual
        images, instead of correcting whole series of sections. The parameters
        are required to be passed via CSV file. Depending on the amount of
        parameters in a single line one of two workflows is used.

        The parameters may be passed twofolds.

        1. If a row contains two values, they are interpreted as: (1) moving
        file index and (2) fixed file index. This means the the outlier
        correction process will rely on warping moving image to the fixed
        images. The registration process will be driven according to the
        parameters passed via the command line thus all images will be
        registared using the same set of parameters.

        2. If a row contains nine fields they are interpreted in the following way:
            1. Moving image index,
            2. Fixed image index,
            3. Image similarity metric,
            4. Image similarity metric parameter,
            5. Registration iterations,
            6. Gradient step for SyN transformation,
            7. Regularization type,
            8. Ammount of regularization.

        Unlike in the former scheme, In the latter approach each pair of
        sections may be coregistered using different setting.
        """

        returnDictionary = {}
        columns = {'fixed': 1, 'moving': 0, 'metric': 2, 'met_opt': 3,
                   'iters': 4, 'trval': 5, 'regtype': 6, 'regam': 7}

        for sourceLine in open(filename):
            if sourceLine.strip().startswith('#') or sourceLine.strip() == "":
                continue
            line = sourceLine.split("#")[0].strip().split(delimiter)
            key = int(line[columns['moving']])

            # There are two options possible, either
            # 1) There is only moving_image => fixed image assignment
            # 2) There are full registration settings provided for
            #    each of the entries
            # The two options can be mixed within single assignment file

            # Check, if there is only one assignment per file

            if key in returnDictionary:
                print >>sys.stderr, \
                    "Entry %s defined more than once. Skipping..." % key
                continue

            if len(line) > 2:
                value = {}
                value['moving'] = key
                value['fixed'] = int(line[columns['fixed']])
                value['metric'] = line[columns['metric']]
                value['met_opt'] = float(line[columns['met_opt']])
                value['iters'] = map(int, line[columns['iters']].split("x"))
                value['trval'] = float(line[columns['trval']])
                value['regtype'] = line[columns['regtype']]
                value['regam'] = map(float, line[columns['regam']].split(","))

            elif len(line) == 2:
                value = {}
                value['moving'] = key
                value['fixed'] = int(line[columns['fixed']])
                value['metric'] = self.options.antsImageMetric
                value['met_opt'] = self.options.antsImageMetricOpt
                value['iters'] = self.options.antsIterations
                value['trval'] = self.options.antsTransformation
                value['regtype'] = self.options.antsRegularizationType
                value['regam'] = self.options.antsRegularization

            returnDictionary[key] = value

        return returnDictionary

    def _get_edges(self):
        """
        Convenience function for returning frequently used numbers

        :returns: Returns the first and the last slice index of the
        reconstruction process as well as epsilon.
        :rtype: tuple
        """

        return (self.options.startSlice,
                self.options.endSlice,
                self.options.neighbourhood)

    def _load_subset_file(self):
        """
        Loads a subset of slices from a given file.  When the additional file
        is provided, only slices with indices from the file will be registered.
        """

        if self.options.registerSubset:
            subset = np.loadtxt(self.options.registerSubset)
            self.subset = list(subset)
        else:
            self.subset = self.slice_range

    def _assign_weights_from_func(self):
        """
        Assing weights for image averaging. Currently just constants weights
        are assigned and that seems to be quite a good solution.
        """
        start, end, eps = self._get_edges()

        self.weights = {}
        for i in self.slice_range:
            for j in range(i - eps, i + eps + 1):
                if j != i and j <= end and j >= start:
                    self.weights[(i, j)] = 1

    def _assign_weights(self):
        self._assign_weights_from_func()

    def get_weight(self, i, j):
        return self.weights[(i, j)]

    def _preprocess_images(self):
        return self._average_images()

    def _average_images(self):
        start, end, eps = self._get_edges()

        if self.options.inputVolume and self.options.inputVolumeWeight > 0:
            commands = []

            for i in self.slice_range:
                files_to_average = []
                weights = []

                for j in range(i - eps, i + eps + 1):
                    if j != i and j <= end and j >= start:
                        files_to_average.append(self.f['src_slice'](idx=j))
                        weights.append(self.get_weight(i, j))

                command = pos_wrappers.images_weighted_average(
                    dimension=2,
                    input_images=files_to_average,
                    weights=weights,
                    output_type='float',
                    output_image=self.f['processed'](idx=i))
                commands.append(copy.deepcopy(command))

            self.execute(commands)

        if self.options.outlineVolume and self.options.outlineVolumeWeight > 0:
            commands = []

            for i in self.slice_range:
                files_to_average = []
                weights = []

                for j in range(i - eps, i + eps + 1):
                    if j != i and j <= end and j >= start:
                        files_to_average.append(self.f['outline'](idx=j))
                        weights.append(self.get_weight(i, j))

                command = pos_wrappers.images_weighted_average(
                    dimension=2,
                    input_images=files_to_average,
                    weights=weights,
                    output_type='float',
                    output_image=self.f['poutline'](idx=i))
                commands.append(copy.deepcopy(command))

            self.execute(commands)

    def _get_default_reg_settings(self):
        return (self.options.antsImageMetric,
                self.options.antsImageMetricOpt,
                self.options.antsIterations,
                self.options.antsTransformation,
                self.options.antsRegularizationType,
                self.options.antsRegularization)

    def _get_custom_reg_settings(self, mov_slice_idx):
        src = self.masked_registraion[mov_slice_idx]
        return (src['metric'], src['met_opt'], src['iters'],
                src['trval'], src['regtype'], src['regam'])

    def _calculate_transformations_masked(self):
        """
        Generate and invoke commands for generating deformation fields.
        Commands are generated based on a number of factors. The actual
        dependencies what is registered to what and how its quite complicated
        and it is my sweet secret how it is actually calculated.
        """

        start, end, eps = self._get_edges()

        commands = []

        for i in self.slice_range:
            metrics  = []
            j_data = self.masked_registraion.get(i, None)

            if j_data == None:
                fixed_image_type = 'processed'
                fixed_outline_type='poutline'
                mask_image = None
                j=i
                r_metric, parameter, iterations, transf_grad, reg_type, reg_ammount =\
                        self._get_default_reg_settings()

            else:
                fixed_image_type = 'src_slice'
                fixed_outline_type = 'outline'
                j = j_data['fixed']
                mask_image = self.f['cmask'](idx=j)
                r_metric, parameter, iterations, transf_grad, reg_type, reg_ammount =\
                    self._get_custom_reg_settings(i)

            if self.options.inputVolume and self.options.inputVolumeWeight > 0:
                metric = pos_wrappers.ants_intensity_meric(
                    fixed_image=self.f[fixed_image_type](idx=j),
                    moving_image=self.f['src_slice'](idx=i),
                    metric=r_metric,
                    weight=self.options.inputVolumeWeight,
                    parameter=parameter)
                metrics.append(copy.deepcopy(metric))

            if self.options.outlineVolume and self.options.outlineVolumeWeight > 0:
                outline_metric = pos_wrappers.ants_intensity_meric(
                    fixed_image=self.f[fixed_outline_type](idx=j),
                    moving_image=self.f['outline'](idx=i),
                    metric=r_metric,
                    weight=self.options.outlineVolumeWeight,
                    parameter=parameter)
                metrics.append(copy.deepcopy(outline_metric))

            if self.options.referenceVolume and self.options.referenceVolumeWeight > 0:
                reference_metric = pos_wrappers.ants_intensity_meric(
                    fixed_image=self.parent_process.f['ref_custom'](idx=j),
                    moving_image=self.f['src_slice'](idx=i),
                    metric=r_metric,
                    weight=self.options.referenceVolumeWeight,
                    parameter=parameter)
                metrics.append(copy.deepcopy(reference_metric))

            if i in self.subset:
                registration = pos_wrappers.ants_registration(
                    dimension=2,
                    outputNaming=self.f['out_naming'](idx=i),
                    iterations=iterations,
                    transformation=('SyN', [transf_grad]),
                    regularization=(reg_type, reg_ammount),
                    affineIterations=[0],
                    continueAffine=False,
                    rigidAffine=False,
                    imageMetrics=metrics,
                    maskImage=mask_image,
                    allMetricsConverge=True)
            else:
                registration = blank_slice_deformation_wrapper(
                    input_image=self.f['src_slice'](idx=i),
                    output_image=self.f['transform'](idx=i))
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

        self._assign_weights()
        self._preprocess_images()
        self._calculate_transformations_masked()

    def __call__(self, *args, **kwargs):
        return self.launch()
