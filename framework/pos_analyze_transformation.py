#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys
import tempfile
from optparse import OptionParser, OptionGroup

import math
import numpy as np

from pos_wrapper_skel import enclosed_workflow
import pos_wrappers
import pos_parameters

"""
#TODO: documentation and description, usage examples.

Rigid transformation plotting script
************************************

:author: Piotr Majka <pmajka@nencki.gov.pl>
:revision: $Rev$
:date: $LastChangedDate$

`pos_analyze_transformation` -- a script for plotting a series of rigid
transformations.

This file is part of imaging data integration framework,
a private property of Piotr Majka
(c) Piotr Majka 2011-2014. Restricted, damnit!

Syntax
======

.. highlight:: bash

Providing information on slices to process
------------------------------------------

There are two ways of defining the moving slice image. Either 1) it can go from


How to process additional image stacks
--------------------------------------

First of all: additional stack settings are optional while the primary image
stacks are obligatory.
"""


class rigid_transformations_plotter(pos_wrappers.generic_wrapper):
    """
    Defienes the plotting template for the prameters of the series of a rigid
    transformation parameters: namely, the horizontal and the vertical
    translation and the rotation angle.

    This is quite a primitive plot as almost all of the plotting parameters are
    set automatically thus the plot is rather not artistic one.
    """

    _template = """#!/usr/bin/gnuplot -persist
        set terminal pngcairo noenhanced color notransparent size 800,400 font 'Arial,10'
        set output '{graph_image}'

        set title  sprintf("registration results\\n %s", '{calculation_prefix}')
        set xlabel "slide number"
        set ylabel "translation [mm]"
        set y2label "rotation [degrees]"

        set yrange [:]
        set y2range [:]

        set xtics nomirror
        set y2tics auto nomirror
        set ytics auto nomirror

        plot '{transformation_report_file}' u 0:3 w l title 'horizontal translation', \
            '{transformation_report_file}' u 0:2 w l title 'vertical translation', \
            '{transformation_report_file}' u 0:(sqrt($2**2+$3**2)) w l title 'total translation', \
            '{transformation_report_file}' u 0:1 axes x1y2 w l title 'rotation angle'
    """

    _parameters = {
        'graph_image': pos_parameters.filename_parameter('graph_image', None),
        'calculation_prefix': pos_parameters.filename_parameter('calculation_prefix', None),
        'transformation_report_file': pos_parameters.filename_parameter('transformation_report_file', None),
    }

class rigid_transformations_plotter_wapper(pos_wrappers.generic_wrapper):
    """
    #TODO: Provide doctests fore this wrapper.
    """

    _template = """
    pos_analyze_transformation.py \
        {signature} {reportFilename} {plotFilename}
    """

    _parameters = {
        'signature': pos_parameters.string_parameter('signature', None, '--{_name} {_value}'),
        'reportFilename': pos_parameters.filename_parameter('reportFilename', None, '--{_name} {_value}'),
        'plotFilename': pos_parameters.filename_parameter('plotFilename', None, '--{_name} {_value}'),
    }


