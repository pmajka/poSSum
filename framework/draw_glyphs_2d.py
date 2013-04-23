import vtk
from pos_palette import pos_palette
from pos_wrapper_skel import generic_workflow
from pos_parameters import value_parameter, filename_parameter, vector_parameter, filename
import pos_wrappers

SCALAR_BAR_TEXT_COLOR = (1, 1, 1)
JACOBIAN_BAR_NAME = "Jacobian of the deformation filed"
JACOBIAN_BAR_LOCATION = (0.95, 0.5)
JACOBIAN_BAR_SIZE = (.05, .5)

DEFORMATION_BAR_NAME = "Magnitude of the displacement vector"
DEFORMATION_BAR_LOCATION = (0.025, 0.5)
DEFORMATION_BAR_SIZE = (.05, .5)

JACOBIAN_COLOR_PALETTE_NAME = 'cool-warm'
DEFORMATION_FILED_PALETTE_NAME = 'bb'


class convert_slice_image(pos_wrappers.generic_wrapper):
    _template = """c{dimension}d {input_image} {spacing} -o {output_image}"""

    _parameters = {
            'dimension'     : value_parameter('dimension', 2),
            'input_image'   : filename_parameter('input_image', None),
            'output_image'  : filename_parameter('output_image', None),
            'spacing' : vector_parameter('spacing', None, '-spacing {_list}mm')
            }


class convert_wrap_file(pos_wrappers.generic_wrapper):
    _template = """c{dimension}d -mcs {input_image} \
            -foreach {spacing} -endfor\
            -omc 2 {output_image}"""

    _parameters = {
            'dimension'     : value_parameter('dimension', 2),
            'input_image'     : filename_parameter('input_image', None),
            'output_image'    : filename_parameter('output_image', None),
            'spacing' : vector_parameter('spacing', None, '-spacing {_list}mm')
            }


class generate_jacobian_vtk(pos_wrappers.generic_wrapper):
    _template = """ANTSJacobian {dimension} {input_image} {output_naming};
    c{dimension}d {input_jacobian_image} {spacing} -o {output_image}"""

    _parameters = {
            'dimension'     : value_parameter('dimension', 2),
            'input_image'   : filename_parameter('input_image', None),
            'input_jacobian_image'   : filename_parameter('input_jacobian_image', None),
            'output_naming' : filename_parameter('output_naming', None),
            'output_image'    : filename_parameter('output_image', None),
            'spacing' : vector_parameter('spacing', None, '-spacing {_list}mm')
            }


