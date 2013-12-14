#!/usr/bin/python
# -*- coding: utf-8 -*
###############################################################################
#                                                                             #
#    This file is part of Multimodal Atlas of Monodelphis Domestica           #
#                                                                             #
#    Copyright (C) 2011-2012 Piotr Majka                                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is free software: you can redistribute      #
#    it and/or modify it under the terms of the GNU General Public License    #
#    as published by the Free Software Foundation, either version 3 of        #
#    the License, or (at your option) any later version.                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is distributed in the hope that it          #
#    will be useful, but WITHOUT ANY WARRANTY; without even the implied       #
#    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.         #
#    See the GNU General Public License for more details.                     #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along  with  3d  Brain  Atlas  Reconstructor.   If  not,  see            #
#    http://www.gnu.org/licenses/.                                            #
#                                                                             #
###############################################################################

import os, sys
import copy
from optparse import OptionParser, OptionGroup
import pos_parameters
from pos_wrapper_skel import output_volume_workflow
from pos_wrappers import generic_wrapper

import numpy
from scipy.ndimage.filters import gaussian_filter1d

class coarse_to_fine_transformation_merger_plot(generic_wrapper):
    """
    #TODO: Implement some axis configuration, etc.
    """

    _template = """#!/usr/bin/gnuplot -persist
        set macros

        set terminal pngcairo enhanced color notransparent size 800,600  font 'Verdana,8'
        set output '{graph_image}'

        POS = "at graph 0.5,0.95 font ',8' center"

        NOXTICS = "set xtics; unset xlabel; set format x '';"
        XTICS   = "set xtics; set xlabel 'Slice index' font ',8'; set format x '%%g';"

        NOYTICS = "set format y ''; unset ylabel"
        YTICS = "set format y '%%g'; set ylabel ''"

        TMARGIN = "set tmargin at screen 0.90; set bmargin at screen 0.55"
        BMARGIN = "set tmargin at screen 0.50; set bmargin at screen 0.15"
        LMARGIN = "set lmargin at screen 0.10; set rmargin at screen 0.50"
        RMARGIN = "set lmargin at screen 0.55; set rmargin at screen 0.95"

        FN_SMOOTH = "'{smooth_transformations}'"
        FN_RAW = "'{fine_transformations}'"
        FN_DIFF = "'{transformation_difference}'"

        set style line 1 lc rgb '#031A49' lt 1 lw 1 # --- blue
        set style line 2 lc rgb '#1D4599' lt 1 lw 1 # --- lblue
        set style line 3 lc rgb '#025214' lt 1 lw 1 # --- blue
        set style line 4 lc rgb '#11AD34' lt 1 lw 1 # --- red
        set style line 5 lc rgb '#E62B17' lt 1 lw 1 # --- blue
        set style line 6 lc rgb '#6D0D03' lt 1 lw 1 # --- red
        set style line 7 lc rgb '#E69F17' lt 1 lw 1 # --- blue
        set style line 8 lc rgb '#6D4903' lt 1 lw 1 # --- red

        STYLE_RAW_1    = "w l ls 1 notitle"
        STYLE_SMOOTH_1 = "w l ls 2 notitle"
        STYLE_RAW_2    = "w l ls 3 notitle"
        STYLE_SMOOTH_2 = "w l ls 4 notitle"
        STYLE_RAW_3    = "w l ls 5 notitle"
        STYLE_SMOOTH_3 = "w l ls 6 notitle"
        STYLE_RAW_4    = "w l ls 7 notitle"
        STYLE_SMOOTH_4 = "w l ls 8 notitle"

        set multiplot layout 2,2 rowsfirst title "Fine - coarse : {graph_image}"

        set label 1 'Offset (translation) [pixels]' @POS
        @NOXTICS; @YTICS
        @TMARGIN; @LMARGIN
        plot @FN_RAW  u 0:5 @STYLE_RAW_1, @FN_SMOOTH u 0:5 @STYLE_SMOOTH_1 , \
            @FN_RAW  u 0:6 @STYLE_RAW_2, @FN_SMOOTH u 0:6 @STYLE_SMOOTH_2

        set label 1 'Horizontal and vertical scaling' @POS
        @NOXTICS; @YTICS
        @TMARGIN; @RMARGIN
        set yrange [0.95:1.05]
        plot @FN_RAW u 0:1 @STYLE_RAW_3, @FN_SMOOTH u 0:1 @STYLE_SMOOTH_3 , \
            @FN_RAW u 0:4 @STYLE_RAW_4, @FN_SMOOTH u 0:4 @STYLE_SMOOTH_4

        set label 1 'Slice rotation [degrees]' @POS
        @XTICS; @YTICS
        @BMARGIN; @LMARGIN
        set nokey
        set yrange [-20:20]
        plot @FN_RAW  u 0:(90-acos($2)*180./pi) @STYLE_RAW_3, @FN_SMOOTH u 0:(90-acos($2)*180./pi) @STYLE_SMOOTH_3

        set label 1 'Fixed parameters [pixels]' @POS
        @XTICS; @YTICS
        @BMARGIN; @RMARGIN
        set auto y
        plot @FN_RAW  u 0:7 @STYLE_RAW_3, @FN_SMOOTH u 0:7 @STYLE_SMOOTH_3 , \
            @FN_RAW  u 0:8 @STYLE_RAW_4, @FN_SMOOTH u 0:8 @STYLE_SMOOTH_4

        unset multiplot
        """

    _parameters = {
        'graph_image' : pos_parameters.filename_parameter('graph_image', None),
        'smooth_transformations' : pos_parameters.filename_parameter('smooth_transformations', None),
        'fine_transformations' : pos_parameters.filename_parameter('fine_transformations', None),
        'transformation_difference' : pos_parameters.filename_parameter('transformation_difference', None)
    }


