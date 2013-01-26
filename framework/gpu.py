# An example from scipy cookbook demonstrating the use of numpy arrys in vtk

import vtk

imread = vtk.vtkStructuredPointsReader()
imread.SetFileName('/home/pmajka/a.vtk')
imread.Update()

cast = vtk.vtkImageCast();
cast.SetInput(imread.GetOutput())
cast.SetOutputScalarTypeToUnsignedChar()
cast.Update()


#def ShowOrientationCube(interactor):
#	print "ORIENTATION CUBE!"




# The following class is used to store transparencyv-values for later retrival. In our case, we want the value 0 to be
# completly opaque whereas the three different cubes are given different transperancy-values to show how it works.
alphaChannelFunc = vtk.vtkPiecewiseFunction()
#   alphaChannelFunc.AddPoint(0, 0.0)
#   alphaChannelFunc.AddPoint(1, 0.0)
#   alphaChannelFunc.AddPoint(2, 0.9)
#   alphaChannelFunc.AddPoint(7, 1.0)
alphaChannelFunc.AddPoint(128, 0.5)
alphaChannelFunc.AddPoint(153, 0.0)
alphaChannelFunc.AddPoint(255, 0.0)

# This class stores color data and can create color tables from a few color points. For this demo, we want the three cubes
# to be of the colors red green and blue.
colorFunc = vtk.vtkColorTransferFunction()
#   colorFunc.AddRGBPoint(00, 0.0, 0.0, 0.0)
#   colorFunc.AddRGBPoint(1, 1.0, 0.0, 0.0)
#   colorFunc.AddRGBPoint(7, 0.0, 1.0, 0.0)
colorFunc.AddRGBPoint(01, 0.0, 0.0, 0.0)
colorFunc.AddRGBPoint(128, 0.5, 0.5, 0.5)
colorFunc.AddRGBPoint(255, 1.0, 1.0, 1.0)

# The preavius two classes stored properties. Because we want to apply these properties to the volume we want to render,
# we have to store them in a class that stores volume prpoperties.
volumeProperty = vtk.vtkVolumeProperty()
volumeProperty.SetColor(colorFunc)
volumeProperty.SetScalarOpacity(alphaChannelFunc)
volumeProperty.SetInterpolationTypeToLinear()
#volumeProperty.ShadeOn()

# This class describes how the volume is rendered (through ray tracing).
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
#compositeFunction = vtk.vtkVolumeRayCastIsosurfaceFunction()
#compositeFunction.SetIsoValue(80)

# We can finally create our volume. We also have to specify the data for it, as well as how the data will be rendered.
volumeMapper = vtk.vtkVolumeRayCastMapper()
volumeMapper.SetSampleDistance(0.05)
#volumeMapper = vtk.vtkSmartVolumeMapper()
#volumeMapper= vtk.vtkFixedPointVolumeRayCastMapper()
volumeMapper.SetVolumeRayCastFunction(compositeFunction)
volumeMapper.SetInputConnection(cast.GetOutputPort())

# The class vtkVolume is used to pair the preaviusly declared volume as well as the properties to be used when rendering that volume.
volume = vtk.vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volumeProperty)

# With almost everything else ready, its time to initialize the renderer and window, as well as creating a method for exiting the application
renderer = vtk.vtkRenderer()
renderWin = vtk.vtkRenderWindow()
renderWin.AddRenderer(renderer)
renderInteractor = vtk.vtkRenderWindowInteractor()
renderInteractor.SetRenderWindow(renderWin)

# We add the volume to the renderer ...
renderer.AddVolume(volume)
# ... set background color to white ...
renderer.SetBackground(1.0,1.0,1.0)
# ... and set window size.
renderWin.SetSize(400, 400)

# A simple function to be called when the user decides to quit the application.
def exitCheck(obj, event):
    if obj.GetEventPending() != 0:
        obj.SetAbortRender(1)

# Tell the application to use the function as an exit check.
renderWin.AddObserver("AbortCheckEvent", exitCheck)


cube = vtk.vtkAnnotatedCubeActor()
cube.GetXMinusFaceProperty().SetColor(1,0,0)
cube.GetXPlusFaceProperty().SetColor(1,0,0)
cube.GetYMinusFaceProperty().SetColor(0,1,0)
cube.GetYPlusFaceProperty().SetColor(0,1,0)
cube.GetZMinusFaceProperty().SetColor(0,0,1)
cube.GetZPlusFaceProperty().SetColor(0,0,1)
cube.GetTextEdgesProperty().SetColor(0,0,0)

# anatomic labelling
cube.SetXPlusFaceText ("R")
cube.SetXMinusFaceText("L")
cube.SetYPlusFaceText ("A")
cube.SetYMinusFaceText("P")
cube.SetZPlusFaceText ("S")
cube.SetZMinusFaceText("I")

axes = vtk.vtkAxesActor()
axes.SetShaftTypeToCylinder()
axes.SetTipTypeToCone()
axes.SetXAxisLabelText("X")
axes.SetYAxisLabelText("Y")
axes.SetZAxisLabelText("Z")
#axes.SetNormalizedLabelPosition(.5, .5, .5)

orientation_widget = vtk.vtkOrientationMarkerWidget()
orientation_widget.SetOrientationMarker(cube)
orientation_widget.SetViewport(0.85,0.85,1.0,1.0)
#orientation_widget.SetOrientationMarker(axes)
orientation_widget.SetInteractor(renderInteractor)
orientation_widget.SetEnabled(1)
orientation_widget.On()
orientation_widget.InteractiveOff()


renderInteractor.Initialize()
# Because nothing will be rendered without any input, we order the first render manually before control is handed over to the main-loop.
renderWin.Render()
renderInteractor.Start()
