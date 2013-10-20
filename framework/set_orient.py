import itk
import itkSpatialOrientation
import sys

import pos_wrapper_skel
import pos_itk_core

def print_matrix(matrix):
    print "[", matrix.get(0,0), matrix.get(0,1), matrix.get(0,2) , "]"
    print "[", matrix.get(1,0), matrix.get(1,1), matrix.get(1,2) , "]"
    print "[", matrix.get(2,0), matrix.get(2,1), matrix.get(2,2) , "]"


def get_direction_matrix(code):
    rai=code
    e=itk.vnl_matrix_fixed.D_3_3()
    e.set_identity()

    d=itk.vnl_matrix_fixed.D_3_3()
    d.set_identity()

    codes=[["R","L"], ["A","P"], ["I","S"]]

    for i in range(3):
        matched = False
        for j in range(3):
            for k in range(2):
                if rai[i] == codes[j][k]:
                    mp = [-1.0, 1.0][k==0]
                    d.set(0,i,  e.get(j,0) * mp)
                    d.set(1,i,  e.get(j,1) * mp)
                    d.set(2,i,  e.get(j,2) * mp)

                    codes[j][0] = codes[j][1] = 'X'
                    matched = True
    print_matrix(d)
    return itk.Matrix.D33(d)


class reorient_image_wrokflow(pos_wrapper_skel.generic_workflow):
    """
    """
    rgb_out_component_type = itk.Image.UC3

    def _validate_options(self):
        assert self.options['sliceAxisIndex'] in [0,1,2] , \
            self._logger.error("The slicing plane has to be either 0, 1 or 2.")

        assert self.options['inputFileName'] is not None, \
            self._logger.error("No input provided (-i ....). Plese supply input filename and try again.")

        # TODO: Check if the image to reorient is indeed three dimensional!


    def launch(self):
        """
        Launch the filter. If multicomponent image is provided approperiate
        workflow is used to process it. In case of grayscale image - grayscale
        workflow is used.
        """
        if self.options.stackingOptions:
            self._stack_input_slices()
        else:
            self._load_input_volume()

        numbers_of_components = \
            self._reader.GetOutput().GetNumberOfComponentsPerPixel()

        if numbers_of_components > 1:
            processed_components = []

            for i in range(numbers_of_components):
                extract_filter = \
                    itk.VectorIndexSelectionCastImageFilter[\
                    self._input_type, self.rgb_out_component_type].New()
                extract_filter.SetIndex(i)
                extract_filter.SetInput(self._reader.GetOutput())

                processed_channel = \
                    self.process_single_channel(extract_filter.GetOutput())
                processed_components.append(processed_channel)

            compose = itk.ComposeImageFilter[
                self.rgb_out_component_type,
                self._input_type].New(
                    Input1 = processed_components[0],
                    Input2 = processed_components[1],
                    Input3 = processed_components[2])
            processed_image = compose.GetOutput()

        else:
            processed_image =\
                self.process_single_channel(self._reader.GetOutput())

        self._writer=itk.ImageFileWriter[processed_image].New()
        self._writer.SetFileName(self.options.outputFile)
        self._writer.SetInput(processed_image)
        self._writer.Update()

    def process_single_channel(self, input_image):

        # Permuting the input image
        permute = itk.PermuteAxesImageFilter[input_image].New()
        permute.SetInput(input_image)
        permute.SetOrder(self.options.permutation)

        # Flipping the permuted volume
        flip = itk.FlipImageFilter[permute.GetOutput()].New()
        flip.SetInput(permute.GetOutput())
        flip.SetFlipAxes(self.options.flipAxes)

        if self.options.flipAroundOrigin:
            flip.FlipAboutOriginOn()
        else:
            flip.FlipAboutOriginOff()

        # Changing the image information
        change_information = \
                itk.ChangeInformationImageFilter[flip.GetOutput()].New()
        change_information.SetInput(flip.GetOutput())

        if self.options.setOrigin:
            change_information.ChangeOriginOn()
            change_information.SetOutputOrigin(self.options.setOrigin)

        if self.options.setSpacing:
            change_information.ChangeSpacingOn()
            change_information.SetOutputSpacing(self.options.setSpacing)

        if self.options.orientationCode:
            change_information.ChangeDirectionOn()
            new_code = get_direction_matrix(self.options.orientationCode.upper())
            change_information.SetOutputDirection(new_code)

        # Latch the changes
        change_information.Update()
        last_image = change_information.GetOutput()

        # Resample the image, if required
        if self.options.resample:
            last_image = pos_itk_core.resample_image_filter(\
                change_information.GetOutput(),
                self.options.resample,
                interpolation=self.options.interpolation)

        return last_image

    def _stack_input_slices(self):
        start, stop, step = tuple(self.options.stackingOptions)

        first_slice = self.options.inputFile % (start)
        slice_type = pos_itk_core.autodetect_file_type(first_slice)
        self._input_type = pos_itk_core.types_increased_dimensions[slice_type]

        nameGenerator = itk.NumericSeriesFileNames.New()
        nameGenerator.SetSeriesFormat(self.options.inputFile)
        nameGenerator.SetStartIndex(start)
        nameGenerator.SetEndIndex(stop)
        nameGenerator.SetIncrementIndex(step)

        self._reader = itk.ImageSeriesReader[self._input_type].New()
        self._reader.SetFileNames(nameGenerator.GetFileNames())
        self._reader.Update()

    def _load_input_volume(self):
        self._input_type = \
            pos_itk_core.autodetect_file_type(self.options.inputFile)

        self._reader = itk.ImageFileReader[self._input_type].New()
        self._reader.SetFileName(self.options.inputFile)
        self._reader.Update()

    @classmethod
    def _getCommandLineParser(cls):
        parser = pos_wrapper_skel.generic_workflow._getCommandLineParser()

        parser.add_option('--outputFile', '-o', dest='outputFile', type='str',
                default=None, help='')
        parser.add_option('--inputFile', '-i', dest='inputFile', type='str',
                default=None, help='')
        parser.add_option('--orientationCode', dest='orientationCode', type='str',
                default=None, help='')
        parser.add_option('--stackingOptions', dest='stackingOptions', type='int',
                default=None, help='first, last, increment', nargs=3)

        parser.add_option('--interpolation', default='linear',
                type='str', dest='interpolation',
                help='<NearestNeighbor|Linear')
        parser.add_option('--resample', default=None,
                type='float', nargs=3, dest='resample',
                help='Resampling vector (%, floats ). Mutualy exclusive with --resample-mm option.')
        parser.add_option('--permutation', default=[0,1,2],
                type='int', nargs=3, dest='permutation',
                help='Apply axes permutation. Permutation has to be provided as sequence of 3 integers separated by space. Identity (0,1,2) permutation is a default one.')
        parser.add_option('--flipAxes', default=[0,0,0],
                type='int', nargs=3, dest='flipAxes',
                help='Select axes to flip. Selection has to be provided as sequence of three numbers. E.g. \'0 0 1\' will flip the z axis.')
        parser.add_option('--flipAroundOrigin', default=False,
                dest='flipAroundOrigin', action='store_const', const=True,
                help='Flip around origin.')
        parser.add_option('--setSpacing',
                dest='setSpacing', type='float', nargs=3, default=None,
                help='Set spacing values. Spacing has to be provided as three floats.')
        parser.add_option('--setOrigin', dest='setOrigin', type='float',
                nargs=3, default=None,
                help='Set origin values instead of voxel location. Origin has to be provided as three floats.')

        return parser

if __name__ == '__main__':
    options, args = reorient_image_wrokflow.parseArgs()
    d = reorient_image_wrokflow(options, args)
    d.launch()