class gnuplot_execution_wrapper(generic_wrapper):
    """
    Executes the gnuplot ploting file.
    """

    _template = """gnuplot {plot_filename}; rm -fv {plot_filename};"""

    _parameters = {
        'plot_filename' : pos_parameters.filename_parameter('plot_filename', None),
    }


class invert_affine_transform(generic_wrapper):
    """
    A very simple wrapper of the `ComposeMultiTransform` binary file from the
    ANTS package. The purpose of this wrapper is to simply invert given affine
    (or, in this very case a rigid) transformation.
    """
    _template = """ComposeMultiTransform {dimension} \
                  {output_image} \
                  -i {input_filename}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'input_filename': pos_parameters.filename_parameter('input_filename', None, str_template='-i {_value}'),
    }


class coarse_to_fine_transformation_merger(output_volume_workflow):
    """
    Coarse to fine transformation merger.
    Obligatory command line parameters:

        1. self.options.sliceIndex
        2. fineTransformFilenameTemplate
        3. outputTransformFilenameTemplate
    """

    _f = {
        'fine_transf' : pos_parameters.filename('fine_transf', work_dir = '01_fine_transformation', str_template = '{idx:04d}.txt'),
        'smooth_transf' : pos_parameters.filename('smooth_transf', work_dir = '03_smooth_transformation', str_template = '{idx:04d}.txt'),
        'final_transf' : pos_parameters.filename('final_transf', work_dir = '04_final_transformation', str_template = '{idx:04d}.txt'),

        'fine_report' : pos_parameters.filename('fine_report', work_dir = '05_reports', str_template='fine_transformations.csv'),
        'smooth_report' : pos_parameters.filename('smooth_report', work_dir = '05_reports', str_template='smooth_transformations.csv'),
        'difference_report' : pos_parameters.filename('difference_report', work_dir = '05_reports', str_template='difference_trasnformations.csv'),
        'final_report' : pos_parameters.filename('final_report', work_dir = '05_reports', str_template='final_transformations.csv'),
        'graph' : pos_parameters.filename('graph', work_dir = '05_reports', str_template='graph_{desc:s}.png'),
        'graph_source' : pos_parameters.filename('graph_source', work_dir = '05_reports', str_template='graph_source.plt'),
         }

    def _initializeOptions(self):
        super(self.__class__, self)._initializeOptions()

        # Assert if both: starting slice index and the last slice index
        # are actually provided.
        assert self.options.sliceIndex is not None,\
            self._logger.error("Starting and ending slices indexes are not provided. Please supply the starting and ending slice index.")

        # Range of images to register. This is pretty self explaining.
        self.options.slice_range = \
                range(self.options.sliceIndex[0], self.options.sliceIndex[1] + 1)

        # Define default smoothing kernels for different type of parameters:
        fields_array = ['smoothingSimgaRotation', 'smoothingSimgaOffset', \
                        'smoothingSimgaScaling', 'smoothingSimgaFixed']

        # This is a bit more complicated. Iterate over the parameters regarding
        # the custom parameters' set. If given custom parameter is not defined,
        # use the generic parameter instead.
        for field in fields_array:
            if getattr(self.options, field) == None:
                setattr(self.options, field, self.options.smoothingSimga)

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # Assert if the proper transformation naming schemes are provided:
        assert self.options.coarseTransformFilenameTemplateis is not None,\
            self._logger.error("Coarse transformation filename scheme is an obligatory parameter.")

        assert self.options.fineTransformFilenameTemplateis is not None,\
            self._logger.error("Fine transformation filename naming scheme is an obligatory parameter.")

        assert self.options.outputTransformationsFilenameTemplate is not None,\
            self._logger.error("Please provide an output transformation filename scheme.")

        assert self.options.smoothTransformFilenameTemplate is not None,\
            self._logger.error("Please provide a smoothed transformation filename scheme.")

        # Latch the provided naming schemes.
        self.f['fine_transf'].override_path = \
            self.options.fineTransformFilenameTemplate
        self.f['final_transf'].override_path = \
            self.options.outputTransformFilenameTemplate
        self.f['smooth_transf'].override_path = \
            self.options.smoothTransformFilenameTemplate

        filenames_to_check = map(lambda x: self.f['fine_transf'](idx=x),
            self.options.slice_range)

        for transf_filename in filenames_to_check:
            self._logger.debug("Checking for image: %s.", transf_filename)

            if not os.path.isfile(transf_filename):
                self._logger.error("File does not exist: %s. Exiting",
                    transf_filename)
                sys.exit(1)

        # Oh, an the last but not least. One can assign a custom reports
        # directory (for whatever reason :). If that's the case
        if self.options.reportsDirectory != None:
            self.f['final_report'].override_dir = self.options.reportsDirectory
            self.f['graph'].override_dir = self.options.reportsDirectory
            self.f['graph_source'].override_dir = self.options.reportsDirectory

    def _launch(self):
        # At the very beginning we read all the provided fine transformations
        self._extract_transformation_parameters()

        # The parameters of the transformation are then smoothed to filter out
        # the low frequency component of the transformation parameters.
        self._calculate_smoothed_transforms()

        # Sometimes it is required to turn off calculation of the
        # transformations
        if self.options.skipTransformsGeneration == False:
            self._store_smoothed_transformations()
            self._generate_final_transformations()

        # At the end of the calculations, simple report graph is generated.
        self._generate_report()

    def _extract_transformation_parameters(self):
        """
        Iterate over all supplied parameters, collect the transformation
        parameters and finally create numpy array containing all the extracted
        parameters.
        """
        # An array holding parameters of the transformations befoer they're
        # actually converted to numpy array.
        transformation_parameters = []

        # Interate over all slices, extract parameters of the trasnformation.
        for slice_index in self.options.slice_range:
            transformation_parameters.append(
                self._set_single_transformation_parameters(slice_index))

        # After collecting parameters of the all transformations convert the
        # parameters into numpy arrays before conducting any futher
        # calculations
        self._parameters_array = numpy.array(transformation_parameters).T

        # So basically we end up with all the transformation parameters
        # extracted from the series of fine transformations.

    def _set_single_transformation_parameters(self, slice_index):
        """
        Load a given transformation file and extract and return tranasformation
        parameters.

        :param slice_index: the slice index
        :type slice_index: int

        :return: list of the parameters extracted from the transformation
                 files.
        :rtype: list
        """

        # Simple as it goes: define the name of the transformation file,
        # grab the file's content and extract the transformation parameters
        # from the file's content.
        transformation_filename = self.f['fine_transf'](idx=slice_index)
        transformation_string = open(transformation_filename).readlines()
        transformation_parameters =\
            self._extract_transformation_parameters(transformation_string)

        return transformation_parameters

    def _extract_transformation_parameters(self, transformation_string):
        """
        This function assumes that itk rigid transformation file has a proper
        structure.

        :param transformation_string: string to extract parameters from
        :type transformation_string: str

        :return: list of the transformation parameters extracted from the
                 transformation string.
        :rtype: list
        """

        # Check if the string really contains a itk transformation:
        # To prove that the file contains an actual itk rigid transformation
        # we simply check if the first two lines contains "Transform" and
        # "Parameters" strings, respectively. While this is not bullet-proof
        # it allows to point out some simple mistakes.
        if not transformation_string[2].strip().split(':')[0] == 'Transform':
            transformation_string_validation_flag = False

        if not transformation_string[3].strip().split(':')[0] == 'Parameters':
            transformation_string_validation_flag = False

        # Assert if the transformation_string_validation_flag is True
        assert transformation_string_validation_flag,\
         "One of the supplied transformation files is corrupted or it is not a valid transformation file."

        # Extract the transformation parameters (first line)
        # and then the fixed parameters of the transformation (the bottom line)
        parameters_string = \
            transformation_string[3].strip().split(':')[1].strip().split(' ')
        fixed = \
            transformation_string[4].strip().split(':')[1].strip().split(' ')

        # as the extracted parameters are in fact strings, convert them to
        # floats ...
        transformation_parameters =  map(float, parameters_string)
        fixed_parameters = map(float, fixed)

        # ... and finally join them into a single list
        all_parameters = transformation_parameters + fixed_parameters

        return all_parameters

    def _calculate_smoothed_transforms(self):
        """
        Extracts the low frequency component of the transformation and
        calculates the difference between the initial transformation and the
        low frequency component of the initial transformation. Bla bla...
        """

        # Just create a few aliases. They are so short that actually I think
        # they are even too short :)
        k = self._parameters_array
        l = k.copy()

        # Save initial transformation parameters before processing :)
        initial_parameters_filename = self.f['fine_report']()
        self._save_parameters_array(k, initial_parameters_filename)

        # Smooth the initial transformation. There are three types of
        # parameters, each of them may recieve different ammount of smoothing
        # if required.  The parameter types are: scaling (no unit), offset and
        # fixed parametes (physical units) and translation (no unit). By
        # default all types of parameters are smoothed with the same kernel.
        # Using command line parameters one can customize this behaviour.
        parameters_index = \
            {'fixed'    : ([6,7], self.options['smoothingSimgaFixed']), \
             'offset'   : ([4,5], self.options['smoothingSimgaOffset']), \
             'rotation' : ([1,2], self.options['smoothingSimgaRotation']), \
             'scaling'  : ([0,3], self.options['smoothingSimgaScaling'])}

        # Apply smoothing for each of the parameters. Each kind of parameters
        # is smoothed with a amount of smoothing which depends on the king of
        # the parameter :)
        for index, sigma in parameters_index.values():
            for i in index:
                l[i, :]=gaussian_filter1d(k[i], sigma)[0 : k.shape[1]]

        # Save smoothed parameters array:
        smoothed_parameters_array_filename = self.f['smooth_report']()
        self._save_parameters_array(l, smoothed_parameters_array_filename)

        # And save the smoothed paramters array as we we need to actually
        # use the parameters in some further cfomputations within this
        # workflow.
        self._smoothed_parameters = l

        # Store difference of two sets of transformations as well:
        diff_parameters_array_filename = self.f['difference_report']()
        self._save_parameters_array(k-l, diff_parameters_array_filename)

    def _save_parameters_array(self, parameters_array, filename):
        """
        Stores the given transformation parameters array as text file. Really,
        no big deal here.

        :param parameters_array: parameters array to store
        :type parameters_array: np.array

        :param filename: filename to store the array in
        :type filename: str
        """
        numpy.savetxt(filename, parameters_array.T)

    def _store_smoothed_transformations(self):
        """
        Saves the smoothed transformation parameters as a itk transformation
        files.
        """
        # Just an alias:
        l = self._smoothed_parameters

        # Iterate over the smoothed transformation parameters, exctract the
        # parameters and save them as an itk transformation file.
        for i in range(l.shape[1]):
            slice_index = i + self.options.slice_range[0]
            output_filename = self.f['final_transf'](idx=slice_index)
            self._save_itk_transform(list(l[:,i]), output_filename)

    def _save_itk_transform(self,  parameters, filename):
        """
        Creates and saves the itk rigid transformation based on the provided
        parameters.

        :param parameters: itk rigid transformation parameters
        :type parameters: np.array

        :param filename: filename to store the parameters in
        :type filename: str
        """
        # Just make an alias.
        p = parameters

        # And then form the transformation string. After saving the
        # transformation string just save it into the file. Easy.
        tstr =""
        tstr += "#Insight Transform File V1.0\n"
        tstr += "#Transform 0\n"
        tstr += "Transform: MatrixOffsetTransformBase_double_2_2\n"
        tstr += "Parameters: %f %f %f %f %f %f\n" % (p[0], p[1], p[2], p[3], p[4], p[5])
        tstr += "FixedParameters: %f %f\n" % (p[6], p[7])
        open(filename, 'w').write(tstr)

    def _save_identity_itk_transformation(self, filename):
        """
        Saves the two dimensional itk identity transformation under the
        provided filename.

        :param filename: filename to store the transformation into
        :type filename: str
        """

        # Define the identiry transformation parametres (which are very simple)
        identity_transformation_parameters = \
            [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]

        # And the execute the regular `_save_itk_transform` function
        self._save_itk_transform(identity_transformation_parameters, filename)

    def _generate_final_transformations(self):
        """
        Iterate over all transformations and compute the inversion of the
        transformation.  The inversion of the smoothed fine transformation is
        called the "final" transformation.
        """

        commands = []
        for slice_index in self.options.slice_range:
            commands.append(self._store_final_transformation(slice_index))
        self.execute(commands)

    def _store_final_transformation(self, slice_index):
        """
        :param slice_index: index of the slice to save final
                            transformation for.
        :type slice_index: int

        :return: invert affine transformation commad wrapper.
        :rtype: `invert_affine_transform`
        """
        input_transformation = self.f['smooth_transf'](idx=slice_index)
        output_transformation =  self.f['final_transf'](idx=slice_index)

        command = invert_affine_transform(
            output_image = output_transformation,
            input_filename = input_transformation)
        return copy.deepcopy(command)

    def _generate_report(self):
        """
        Create a plot comparing the initial, smoothed and filtered affine
        transformation parameters. Pretty simple procedure :)
        """
        # The name of the graph will be based on the merging parameters
        # passed using the command line parameters. So:
        # grap the file prefix.
        prefix = self._get_parameters_based_filename_prefix()

        # Define the gnuplot plotting file using the approperiate plotting
        # wrapper.
        command = coarse_to_fine_transformation_merger_plot(
            graph_image = self.f['graph'](desc=prefix),
            smooth_transformations = self.f['smooth_report'],
            fine_transformations = self.f['fine_report'],
            transformation_difference = self.f['difference_report'])

        # Save the plot file
        plot_filename = self.f['graph_source']()
        open(plot_filename, 'w').write(str(command))

        # Execute proviouslu generated plot file
        command = gnuplot_execution_wrapper(
            plot_filename = plot_filename)
        self.execute(command)

    def _get_parameters_based_filename_prefix(self):
        """
        Generate output naming prefix. The parameters based filename prefix
        helps to easier identify given results among multiple attempts
        performed with different parameters.
        """
        ret_value = ""

        ret_value+= "_start_" + str(self.options.slice_range[0])
        ret_value+= "_end_"   + str(self.options.slice_range[-1])

        ret_value+= "_s_" + str(self.options.smoothingSimga)
        ret_value+= "_sR_" + str(self.options.smoothingSimgaRotation)
        ret_value+= "_sO_" + str(self.options.smoothingSimgaOffset)
        ret_value+= "_sS_" + str(self.options.smoothingSimgaScaling)
        ret_value+= "_sF_" + str(self.options.smoothingSimgaFixed)

        return ret_value

    @classmethod
    def _getCommandLineParser(cls):
        """
        TODO: Reorganize the command line options into sensible groups.
        """
        parser = output_volume_workflow._getCommandLineParser()

        preprocessingSettings = \
                OptionGroup(parser, 'Processing settings')

        preprocessingSettings.add_option('--sliceIndex', default=None,
                type='int', dest='sliceIndex', nargs=2,
                help='first, last slice index')
        preprocessingSettings.add_option('--smoothingSimga', default=5,
                type='float', dest='smoothingSimga',
                help='General smoothing simga. Can be customized for specific parameters.')
        preprocessingSettings.add_option('--smoothingSimgaRotation', default=None,
                type='float', dest='smoothingSimgaRotation', help='')
        preprocessingSettings.add_option('--smoothingSimgaScaling', default=None,
                type='float', dest='smoothingSimgaScaling', help='')
        preprocessingSettings.add_option('--smoothingSimgaOffset', default=None,
                type='float', dest='smoothingSimgaOffset', help='')
        preprocessingSettings.add_option('--smoothingSimgaFixed', default=None,
                type='float', dest='smoothingSimgaFixed', help='')

        workflowSettings = \
                OptionGroup(parser, 'Workflow settings')
        workflowSettings.add_option('--outputTransformFilenameTemplate', default=None,
                dest='outputTransformFilenameTemplate', action='store',
                help='Store transformations in given directory instead of using default one.')
        workflowSettings.add_option('--reportsDirectory', default=None,
                dest='reportsDirectory', action='store',
                help='Use custom reports directory instead of using default one.')
        workflowSettings.add_option('--skipTransformsGeneration', default=False,
                dest='skipTransformsGeneration', action='store_const', const=True,
                help='')
        parser.add_option('--fineTransformFilenameTemplate', default=None,
                dest='fineTransformFilenameTemplate', action='store',
                help='')
        parser.add_option('--smoothTransformFilenameTemplate', default=None,
                dest='smoothTransformFilenameTemplate', action='store',
                help='')

        parser.add_option_group(workflowSettings)
        parser.add_option_group(preprocessingSettings)
        return parser

if __name__ == '__main__':
    options, args = coarse_to_fine_transformation_merger.parseArgs()
    s = coarse_to_fine_transformation_merger(options, args)
    s.launchFilter()
