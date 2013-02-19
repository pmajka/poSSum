import vtk
import os
import sys
import pos_palette
from config import Config

imread = vtk.vtkStructuredPointsReader()
imread.SetFileName('/home/pmajka/mri.vtk')
#imread.SetFileName('/home/pmajka/nietoperz_finished_uchar_small.vtk')
imread.Update()

cast0 = vtk.vtkImageCast()
cast0.SetInput(imread.GetOutput())
cast0.SetOutputScalarTypeToUnsignedChar()
cast0.Update()

extract = vtk.vtkExtractVOI()
extract.SetInputConnection(cast0.GetOutputPort())
extract.SetVOI(0, 175*2, 0, 255*2, 00, 136*2)
extract.SetSampleRate(1, 1, 1)

imread1 = vtk.vtkStructuredPointsReader()
imread1.SetFileName('/home/pmajka/mri.vtk')
imread1.Update()

cast1 = vtk.vtkImageCast()
cast1.SetInput(imread1.GetOutput())
cast1.SetOutputScalarTypeToUnsignedChar()
cast1.Update()

extract1 = vtk.vtkExtractVOI()
extract1.SetInputConnection(cast1.GetOutputPort())
extract1.SetVOI(0, 175*2, 0, 255*2, 00, 136*2)
extract1.SetSampleRate(1, 1, 1)

class vtk_volume_mapper_wrapper():
    """
    vtk_volume_mapper_wrapper(image_data,  use_multichannel_workflow=False)

    """

    def __init__(self, image_data, use_multichannel_workflow=False):
        """
        vtk_volume_mapper_wrapper(image_data,  use_multichannel_workflow=False)
        """
        self.acf = 'grad_ramp_one_to_zero'
        self.ctf = 'grayscale'
        self.gof = 'grad_constant_one'

        self.configuration = None

        self.use_multichannel_workflow = use_multichannel_workflow
        self.alpha_channel_function = None
        self.color_transfer_function = None
        self.gradient_opacity_function = None

        self.image_data = image_data

        self._min, self._max = (0, 255)

        self.volume_property = vtk.vtkVolumeProperty()
        self.volume_mapper = vtk.vtkFixedPointVolumeRayCastMapper()
        self.volume = vtk.vtkVolume()

    def _prepare_volume_property(self):
        print self.alpha_channel_function.piecewise_function().GetRange()
        self.volume_property.SetColor(self.color_transfer_function.color_transfer_function())
        self.volume_property.SetScalarOpacity(self.alpha_channel_function.piecewise_function())
        self.volume_property.SetGradientOpacity(self.gradient_opacity_function.piecewise_function())
        self.volume_property.SetInterpolationTypeToLinear()
        #self.volume_property.ShadeOn()
        print self.volume_property.GetShade()

        if self.use_multichannel_workflow == True:
            self.volume_property.IndependentComponentsOff()

        if self.volume_property.ShadeOn():
            self.volume_property.SetDiffuse(0.5)
            self.volume_property.SetSpecular(0.5)
            self.volume_property.SetAmbient(0.5)
            self.volume_property.SetSpecularPower(0.5)

    def _prepare_volume_mapper(self):
        self.volume_mapper.SetInputConnection(self.image_data.GetOutputPort())
        self.volume_mapper.SetSampleDistance(0.01)
        self.volume_mapper.SetBlendModeToComposite()

    def _prepare_volume(self):
        self.volume.SetMapper(self.volume_mapper)
        self.volume.SetProperty(self.volume_property)

    def _load_transfer_functions(self):
        self.alpha_channel_function = pos_palette.pos_palette.get(self.acf, min=self._min, max=self._max)
        self.color_transfer_function = pos_palette.pos_palette.get(self.ctf, min=self._min, max=self._max)
        self.gradient_opacity_function = pos_palette.pos_palette.get(self.gof, min=self._min, max=self._max)

    def reload_configuration(self):
        self._load_transfer_functions()
        self._prepare_volume_property()
        self._prepare_volume_mapper()
        self._prepare_volume()

        return self.volume

# With almost everything else ready, its time to initialize the renderer and window, as well as creating a method for exiting the application
renderer = vtk.vtkRenderer()
renderer1 = vtk.vtkRenderer()

renderWin = vtk.vtkRenderWindow()
renderWin.AddRenderer(renderer)
renderWin.AddRenderer(renderer1)

renderer.SetViewport(0.0, 0.0, 0.5, 1.0)
renderer1.SetViewport(0.5, 0.0, 1.0, 1.0)

renderInteractor = vtk.vtkRenderWindowInteractor()
renderInteractor.SetRenderWindow(renderWin)

renderer.GetCullers().InitTraversal()
culler = renderer.GetCullers().GetNextItem()
culler.SetSortingStyleToBackToFront()

volume = vtk_volume_mapper_wrapper(extract)
###############################################################################
volume.acf = 'grad_ramp_one_to_zero'
volume.ctf = 'bb'
volume.gof = 'grad_constant_one'
#volume.acf = '/home/pmajka/bat_alpha.gpf'
#volume.ctf = '/home/pmajka/bat_color.gpf'
#volume.gof = '/home/pmajka/bat_gradient.gpf'
###############################################################################
#volume1 = vtk_volume_mapper_wrapper(extract1, True)
#volume1.acf = '/home/pmajka/02_02_NN2_myelin_alpha_surface.gpf'
#volume1.ctf = '/home/pmajka/02_02_NN2_mri_color_surface.gpf'
#volume1.gof = '/home/pmajka/02_02_NN2_myelin_gradient_surface.gpf'

vol = volume.reload_configuration()
#vol1 = volume1.reload_configuration()

lightKit=vtk.vtkLightKit()
lightKit.AddLightsToRenderer(renderer)
lightKit.MaintainLuminanceOn()
lightKit.SetKeyLightIntensity(1.0)

lightKit.SetKeyLightWarmth(0.65)
lightKit.SetFillLightWarmth(0.6)
try :
    lightKit.SetHeadLightWarmth(0.45)
except :
    lightKit.SetHeadlightWarmth(0.45)

lightKit.SetKeyToFillRatio(2.)
lightKit.SetKeyToHeadRatio(7.)
lightKit.SetKeyToBackRatio(1000.)

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
axes.SetNormalizedLabelPosition(.5, .5, .5)

orientation_widget = vtk.vtkOrientationMarkerWidget()
orientation_widget.SetOrientationMarker(cube)
orientation_widget.SetViewport(0.85,0.85,1.0,1.0)
#orientation_widget.SetOrientationMarker(axes)
orientation_widget.SetInteractor(renderInteractor)
orientation_widget.SetEnabled(1)
orientation_widget.On()
orientation_widget.InteractiveOff()


renderer1.SetActiveCamera(renderer.GetActiveCamera())

# We add the volume to the renderer ...
#renderer1.AddVolume(vol1)
renderer.AddVolume(vol)
renderer.SetBackground(1.0, 1.0, 1.0)
renderWin.SetSize(400, 400)


def Keypress(obj, event):
    key = obj.GetKeySym()
    if key.startswith('k'):
        volume.reload_configuration()
        #volume1.reload_configuration()
        renderWin.Render()

# Tell the application to use the function as an exit check.
renderInteractor.AddObserver("KeyPressEvent", Keypress)

renderWin.Render()
renderInteractor.Initialize()
renderInteractor.Start()

for i in range(0):
    renderer.GetActiveCamera().Azimuth(1)
    renderer.ResetCameraClippingRange()
    renderWin.Render()
