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
renWin.AddRenderer(ren)

ia = vtkImageActor()
ia.SetInput(cast.GetOutput())
ren.AddActor(ia)

reader = vtkStructuredPointsReader()
reader.SetFileName('/home/pmajka/0160.vtk')
reader.Update()
valuerange = reader.GetOutput().GetScalarRange()
print "valuerange",valuerange


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
#ac2.SetFunction("sqrt(u*u+v*v)")
ac2.Update()

lut2 = vtkLookupTable()
lut2.SetRange(ac2.GetOutput().GetScalarRange())
lut2.SetValueRange(0.0, 1.0) 
lut2.SetSaturationRange(0.0, 0.0)
lut2.SetRampToLinear()
lut2.Build()

print ac2.GetOutput().GetScalarRange()
dataMapper = vtkDataSetMapper()
dataMapper.SetInput(ac2.GetOutput())
dataMapper.SetScalarRange(ac2.GetOutput().GetScalarRange())
#dataMapper.SetScalarRange(0,11)
dataMapper.SetLookupTable(lut2)

dataActor = vtkLODActor()
dataActor.GetProperty().SetOpacity(1.0)
dataActor.SetMapper(dataMapper)
ren.AddActor(dataActor)


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
glyph.SetColorModeToColorByScalar()
#glyph.SetColorModeToColorByScale()
#glyph.SetColorModeToColorByVector()
#glyph.SetScaleModeToScaleByScalar()
glyph.SetScaleModeToScaleByVector()
glyph.SetVectorModeToUseVector()
glyph.SetScaleFactor(5)
glyph.SetIndexModeToVector()
#glyph.OrientOn()

lut = vtkLookupTable()
lut.SetHueRange(.667,0.0)
lut.Build()

hhogMapper = vtkPolyDataMapper()
hhogMapper.SetInput(glyph.GetOutput())
hhogMapper.SetScalarRange(valuerange)
hhogMapper.SetLookupTable(lut)
hhogMapper.SetUseLookupTableScalarRange(0)

hhogActor = vtkActor()
hhogActor.SetMapper(hhogMapper)

ren.AddActor(hhogActor)

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
interactorstyle = iren.GetInteractorStyle()
interactorstyle.SetCurrentStyleToTrackballCamera()

renWin.Render()
iren.Initialize()
iren.Start()
