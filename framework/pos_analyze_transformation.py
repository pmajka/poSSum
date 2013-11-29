#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys
from optparse import OptionParser, OptionGroup
import math
import numpy as np
from pos_wrapper_skel import generic_workflow


class transformation_analyzer(generic_workflow):
    """
    A script analyzing the affine transformation series produces by the
    sequential alignment script.
    """

    _usage = ""

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
            self._transformation_parameters_list.append( \
                self._process_single_transformation(transformation_file))

    def _process_single_transformation(self, transformation_file):
        """
        Extracts paramters from a single itk 2d rigid transform file.
        """
        transformation_string =  open(transformation_file).readlines()
        transformation_parameters = self._extractParameters(transformation_string)
        return transformation_parameters

    def _extractParameters(self, transformation_string):
        """
        Extracts transformation parameters from the transformation file
        contents.

        #TODO: Provide detailed syntax of the trasnsformation file content.

        returns {parameterName: parameterValue}
        """

        # We assume that the transofmration string is correct, it may turn out
        # later that it is not:
        validation_flag = True

        # Check if the string really contains a itk transformation:
        if not transformation_string[2].strip().split(':')[0] == 'Transform':
            validation_flag = False

        if not transformation_string[3].strip().split(':')[0] == 'Parameters':
            validation_flag = False

        if not validation_flag:
            raise ValueError, "%s contains invalid transformation description." % transformation_string

        parameters_string = transformation_string[3].strip().split(':')[1].strip().split(' ')
        assert(len(parameters_string) == 6), "Number of parameters in the transformation has to be 6."

        transformationParams =  tuple(map(float, parameters_string))
        sx, ra, rb, sy, tx, ty = transformationParams
        phi = 90 - math.degrees(math.acos(rb))

        result = {'rotation' : phi, 'translation' : (tx, ty)}
        return result

    def _plot_transformation_parameters(self):
        """
        Draws a gnuplot chart illustrating changes of the parameters in
        different slices.
        """

        # Generate numpy arrays containing all of the parameters of the
        # transform, namely: translation in both directions and rotation
        translations = np.array(map(lambda x: x['translation'], \
                        self._transformation_parameters_list))
        rotations = np.array(map(lambda x: x['rotation'], \
                        self._transformation_parameters_list))

        # Define some nice aliases to easily manipulate the data.
        translation_x_array = translations[:,0]
        translation_y_array = translations[:,1]
        rotation_array = rotations[:]

        # Prepare a column array for convenient saving the transformation
        # parameters.
        columnsArray = np.column_stack((rotation_array,
            translation_x_array,translation_y_array))

        # Generate filenames for all the files used in this procedure
        reportFilename = self.options.reportFilename
        plotFilename   = self.options.plotFilename

        # Save the transformation parameters into the file
        # for further ploting
        np.savetxt(reportFilename, columnsArray, delimiter='\t')

        # And then, plot the transformation parameters.
        self._plot_sequential_alignment(translation_x_array, translation_y_array, rotation_array)

    def _plot_sequential_alignment(self, x_trans, y_trans, rotation):
        no_of_slices = len(self.args)
        slices = np.arange(1, no_of_slices+1)

        import matplotlib.pyplot as plt
        import matplotlib
        from mpl_toolkits.axes_grid1 import host_subplot
        from matplotlib.ticker import FormatStrFormatter
        import mpl_toolkits.axisartist as AA

        matplotlib.rcParams['font.sans-serif']='Arial'
        size=tuple(map(lambda x: 2.0*x, (3,2)))
        fig = plt.figure(figsize=size, dpi=100)

        additional_plot = host_subplot(111, axes_class=AA.Axes)
        right_y_axis = additional_plot.twinx()
        right_y_axis.yaxis.set_major_formatter(FormatStrFormatter('%0.1f'))

        plt.plot(slices, y_trans, linewidth=2.0, color = "#fab41e", linestyle="-", label="horizontal translation")
        plt.plot(slices, x_trans, linewidth=2.0, color = "#c4522f", linestyle="-", label="vertical translation")
        right_y_axis.plot(slices, rotation, linewidth=2.0, color = "#317a6b", linestyle="-", label="rotation")

        plt.title('Sequential alignment $t_x=23$')

        plt.ylabel('translation (mm)')
        plt.xlabel('slice index (1)')
        right_y_axis.set_ylabel("rotation (degree)")

        right_y_axis.set_ylim(-5, 5)
        plt.xlim(1,21)
        plt.ylim(-15,15)
        plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%0.0f'))
        plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%d'))

        plt.legend(loc="upper right", bbox_to_anchor=(1,1),
                   frameon=False, labelspacing=0, handlelength=2,
                   fontsize=13)

        if self.options.plotFilename:
            plt.savefig(self.options.plotFilename, dpi=100)
        else:
            plt.show()
        matplotlib.pyplot.close()

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('--inputImageDir', default=None,
            type='str', dest='inputImageDir',
            help='')
        parser.add_option('--reportFilename', default=None,
            type='str', dest='reportFilename',
            help='')
        parser.add_option('--plotFilename', default=None,
            type='str', dest='plotFilename',
            help='Image filename.')

        return parser

if __name__ == '__main__':
    options, args = transformation_analyzer.parseArgs()
    d = transformation_analyzer(options, args)
    d.launch()
