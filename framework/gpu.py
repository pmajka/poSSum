import vtk
import os
import sys
import pos_palette
from config import Config

imread = vtk.vtkStructuredPointsReader()
imread.SetFileName('/home/pmajka/mri.vtk')
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

class vtk_volume_image_reader():
    def __init__(self, filename, configuration_file):
        self._configuration_filename = configuration_file

    def _load_config_file(self):
        self.cfg = Config(file(self._configuration_filename))
        print self.cfg
        for attr in ['acf', 'ctf', 'gof', 'use_multichannel_workflow','_min','_max']:
            setattr(self, attr, self.cfg['mri_volume'][attr])

    def _prepare_reader(self):
        pass

    def _prepare_image_cast(self):
        pass

    def _prepare_volume_subset(self):
        pass

    def _prepare_flip(self):
        pass

    def reload_configuration(self):
        self._load_config_file()
        self._load_transfer_functions()
        self._prepare_volume_property()
        self._prepare_volume_mapper()
        self._prepare_volume()


class vtk_light_kit():
    def __init__(self, configuration_file):
        self._configuration_filename = configuration_file
        self.light_kit = vtk.vtkLightKit()

        self.reload_configuration()

    def _load_config_file(self):
        self.cfg = Config(file(self._configuration_filename))
        print self.cfg

        attrmap = self.cfg['scene']['scene_lightning']
        for attr, val in attrmap.iteritems():
            getattr(self.light_kit, attr)(val)

    def _prepare_light_kit(self):
        self.light_kit.MaintainLuminanceOn()

    def reload_configuration(self):
        self._load_config_file()
        self._prepare_light_kit()


class vtk_volume_mapper_wrapper():
    """
    vtk_volume_mapper_wrapper(image_data,  use_multichannel_workflow=False)
    """

    def __init__(self, image_data, configuration_file):
        """
        vtk_volume_mapper_wrapper(image_data,configuration_file)
        """

        self._configuration_filename = configuration_file
        self._load_config_file()
        self.image_data = image_data

        self.alpha_channel_function = None
        self.color_transfer_function = None
        self.gradient_opacity_function = None

        self.volume_property = vtk.vtkVolumeProperty()
        self.volume_mapper = vtk.vtkFixedPointVolumeRayCastMapper()
        self.volume = vtk.vtkVolume()

    def _load_config_file(self):
        self.cfg = Config(file(self._configuration_filename))
        print self.cfg
        for attr in ['acf', 'ctf', 'gof', 'use_multichannel_workflow','_min','_max']:
            setattr(self, attr, self.cfg['mri_volume'][attr])

    def _prepare_volume_property(self):
        self.volume_property.SetColor(self.color_transfer_function.color_transfer_function())
        self.volume_property.SetScalarOpacity(self.alpha_channel_function.piecewise_function())
        self.volume_property.SetGradientOpacity(self.gradient_opacity_function.piecewise_function())

        # Just an alias:
        attrmap = self.cfg['mri_volume']['volume_property']
        for attr, val in attrmap.iteritems():
            getattr(self.volume_property, attr)(val)
            print  attr, val

        print self.volume_property.GetShade()
        if self.volume_property.GetShade():
            # Just an alias:
            attrmap = self.cfg['mri_volume']['volume_property_shading']
            for attr, val in attrmap.iteritems():
                getattr(self.volume_property, attr)(val)
                print attr, val

        if self.use_multichannel_workflow == True:
            self.volume_property.IndependentComponentsOff()

    def _prepare_volume_mapper(self):
        self.volume_mapper.SetInputConnection(self.image_data.GetOutputPort())
        self.volume_mapper.SetBlendModeToComposite()

        attrmap = self.cfg['mri_volume']['volume_mapper']
        for attr, val in attrmap.iteritems():
            getattr(self.volume_mapper, attr)(val)

    def _prepare_volume(self):
        self.volume.SetMapper(self.volume_mapper)
        self.volume.SetProperty(self.volume_property)

    def _load_transfer_functions(self):
        self.alpha_channel_function = pos_palette.pos_palette.get(self.acf, min=self._min, max=self._max)
        self.color_transfer_function = pos_palette.pos_palette.get(self.ctf, min=self._min, max=self._max)
        self.gradient_opacity_function = pos_palette.pos_palette.get(self.gof, min=self._min, max=self._max)

    def reload_configuration(self):
        self._load_config_file()
        self._load_transfer_functions()
        self._prepare_volume_property()
        self._prepare_volume_mapper()
        self._prepare_volume()

        return self.volume

# With almost everything else ready, its time to initialize the renderer and window, as well as creating a method for exiting the application
renderer = vtk.vtkRenderer()

renderWin = vtk.vtkRenderWindow()
renderWin.AddRenderer(renderer)

renderInteractor = vtk.vtkRenderWindowInteractor()
renderInteractor.SetRenderWindow(renderWin)

renderer.GetCullers().InitTraversal()
culler = renderer.GetCullers().GetNextItem()
culler.SetSortingStyleToBackToFront()

volume = vtk_volume_mapper_wrapper(extract, 'a.cfg')
###############################################################################
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

light_kit = vtk_light_kit('a.cfg')
light_kit.light_kit.AddLightsToRenderer(renderer)

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

# We add the volume to the renderer ...
renderer.AddVolume(vol)
renderer.SetBackground(1.0, 1.0, 1.0)
renderWin.SetSize(400, 400)

def Keypress(obj, event):
    key = obj.GetKeySym()
    if key.startswith('k'):
        volume.reload_configuration()
        light_kit.reload_configuration()
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
