import vtk
from pos_palette import pos_palette
from pos_wrapper_skel import generic_workflow
from pos_filenames import filename
from pos_parameters import generic_wrapper, value_parameter, filename_parameter, vector_parameter

SCALAR_BAR_TEXT_COLOR=(1,1,1)
JACOBIAN_BAR_NAME="Jacobian of the deformation filed"
JACOBIAN_BAR_LOCATION=(0.95, 0.5)
JACOBIAN_BAR_SIZE=(.05, .5)

DEFORMATION_BAR_NAME="Magnitude of the displacement vector"
DEFORMATION_BAR_LOCATION=(0.025,0.5)
DEFORMATION_BAR_SIZE=(.05, .5)

class vtk_slice_image(generic_wrapper):
    _template = """c{dimension}d {input_image} {spacing} -o {output_image}"""
    
    _parameters = { \
            'dimension'     : value_parameter('dimension', 2),
            'input_image'   : filename_parameter('input_image', None),
            'output_image'  : filename_parameter('output_image', None),
            'spacing' : vector_parameter('spacing', None, '-spacing {_list}mm')
            }

class vtk_warp(generic_wrapper):
    _template = """c{dimension}d -mcs {input_image} \
            -foreach {spacing} -endfor\
            -omc 2 {output_image}"""
    
    _parameters = { \
            'dimension'     : value_parameter('dimension', 2),
            'input_image'     : filename_parameter('input_image', None),
            'output_image'    : filename_parameter('output_image', None),
            'spacing' : vector_parameter('spacing', None, '-spacing {_list}mm')
            }

class vtk_jacobian(generic_wrapper):
    _template = """ANTSJacobian {dimension} {input_image} {output_naming};
    c{dimension}d {input_jacobian_image} {spacing} -o {output_image}"""
    
    _parameters = { \
            'dimension'     : value_parameter('dimension', 2),
            'input_image'   : filename_parameter('input_image', None),
            'input_jacobian_image'   : filename_parameter('input_jacobian_image', None),
            'output_naming' : filename_parameter('output_naming', None),
            'output_image'    : filename_parameter('output_image', None),
            'spacing' : vector_parameter('spacing', None, '-spacing {_list}mm')
            }