class deformation_field_visualizer(generic_workflow):
    _f = {
        'src_naming'   : filename('src_naming', work_dir='00_srcjacobian', str_template='basename_'),
        'src_jacobian' : filename('src_jacobian', work_dir='00_srcjacobian', str_template='basename_jacobian.nii.gz'),
        'image'      : filename('image', work_dir='01_image', str_template='image.vtk'),
        'deformation': filename('deformation', work_dir='02_deformation', str_template='deformation.vtk'),
        'jacobian'   : filename('jacobian', work_dir='03_jacobian', str_template='jacobian.vtk'),
        'screenshot' : filename('screenshot', work_dir='04_screenshot', str_template='screenshot_{idx:04d}.vtk'),
        'analysis'   : filename('analysis', work_dir='05_analysis', str_template='analysis.txt')
        }

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

    def _get_vtk_image_from_file(self, filename):
        """
        Read vtkImageData from the provided file.

        :param filename: file to read the image form
        :return: vtkStructuredPointsReader
        """

        reader = vtk.vtkStructuredPointsReader()
        reader.SetFileName(filename)
        reader.Update()

        valuerange = reader.GetOutput().GetScalarRange()

        self._logger.info("Loading vtk image %s.", filename)
        self._logger.info("Scalar range of image %s: %s.",
                          filename, valuerange)

        return reader

    def _get_jacobian_lut(self):
        """
        Get color table for the data related to jacobian

        :return: vtkColorTransferFunction
        """

        # There are three key points in the jacobian color map: the point with
        # highest contration, the point with no expansion/compression and the
        # point with maximal expansion. Get values of the control points from
        # command line parameters.
        jmin, jmid, jmax = tuple(self.options.jacobianScaleMapping)

        # Map the 0-1 range to using the provided control points.
        jacobian_mapping = [(0.0, jmin), (0.5, jmid), (1.0, jmax)]
        self._logger.debug("Loading jacobian scale mapping: %s",
                           str(jacobian_mapping))

        # Get and return the lookup table.
        palette = pos_palette.lib(JACOBIAN_COLOR_PALETTE_NAME)
        lookup_table = \
            palette.color_transfer_function(additional_mapping=jacobian_mapping)

        return lookup_table

    def _get_deformation_lut(self):
        """
        Get color lookup table for the magnitude of the deformation field.

        :return: vtkColorTransferFunction
        """

        # Get lower and upper boundary for the deformation field.
        dmin, dmax = tuple(self.options.deformationScaleRange)

        # Get the approperiate color transfer function
        lookup_table = \
            pos_palette.lib(DEFORMATION_FILED_PALETTE_NAME,
                            min=dmin, max=dmax).color_transfer_function()

        return lookup_table

    def _get_jacobian_image_actor(self, filename, lut):
        """
        Get image actor containing image of the jacobian.

        :param filename: Filename if the jacobian image. Trivial
        :param lut: lookuptable to use

        :return: vtkActor
        """
        self._logger.debug("Genarating jacobian image actor from %s.",
                           filename)

        reader = self._get_vtk_image_from_file(filename)

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInput(reader.GetOutput())
        mapper.SetScalarRange(reader.GetOutput().GetScalarRange())
        mapper.SetScalarVisibility(1)
        mapper.SetLookupTable(lut)

        actor = vtk.vtkLODActor()
        actor.GetProperty().SetOpacity(self.options.jacobianOverlayOpacity)
        actor.SetMapper(mapper)

        return actor

    def _get_slice_image_actor(self, filename):
        """
        Get image actor containing the slice image. There is no option to
        provide lookuptable. The slice image is displayed using default,
        grayscale color mapping.

        :param filename: Filename if the jacobian image. Trivial
        :return: vtkImageActor
        """
        self._logger.debug("Genarating slice image actor from %s.",
                           filename)

        reader = self._get_vtk_image_from_file(filename)

        cast = vtk.vtkImageCast()
        cast.SetInput(reader.GetOutput())
        cast.SetOutputScalarTypeToUnsignedChar()
        cast.Update()

        actor = vtk.vtkImageActor()
        actor.SetInput(cast.GetOutput())

        return actor

    def _get_deformation_magnitude_actor(self, source_image, lut):
        """
        Get actor containing deformation magnitude image colored trough provided
        lookuptable.

        :param source_image: vtkImageReader outputing float, two component image.
        :param lut: lookuptable to use

        :return: vtkActor
        """

        # The loaded image contains two dimensional vector deformation field.
        # It means that it has two scalar variables decribing each vector
        # component of the image. Simple. We need to calculate the magnitude of
        # the vector for each pixel of the image. To perform this calcualtion we
        # will use a vtkArrayCalculator.

        # Because we want our deformation field to be scaled in milimeters, we
        # need to multiply it by pixel size.
        pixel_size = float(self.options.spacing[0])
        self._logger.debug("Using pixel size: %f for deformation magnitude calculations.",
                           pixel_size)

        calculator = vtk.vtkArrayCalculator()
        calculator.SetInputConnection(source_image.GetOutputPort())
        calculator.SetAttributeModeToUsePointData()
        calculator.SetResultArrayName("result")
        calculator.AddScalarVariable("u", "scalars", 0)
        calculator.AddScalarVariable("v", "scalars", 1)
        calculator.SetFunction("mag(u*iHat+v*jHat) * %f" % pixel_size)
        calculator.Update()

        self._logger.debug("Deformation field magnitude range %s.",
                           calculator.GetOutput().GetScalarRange())

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInput(calculator.GetOutput())
        mapper.SetScalarVisibility(1)
        mapper.SetLookupTable(lut)

        actor = vtk.vtkLODActor()
        actor.GetProperty().SetOpacity(self.options.deformationOverlayOpacity)
        actor.SetMapper(mapper)

        return actor

    def _get_deformation_points(self, source_image):
        """
        Extract as subset of a points from provided 2d deformation field,
        convert them to vector-type point data and return.

        :param source_image: vtkImageReader outputing float, two component image.

        :return: vtkPointData
        """

        # Because we want our deformation field to be scaled in milimeters, we
        # need to multiply it by pixel size.
        pixel_size = float(self.options.spacing[0])
        self._logger.debug("Using pixel size: %f for glyph calculation.",
                           pixel_size)

        # Use the array calculaptor to convert 2d deformation filed containing
        # a two-component image data into vector-type point data.
        ac = vtk.vtkArrayCalculator()
        ac.SetInputConnection(source_image.GetOutputPort())
        ac.SetAttributeModeToUsePointData()
        ac.SetResultArrayName("result")
        ac.AddScalarVariable("u", "scalars", 0)
        ac.AddScalarVariable("v", "scalars", 1)
        ac.SetFunction("(-1*u*iHat+-1*v*jHat) * %f" % pixel_size)

        # Take a random subset of point data (according to provided settings)
        # and return it.
        maximum_points = self.options.glyphConfiguration[0]
        ptMask = vtk.vtkMaskPoints()
        ptMask.SetInputConnection(ac.GetOutputPort())
        ptMask.SetOnRatio(self.options.glyphConfiguration[1])
        ptMask.SetMaximumNumberOfPoints(maximum_points)
        ptMask.RandomModeOn()
        ptMask.Update()

        return ptMask

    def _get_glyphs_actor(self, points, lut):
        """
        """

        source_glyph = vtk.vtkArrowSource()
        source_glyph.SetTipRadius(0.1)
        source_glyph.SetTipLength(0.35)
        source_glyph.SetShaftRadius(0.03)

        glyph = vtk.vtkGlyph3D()
        glyph.SetInput(points.GetOutput())
        glyph.SetSource(source_glyph.GetOutput())
        glyph.ScalingOn()

        glyph.SetColorModeToColorByVector()

        glyph.SetScaleModeToScaleByVector()
        glyph.SetScaleFactor(self.options.glyphConfiguration[2])

        glyph.SetVectorModeToUseVector()

        glyph.OrientOn()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(glyph.GetOutput())
        mapper.SetScalarRange(points.GetOutput().GetScalarRange())
        mapper.SetLookupTable(lut)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        return actor

    def _get_scalar_bar_actor(self, title, location, size, lut):
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(lut)
        scalar_bar.SetTitle(title)
        scalar_bar.SetOrientationToVertical()
        scalar_bar.GetLabelTextProperty().SetColor(*SCALAR_BAR_TEXT_COLOR)
        scalar_bar.GetTitleTextProperty().SetColor(*SCALAR_BAR_TEXT_COLOR)

        coord = scalar_bar.GetPositionCoordinate()
        coord.SetCoordinateSystemToNormalizedViewport()
        coord.SetValue(*location)

        scalar_bar.SetWidth(size[0])
        scalar_bar.SetHeight(size[1])

        return scalar_bar

    def _get_deformation_scalar_bar(self, lut):
        return self._get_scalar_bar_actor(
                DEFORMATION_BAR_NAME, DEFORMATION_BAR_LOCATION,
                DEFORMATION_BAR_SIZE, lut)

    def _get_jacobian_scalar_bar(self, lut):
        return self._get_scalar_bar_actor(
                JACOBIAN_BAR_NAME, JACOBIAN_BAR_LOCATION,
                JACOBIAN_BAR_SIZE, lut)

    def _prepare_files(self):
        prepare_jacobian_command = generate_jacobian_vtk(
                dimension = 2,
                input_image   = self.options.warpImage,
                output_naming = self.f['src_naming'](),
                input_jacobian_image = self.f['src_jacobian'](),
                spacing = self.options.spacing,
                output_image = self.f['jacobian']())
        prepare_jacobian_command()

        prepare_deformation_wrap = convert_wrap_file(
                dimension = 2,
                input_image  = self.options.warpImage,
                output_image = self.f['deformation'](),
                spacing = self.options.spacing)
        prepare_deformation_wrap()

        prepare_slice_image = convert_slice_image(
                dimension = 2,
                input_image  = self.options.sliceImage,
                output_image = self.f['image'](),
                spacing = self.options.spacing)
        prepare_slice_image()

    def launch(self):
        self._prepare_files()

        jacobian_image_file = self.f['jacobian']()
        slice_image_file   = self.f['image']()
        warp_image_file    = self.f['deformation']()

        # ---- begin preparing the data ----
        deformation_mag_lut = self._get_deformation_lut()
        jacobian_lut = self._get_jacobian_lut()

        slice_image_actor = self._get_slice_image_actor(slice_image_file)
        jacobian_image_actor = \
                self._get_jacobian_image_actor(jacobian_image_file, jacobian_lut)

        reader = self._get_vtk_image_from_file(warp_image_file)
        deformation_magnitude_image_actor = \
                self._get_deformation_magnitude_actor(reader, deformation_mag_lut)

        ptMask = self._get_deformation_points(reader)
        # ---- end of preparing the data ----


        # ---- begin create renderer and load the data
        renderer      = vtk.vtkRenderer()
        render_window = vtk.vtkRenderWindow()

        # ---------------
        if self.options.rendererWindowSize:
            render_window.SetSize(*tuple(self.options.rendererWindowSize))
        else:
            reader_dimensions = \
                map(lambda x: reader.GetOutput().GetDimensions()[x], [0,1])
            render_window.SetSize(*tuple(reader_dimensions))
        render_window.AddRenderer(renderer)

        # Load all the actors to the renderer
        renderer.AddActor(slice_image_actor)
        renderer.AddActor(jacobian_image_actor)
        renderer.AddActor(deformation_magnitude_image_actor)

        # Add glyphs
        if not self.options.hideGlyphs:
            renderer.AddActor(self._get_glyphs_actor(ptMask, deformation_mag_lut))

        # Add scalar bars
        if not self.options.hideColorBars:
            renderer.AddActor(self._get_jacobian_scalar_bar(deformation_mag_lut))
            renderer.AddActor(self._get_deformation_scalar_bar(jacobian_lut))

        # ---- end adding data to renderer ----
        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(render_window)
        interactorstyle = iren.GetInteractorStyle()
        interactorstyle.SetCurrentStyleToTrackballCamera()

        self._configure_camera(renderer, reader)

        render_window.Render()

        if self.options.screenshot:
            wif = vtk.vtkRenderLargeImage()
            wif.SetMagnification(self.options.screenshotMagnification)
            wif.SetInput(renderer)
            wif.Update()

            writer = vtk.vtkPNGWriter()
            writer.SetInputConnection(wif.GetOutputPort())
            writer.SetFileName(self.options.screenshot)
            writer.Write()
        else:
            iren.Initialize()
            iren.Start()

        if self.options.cleanup:
            self._cleanUp()

    def _configure_camera(self, renderer, reader):
        camera = renderer.GetActiveCamera()
        camera.ParallelProjectionOn()

        origin = reader.GetOutput().GetOrigin()
        extent = reader.GetOutput().GetWholeExtent()
        spacing = reader.GetOutput().GetSpacing()
        xc = origin[0] + 0.5*(extent[0] + extent[1])*spacing[0]
        yc = origin[1] + 0.5*(extent[2] + extent[3])*spacing[1]
        xd = (extent[1] - extent[0] + 1)*spacing[0]
        yd = (extent[3] - extent[2] + 1)*spacing[1]

        d = camera.GetDistance()
        camera.SetParallelScale(0.5*yd)
        camera.SetFocalPoint(xc,yc,0.0)
        camera.SetPosition(xc,yc,-d)
        camera.SetViewUp(0, -1, 0)

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('-w', '--warpImage', default=None,
                type='str', dest='warpImage',
                help='Input defomation field (warp) image')
        parser.add_option('-i', '--sliceImage', default=None,
                type='str', dest='sliceImage',
                help='Input slice image (preferably png image, nifti will work as well.')
        parser.add_option('--screenshot', default=None,
                type='str', dest='screenshot',
                help='Screenshot filename')
        parser.add_option('--deformationScaleRange', default=[0, 4],
                type='float', dest='deformationScaleRange',  nargs=2,
                help='Scale for deformation colormap')
        parser.add_option('--jacobianScaleMapping', default=[0.5, 1.0, 1.5],
                type='float', dest='jacobianScaleMapping', nargs=3,
                help='Scale mapping for jacobian colormap')
        parser.add_option('--jacobianOverlayOpacity', default=0.5,
                type='float', dest='jacobianOverlayOpacity',
                help='Opacity of the jacobian colormap')
        parser.add_option('--deformationOverlayOpacity', default=0.5,
                type='float', dest='deformationOverlayOpacity',
                help='Opacity of the deformation colormap')
        parser.add_option('--glyphConfiguration', default=[5000, 10, 6],
                type='float', dest='glyphConfiguration', nargs=3,
                help='Glyph configuration (int:max_probe_points:5000, int:probe_ratio:10, int:scale_factor:6)')
        parser.add_option('--rendererWindowSize', default=None,
                type='int', dest='rendererWindowSize', nargs=2,
                help='Size of the render window.')
        parser.add_option('--spacing', default=[1, 1],
                type='float', dest='spacing', nargs=2,
                help='Spacing of the image/deformation field/jacobian.')
        parser.add_option('--cameraPosition', default=None,
                type='float', dest='cameraPosition', nargs=3,
                help='Position of the camera... What did you expect?')
        parser.add_option('--hideColorBars', default=False,
                dest='hideColorBars', action='store_const', const=True,
                help='Do not display the colorbars')
        parser.add_option('--hideGlyphs', default=False,
                dest='hideGlyphs', action='store_const', const=True,
                help='Do not display deformation files vectors.')
        parser.add_option('--screenshotMagnification', default=1,
                dest='screenshotMagnification', action='store', type=int,
                help='Screenshot magnification.')

        return parser

if __name__ == '__main__':
    options, args = deformation_field_visualizer.parseArgs()
    d = deformation_field_visualizer(options, args)
    d.launch()