class transformation_analyzer(enclosed_workflow):
    """
    A script analyzing the affine transformation series produces by the
    sequential alignment script.
    """

    def _validate_options(self):
        super(self.__class__, self)._validate_options()

        # Validate of the ouput plot file is provided.
        assert self.options.plotFilename, \
            self._logger.error("The output plot filename is required. Please provide the output plot filename.")

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # There is not many options to be customized but one's gonna find one
        # or two. The first one is the report file. If the report filename is
        # not provided, the temporary filename will be generated and removed
        # after generating the actual plot.

        self._logger.info("The output report filename is not provided. Generating a tempfile name for the report.")
        if self.options.reportFilename is None:
            self.options.reportFilename = tempfile.mkstemp()[1]
        self._logger.info("The output report filename set to %s"
            % self.options.reportFilename)

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Initialize an array holding the transformation parameters.
        # All the parameters loaded from the transformation series will be
        # loaded here and only then transformed further.
        self._transformation_parameters_list = []

        self._analyze_transformations()
        self._plot_transformation_parameters()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _analyze_transformations(self):
        """
        Analyze single transformation file and extract related information.
        """
        # Iterate trought all transformation file provided as command line
        # arguments and collect the transformation parameters.
        for transformation_file in self.args:
            self._transformation_parameters_list.append(
                self._process_single_transformation(transformation_file))

    def _process_single_transformation(self, transformation_file):
        """
        Extracts paramters from a single itk 2d rigid transform file.

        :param transformation_file: "Insight Transform File V1.0" text
        transformation file carrying the `MatrixOffsetTransformBase_double_2_2`
        transformation. This kind of file is produced, among others, by the
        ANTS package in version 3. For some reason this type of the
        transformmation file is not well describes clearly in the ITK
        specification. Perhaps one day it will be done by someone. For some
        examples of such files please google them out or check some of the
        examples I have found: http://searchcode.com/codesearch/raw/33177477 .

        :type transformation_file: str

        :return: the array of parameters extracted from the transformation
                 file.
        :rtype: list
        """

        # Open the transformation file, read its contents, extract the
        # parameters into array and return the array. Simeple.
        transformation_string = open(transformation_file).readlines()
        transformation_parameters = \
            self._extractParameters(transformation_string)
        return transformation_parameters

    def _extractParameters(self, transformation_string):
        """
        Extracts transformation parameters from the transformation file
        contents nad packs them into an array which is then returned.

        :param transformation_string: the contents of the transformation file.
        :type: transformation_string: string

        :return: An array of the parameters results.
        :rtype: list
        """

        # We assume that the transofmration string is correct, it may turn out
        # later that it is not:
        validation_flag = True

        # Check if the string really contains a itk transformation:
        if not transformation_string[2].strip().split(':')[0] == 'Transform':
            validation_flag = False

        # The second criterion is that the fourth line contains the
        # "Parameters" string.
        if not transformation_string[3].strip().split(':')[0] == 'Parameters':
            validation_flag = False

        # Well, it the transformation if not valid in the formal sense, report
        # that.
        if not validation_flag:
            raise ValueError, "%s contains invalid transformation description." \
                % transformation_string

        # Extract the actual parametres from the parameters string.
        parameters_string = \
            transformation_string[3].strip().split(':')[1].strip().split(' ')

        # Then, convert the string parameters into floats.
        transformationParams = tuple(map(float, parameters_string))
        sx, ra, rb, sy, tx, ty = transformationParams
        phi = 90 - math.degrees(math.acos(rb))

        # Return the rotation angle, translation vector and
        # scaling factors.
        result = {'rotation': phi, 'translation': (tx, ty),
                  'scaling': (sx, sy)}
        return result

    def _plot_transformation_parameters(self):
        """
        Draws a gnuplot chart illustrating changes of the parameters in
        different slices.
        """

        # Generate numpy arrays containing all of the parameters of the
        # transform, namely: translation in both directions and rotation
        translations = np.array(map(lambda x: x['translation'],
                        self._transformation_parameters_list))
        rotations = np.array(map(lambda x: x['rotation'],
                        self._transformation_parameters_list))

        # Define some nice aliases to easily manipulate the data.
        self._translation_x_array = translations[:, 0]
        self._translation_y_array = translations[:, 1]
        self._rotation_array = rotations[:]

        # Prepare a column array for convenient saving the transformation
        # parameters.
        columnsArray = np.column_stack((self._rotation_array,
            self._translation_x_array, self._translation_y_array))

        # Generate filenames for all the files used in this procedure
        report_filename = self.options.reportFilename

        # Save the transformation parameters into the file
        # for further ploting
        np.savetxt(report_filename, columnsArray, delimiter='\t')

        # And then, plot the transformation parameters.
        self._generate_report()

    def _generate_report(self):
        """
        Create a plot comparing the initial, smoothed and filtered affine
        transformation parameters. Pretty simple procedure :)
        """

        # The name of the graph will be based on the merging parameters
        # passed using the command line parameters. So:
        # grap the file prefix.
        prefix = self.options.signature

        # Define the gnuplot plotting file using the approperiate plotting
        # wrapper.
        command = rigid_transformations_plotter(
            graph_image=self.options.plotFilename,
            calculation_prefix=prefix,
            transformation_report_file=self.options.reportFilename)

        # Save the plot file
        (fd, filename) = tempfile.mkstemp()
        os.fdopen(fd, "w").write(str(command))

        # Execute proviouslu generated plot file
        command = pos_wrappers.gnuplot_execution_wrapper(
            plot_filename=filename)
        command()

    @classmethod
    def _getCommandLineParser(cls):
        parser = enclosed_workflow._getCommandLineParser()
        parser.usage = "%s [options] transform_1 transform_2 ..." % \
            os.path.basename(sys.argv[0])

        parser.add_option('--signature', default=None,
            type='str', dest='signature',
            help='[Optional]. A string which will be appended to all of the files outputed by the script.')
        parser.add_option('--reportFilename', default=None,
            type='str', dest='reportFilename',
            help='[Optinal]. A report filename')
        parser.add_option('--plotFilename', default=None,
            type='str', dest='plotFilename',
            help='[Required]. Image filename.')

        return parser


if __name__ == '__main__':
    options, args = transformation_analyzer.parseArgs()
    d = transformation_analyzer(options, args)
    d.launch()
