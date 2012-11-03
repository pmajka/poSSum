from vtk import*

imread = vtkStructuredPointsReader()
imread.SetFileName('/home/pmajka/i0160.vtk')
imread.Update()

cast = vtkImageCast();
cast.SetInput(imread.GetOutput())
cast.SetOutputScalarTypeToUnsignedChar()
cast.Update()

ren    = vtkRenderer()
renWin = vtkRenderWindow()
#renWin.SetSize(1027,749)
renWin.SetSize(500,350)
renWin.AddRenderer(ren)


ia = vtkImageActor()
ia.SetInput(cast.GetOutput())
ren.AddActor(ia)

reader = vtkStructuredPointsReader()
reader.SetFileName('/home/pmajka/0160.vtk')
reader.Update()
valuerange = reader.GetOutput().GetScalarRange()
print "valuerange",valuerange

reader2 = vtkStructuredPointsReader()
reader2.SetFileName('/home/pmajka/j0160.vtk')
reader2.Update()
valuerange2 = reader2.GetOutput().GetScalarRange()
print "valuerange2",valuerange2

lut4 = vtkColorTransferFunction()
lut4.AddRGBPoint(0.50000,0.27451,0.42353,0.87059)
lut4.AddRGBPoint(1.00000,0.87451,0.87451,0.87451)
lut4.AddRGBPoint(2.00000,0.96471,0.12549,0.23529)


print reader2.GetOutput().GetScalarRange()
dataMapper2 = vtkDataSetMapper()
dataMapper2.SetInput(reader2.GetOutput())
dataMapper2.SetScalarRange(reader2.GetOutput().GetScalarRange())
dataMapper2.SetScalarVisibility(1)
dataMapper2.SetScalarRange(0.5,1.5)
dataMapper2.SetLookupTable(lut4)

dataActor2 = vtkLODActor()
dataActor2.GetProperty().SetOpacity(0.5)
dataActor2.SetMapper(dataMapper2)
ren.AddActor(dataActor2)


ac = vtkArrayCalculator()
ac.SetInputConnection(reader.GetOutputPort())
ac.SetAttributeModeToUsePointData()
ac.SetResultArrayName("result")
ac.AddScalarVariable("u", "scalars",0)
ac.AddScalarVariable("v", "scalars",1)
ac.SetFunction("u*iHat+v*jHat+0*kHat")

ac2 = vtkArrayCalculator()
ac2.SetInputConnection(reader.GetOutputPort())
ac2.SetAttributeModeToUsePointData()
ac2.SetResultArrayName("result")
ac2.AddScalarVariable("u", "scalars",0)
ac2.AddScalarVariable("v", "scalars",1)
ac2.SetFunction("mag(u*iHat+v*jHat+0*kHat)")
ac2.Update()

#   lut2 = vtkLookupTable()
#   lut2.SetRange(ac2.GetOutput().GetScalarRange())
#   lut2.SetValueRange(0.0, 1.0) 
#   lut2.SetHueRange(0.0, 0)
#   lut2.SetSaturationRange(1.0, 1.0)
#   lut2.SetAlphaRange(1.0,1.0)
#   lut2.SetRampToLinear()
#   lut2.SetRange(ac2.GetOutput().GetScalarRange())
#   lut2.Build()
lut2 = vtkColorTransferFunction()
lut2.AddRGBPoint(0   ,  0.0, 0.0, 0.0)
lut2.AddRGBPoint(12,  1.0, 0.0, 0.0)
lut2.AddRGBPoint(25 ,  1.0, 1.0, 0.0)

print ac2.GetOutput().GetScalarRange()
dataMapper = vtkDataSetMapper()
dataMapper.SetInput(ac2.GetOutput())
dataMapper.SetScalarRange(ac2.GetOutput().GetScalarRange())
dataMapper.SetScalarVisibility(1)
#dataMapper.SetScalarRange(0,25)
dataMapper.SetLookupTable(lut2)

dataActor = vtkLODActor()
dataActor.GetProperty().SetOpacity(0.5)
dataActor.SetMapper(dataMapper)
#ren.AddActor(dataActor)


maxnpts=5000
ptMask = vtkMaskPoints()
ptMask.SetInputConnection(ac.GetOutputPort())
ptMask.SetOnRatio(10)
ptMask.SetMaximumNumberOfPoints(maxnpts);
ptMask.RandomModeOn()
ptMask.Update()

print ac2.GetOutput().GetScalarRange()

cone = vtkArrowSource()
cone.SetTipRadius(0.1)
cone.SetTipLength(0.35)
cone.SetShaftRadius(0.03)

glyph = vtkGlyph3D()
glyph.SetInput(ptMask.GetOutput())
glyph.SetSource(cone.GetOutput())
glyph.ScalingOn()
#glyph.SetColorModeToColorByScalar()
#glyph.SetColorModeToColorByScale()
glyph.SetColorModeToColorByVector()
glyph.SetScaleModeToScaleByScalar()
#glyph.SetScaleModeToScaleByVector()
glyph.SetVectorModeToUseVector()
glyph.SetScaleFactor(6)
#glyph.SetIndexModeToVector()
#glyph.SetIndexModeToScalar()
#glyph.SetIndexModeToOff()
glyph.OrientOn()

lut = vtkLookupTable()
lut.SetHueRange(.667,0.0)
lut.Build()

hhogMapper = vtkPolyDataMapper()
hhogMapper.SetInput(glyph.GetOutput())
hhogMapper.SetScalarRange(valuerange)
hhogMapper.SetLookupTable(lut2)
#hhogMapper.SetUseLookupTableScalarRange(0)

hhogActor = vtkActor()
hhogActor.SetMapper(hhogMapper)

ren.AddActor(hhogActor)

scalarBar = vtkScalarBarActor()
scalarBar.SetLookupTable( hhogMapper.GetLookupTable() )
scalarBar.SetTitle("Point scalar value")
scalarBar.SetOrientationToVertical()
scalarBar.GetLabelTextProperty().SetColor(1,1,1)
scalarBar.GetTitleTextProperty().SetColor(1,1,1)
coord = scalarBar.GetPositionCoordinate()
coord.SetCoordinateSystemToNormalizedViewport()
coord.SetValue(0.95,0.5)
scalarBar.SetWidth(.05)
scalarBar.SetHeight(.5)
ren.AddActor( scalarBar )

scalarBar2 = vtkScalarBarActor()
scalarBar2.SetLookupTable(lut4)
scalarBar2.SetTitle("Point scalar value")
scalarBar2.SetOrientationToVertical()
scalarBar2.GetLabelTextProperty().SetColor(1,1,1)
scalarBar2.GetTitleTextProperty().SetColor(1,1,1)
coord2 = scalarBar2.GetPositionCoordinate()
coord2.SetCoordinateSystemToNormalizedViewport()
coord2.SetValue(0.05,0.5)
scalarBar2.SetWidth(.05)
scalarBar2.SetHeight(.5)
ren.AddActor( scalarBar2 )


iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
interactorstyle = iren.GetInteractorStyle()
interactorstyle.SetCurrentStyleToTrackballCamera()


renWin.Render()
iren.Initialize()
iren.Start()