class deformation_field_visualizer(generic_workflow):
    _f = { \
        'src_naming'   : filename('src_naming'  , work_dir = '00_srcjacobian', str_template = 'basename_'),
        'src_jacobian' : filename('src_jacobian', work_dir = '00_srcjacobian', str_template = 'basename_jacobian.nii.gz'),
        'image'      : filename('image', work_dir = '01_image', str_template = 'image.vtk'),
        'deformation': filename('deformation', work_dir = '02_deformation', str_template = 'deformation.vtk'),
        'jacobian'   : filename('jacobian', work_dir = '03_jacobian', str_template = 'jacobian.vtk'),
        'screenshot' : filename('screenshot', work_dir = '04_screenshot', str_template = 'screenshot_{idx:04d}.vtk'),
        'analysis'   : filename('analysis', work_dir = '05_analysis', str_template = 'analysis.txt')
        }
    
    def __init__(self, options, args, pool = None):
        super(self.__class__, self).__init__(options, args, pool)
    
    def _get_vtk_image_from_file(self, filename):
        reader = vtk.vtkStructuredPointsReader()
        reader.SetFileName(filename)
        reader.Update()
        
        valuerange = reader.GetOutput().GetScalarRange()
        print "Reading :", filename 
        print "valuerange",valuerange
        print 
        
        return reader
    
    def _get_jacobian_lut(self):
        jmin, jmid, jmax = tuple(self.options.jacobianScaleMapping)
        jacobian_mapping = [(0.0, jmin), (0.5, jmid), (1.0, jmax)]
        
        palette = pos_palette.lib('cool-warm')
        lookup_table = \
            palette.color_transfer_function(additional_mapping = jacobian_mapping)
        
        return lookup_table 
    
    def _get_deformation_lut(self):
        dmin, dmax = tuple(self.options.deformationScaleRange)
        
        lookup_table = \
            pos_palette.lib('bb',\
                            min = dmin, max = dmax).color_transfer_function()
        
        return lookup_table
    
    def _get_jacobian_image_actor(self, filename, lut):
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
        reader = self._get_vtk_image_from_file(filename)
        
        cast = vtk.vtkImageCast();
        cast.SetInput(reader.GetOutput())
        cast.SetOutputScalarTypeToUnsignedChar()
        cast.Update()
        
        actor = vtk.vtkImageActor()
        actor.SetInput(cast.GetOutput())
        
        return actor
    
    def _get_deformation_magnitude_actor(self, source_image, lut):
        """
        """
        calculator = vtk.vtkArrayCalculator()
        calculator.SetInputConnection(source_image.GetOutputPort())
        calculator.SetAttributeModeToUsePointData()
        calculator.SetResultArrayName("result")
        calculator.AddScalarVariable("u", "scalars", 0)
        calculator.AddScalarVariable("v", "scalars", 1)
        calculator.SetFunction("mag(u*iHat+v*jHat+0*kHat)")
        calculator.Update()
        
        print calculator.GetOutput().GetScalarRange()
        
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInput(calculator.GetOutput())
        mapper.SetScalarRange(calculator.GetOutput().GetScalarRange())
        #mapper.SetScalarRange(0,25)
        mapper.SetScalarVisibility(1)
        mapper.SetLookupTable(lut)
        
        actor = vtk.vtkLODActor()
        actor.GetProperty().SetOpacity(self.options.deformationOverlayOpacity)
        actor.SetMapper(mapper)
        
        return actor
    
    def _get_deformation_points(self, source_image):
        ac = vtk.vtkArrayCalculator()
        ac.SetInputConnection(source_image.GetOutputPort())
        ac.SetAttributeModeToUsePointData()
        ac.SetResultArrayName("result")
        ac.AddScalarVariable("u", "scalars", 0)
        ac.AddScalarVariable("v", "scalars", 1)
        ac.SetFunction("u*iHat+v*jHat+0*kHat")
        
        maxnpts = self.options.glyphConfiguration[0]
        ptMask = vtk.vtkMaskPoints()
        ptMask.SetInputConnection(ac.GetOutputPort())
        ptMask.SetOnRatio(self.options.glyphConfiguration[1])
        ptMask.SetMaximumNumberOfPoints(maxnpts);
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
        
        #glyph.SetColorModeToColorByScalar()
        #glyph.SetColorModeToColorByScale()
        glyph.SetColorModeToColorByVector()
        
        glyph.SetScaleModeToScaleByVector()
        #glyph.SetScaleModeToScaleByScalar()
        glyph.SetScaleFactor(self.options.glyphConfiguration[2])
        
        glyph.SetVectorModeToUseVector()
        
        #glyph.SetIndexModeToVector()
        #glyph.SetIndexModeToScalar()
        #glyph.SetIndexModeToOff()
        glyph.OrientOn()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(glyph.GetOutput())
        mapper.SetScalarRange(points.GetOutput().GetScalarRange())
        mapper.SetLookupTable(lut)
        #hhogMapper.SetUseLookupTableScalarRange(0)
        
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
        return self._get_scalar_bar_actor(\
                DEFORMATION_BAR_NAME, DEFORMATION_BAR_LOCATION,
                DEFORMATION_BAR_SIZE, lut)
    
    def _get_jacobian_scalar_bar(self, lut):
        return self._get_scalar_bar_actor(\
                JACOBIAN_BAR_NAME, JACOBIAN_BAR_LOCATION,
                JACOBIAN_BAR_SIZE, lut)
    
    def _prepare_files(self):
        prepare_jacobian_command = vtk_jacobian(
                dimension = 2,
                input_image   = self.options.warpImage,
                output_naming = self.f['src_naming'](),
                input_jacobian_image = self.f['src_jacobian'](),
                spacing = self.options.spacing, 
                output_image = self.f['jacobian']())
        prepare_jacobian_command()
        
        prepare_deformation_wrap = vtk_warp(
                dimension = 2,
                input_image  = self.options.warpImage,
                output_image = self.f['deformation'](),
                spacing = self.options.spacing)
        prepare_deformation_wrap()
        
        prepare_slice_image = vtk_slice_image(
                dimension = 2,
                input_image  = self.options.sliceImage,
                output_image = self.f['image'](),
                spacing = self.options.spacing)
        prepare_slice_image()
    
    def _display(self):
        self._prepare_files()
         
        ren    = vtk.vtkRenderer()
        renWin = vtk.vtkRenderWindow()
        renWin.SetSize(*tuple(self.options.rendererWindowSize))
        renWin.AddRenderer(ren)
        
        lut2 = self._get_deformation_lut()
        lut4 = self._get_jacobian_lut() 
        
        ia = self._get_slice_image_actor(self.f['image']())
        ren.AddActor(ia)
        
        dataActor2 = self._get_jacobian_image_actor(self.f['jacobian'](), lut4)
        ren.AddActor(dataActor2)
        
        reader = self._get_vtk_image_from_file(self.f['deformation']())
        dataActor = self._get_deformation_magnitude_actor(reader, lut2) 
        ren.AddActor(dataActor)
        
        ptMask = self._get_deformation_points(reader)
        ren.AddActor(self._get_glyphs_actor(ptMask, lut2))
        ren.AddActor(self._get_jacobian_scalar_bar(lut2))
        ren.AddActor(self._get_deformation_scalar_bar(lut4))
        
        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(renWin)
        interactorstyle = iren.GetInteractorStyle()
        interactorstyle.SetCurrentStyleToTrackballCamera()
        
        renWin.Render()
        iren.Initialize()
        iren.Start()
    
    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()
        
        parser.add_option('-w', '--warpImage', default=None,
                type='str', dest='warpImage',
                help='Input defomation field (warp) image')
        parser.add_option('-i', '--sliceImage', default=None,
                type='str', dest='sliceImage',
                help='Input slice image (preferably png image, nifti will work as well.')
        parser.add_option('--deformationScaleRange', default=[0,4],
                type='float', dest='deformationScaleRange',  nargs=2,
                help='Scale for deformation colormap')
        parser.add_option('--jacobianScaleMapping', default=[0.5,1.0,1.5],
                type='float', dest='jacobianScaleMapping', nargs=3,
                help='Scale mapping for jacobian colormap')
        parser.add_option('--jacobianOverlayOpacity', default=0.5,
                type='float', dest='jacobianOverlayOpacity',
                help='Opacity of the jacobian colormap')
        parser.add_option('--deformationOverlayOpacity', default=0.5,
                type='float', dest='deformationOverlayOpacity',
                help='Opacity of the deformation colormap')
        parser.add_option('--glyphConfiguration', default=[5000,10,6],
                type='int', dest='glyphConfiguration', nargs=3,
                help='Glyph configuration (int:max_probe_points:5000, int:probe_ratio:10, int:scale_factor:6)')
        parser.add_option('--rendererWindowSize', default=[500,350],
                type='int', dest='rendererWindowSize', nargs=2,
                help='Size of the render window.')
        parser.add_option('--spacing', default=[1,1],
                type='float', dest='spacing', nargs=2,
                help='Spacing of the image/deformation field/jacobian.')
        
        return parser

if __name__ == '__main__':
    options, args = deformation_field_visualizer.parseArgs()
    d = deformation_field_visualizer(options, args)
    d._display()
