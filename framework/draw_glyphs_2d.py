from vtk import*


def get_scalar_bar(lut = None):
    titleProp = vtkTextProperty()
    titleProp.SetColor(0,0,0)
    titleProp.SetFontFamily(VTK_ARIAL)
    titleProp.SetFontSize(18)
    titleProp.SetBold(0.5)
    
    scalarBar = vtkScalarBarActor()
#    scalarBar.SetLookupTable(lut)
    scalarBar.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
    scalarBar.GetPositionCoordinate().SetValue(0.1,0.01)
    scalarBar.SetOrientationToHorizontal()
    scalarBar.SetWidth(0.8)
    scalarBar.SetHeight(0.12)
    scalarBar.SetTitle("Intensity")
    scalarBar.GetLabelTextProperty().SetColor(1,1, 1)
    scalarBar.SetTitleTextProperty(titleProp)
    return scalarBar

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

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
interactorstyle = iren.GetInteractorStyle()
interactorstyle.SetCurrentStyleToTrackballCamera()

renWin.Render()
iren.Initialize()
iren.Start()
