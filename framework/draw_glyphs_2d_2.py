from vtk import*
from pos_palette import pos_palette

SCALAR_BAR_TEXT_COLOR=(1,1,1)
JACOBIAN_BAR_NAME="Jacobian of the deformation filed"
JACOBIAN_BAR_LOCATION=(0.95, 0.5)
JACOBIAN_BAR_SIZE=(.05, .5)

DEFORMATION_BAR_NAME="Magnitude of the displacement vector"
DEFORMATION_BAR_LOCATION=(0.025,0.5)
DEFORMATION_BAR_SIZE=(.05, .5)

def _get_vtk_image_from_file(filename):
    reader = vtkStructuredPointsReader()
    reader.SetFileName(filename)
    reader.Update()
    
    valuerange = reader.GetOutput().GetScalarRange()
    print "Reading :", filename 
    print "valuerange",valuerange
    print 
    
    return reader

def _get_jacobian_lut():
    palette = pos_palette.lib('cool-warm')
    lookup_table = palette.color_transfer_function(\
            additional_mapping=[(0.0,0.5),(0.5,1.0),(1.0,2.0)])
    
    return lookup_table 

def _get_deformation_lut():
    lookup_table = \
        pos_palette.lib('bb',\
                        min = 0, max = 25).color_transfer_function()
    
    return lookup_table

def _get_jacobian_image_actor(filename, lut):
    reader = _get_vtk_image_from_file(filename)
    
    mapper = vtkDataSetMapper()
    mapper.SetInput(reader.GetOutput())
    mapper.SetScalarRange(reader.GetOutput().GetScalarRange())
    mapper.SetScalarVisibility(1)
    #mapper.SetScalarRange(0.5, 1.5)
    mapper.SetLookupTable(lut)
    
    actor = vtkLODActor()
    actor.GetProperty().SetOpacity(0.6)
    actor.SetMapper(mapper)
    
    return actor

def _get_slice_image_actor(filename):
    reader = _get_vtk_image_from_file(filename)
    
    cast = vtkImageCast();
    cast.SetInput(reader.GetOutput())
    cast.SetOutputScalarTypeToUnsignedChar()
    cast.Update()
     
    actor = vtkImageActor()
    actor.SetInput(cast.GetOutput())
    
    return actor

def _get_deformation_magnitude_actor(source_image, lut):
    """
    """
    calculator = vtkArrayCalculator()
    calculator.SetInputConnection(source_image.GetOutputPort())
    calculator.SetAttributeModeToUsePointData()
    calculator.SetResultArrayName("result")
    calculator.AddScalarVariable("u", "scalars", 0)
    calculator.AddScalarVariable("v", "scalars", 1)
    calculator.SetFunction("mag(u*iHat+v*jHat+0*kHat)")
    calculator.Update()
    
    print calculator.GetOutput().GetScalarRange()
    
    mapper = vtkDataSetMapper()
    mapper.SetInput(calculator.GetOutput())
    mapper.SetScalarRange(calculator.GetOutput().GetScalarRange())
    #mapper.SetScalarRange(0,25)
    mapper.SetScalarVisibility(1)
    mapper.SetLookupTable(lut)
    
    actor = vtkLODActor()
    actor.GetProperty().SetOpacity(0.5)
    actor.SetMapper(mapper)
    
    return actor

def _get_deformation_points(source_image):
    ac = vtkArrayCalculator()
    ac.SetInputConnection(source_image.GetOutputPort())
    ac.SetAttributeModeToUsePointData()
    ac.SetResultArrayName("result")
    ac.AddScalarVariable("u", "scalars", 0)
    ac.AddScalarVariable("v", "scalars", 1)
    ac.SetFunction("u*iHat+v*jHat+0*kHat")
    
    maxnpts=5000
    ptMask = vtkMaskPoints()
    ptMask.SetInputConnection(ac.GetOutputPort())
    ptMask.SetOnRatio(10)
    ptMask.SetMaximumNumberOfPoints(maxnpts);
    ptMask.RandomModeOn()
    ptMask.Update()
    
    return ptMask

def _get_glyphs_actor(points, lut):
    """
    """
    source_glyph = vtkArrowSource()
    source_glyph.SetTipRadius(0.1)
    source_glyph.SetTipLength(0.35)
    source_glyph.SetShaftRadius(0.03)
    
    glyph = vtkGlyph3D()
    glyph.SetInput(points.GetOutput())
    glyph.SetSource(source_glyph.GetOutput())
    glyph.ScalingOn()
    
    #glyph.SetColorModeToColorByScalar()
    #glyph.SetColorModeToColorByScale()
    glyph.SetColorModeToColorByVector()
    
    glyph.SetScaleModeToScaleByVector()
    #glyph.SetScaleModeToScaleByScalar()
    glyph.SetScaleFactor(6)
    
    glyph.SetVectorModeToUseVector()
    
    #glyph.SetIndexModeToVector()
    #glyph.SetIndexModeToScalar()
    #glyph.SetIndexModeToOff()
    glyph.OrientOn()
    
    mapper = vtkPolyDataMapper()
    mapper.SetInput(glyph.GetOutput())
    mapper.SetScalarRange(points.GetOutput().GetScalarRange())
    mapper.SetLookupTable(lut)
    #hhogMapper.SetUseLookupTableScalarRange(0)
    
    actor = vtkActor()
    actor.SetMapper(mapper)
    
    return actor

def _get_scalar_bar_actor(title, location, size, lut):
    scalar_bar = vtkScalarBarActor()
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

def _get_deformation_scalar_bar(lut):
    return _get_scalar_bar_actor(DEFORMATION_BAR_NAME, DEFORMATION_BAR_LOCATION,
                                 DEFORMATION_BAR_SIZE, lut)

def _get_jacobian_scalar_bar(lut):
    return _get_scalar_bar_actor(JACOBIAN_BAR_NAME, JACOBIAN_BAR_LOCATION,
                                 JACOBIAN_BAR_SIZE, lut)

def _display():
    pass

ren    = vtkRenderer()
renWin = vtkRenderWindow()
#renWin.SetSize(1027,749)
renWin.SetSize(500,350)
renWin.AddRenderer(ren)

lut2 = _get_deformation_lut()
lut4 = _get_jacobian_lut() 

ia=_get_slice_image_actor('/home/pmajka/i0160.vtk')
ren.AddActor(ia)

dataActor2 = _get_jacobian_image_actor('/home/pmajka/j0160.vtk', lut4)
ren.AddActor(dataActor2)

reader = _get_vtk_image_from_file('/home/pmajka/0160.vtk')
#dataActor = _get_deformation_magnitude_actor(reader, lut2) 
#ren.AddActor(dataActor)

ptMask = _get_deformation_points(reader)
ren.AddActor(_get_glyphs_actor(ptMask, lut2))
ren.AddActor(_get_jacobian_scalar_bar(lut2))
ren.AddActor(_get_deformation_scalar_bar(lut4))

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
interactorstyle = iren.GetInteractorStyle()
interactorstyle.SetCurrentStyleToTrackballCamera()

renWin.Render()
iren.Initialize()
iren.Start()
