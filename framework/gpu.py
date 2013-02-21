import vtk
import os
import sys
import pos_palette
from config import Config

class vtk_volume_image_reader():
    def __init__(self, filename, configuration_file):
        self._configuration_filename = configuration_file
        self._image_filename = filename

    def _load_config_file(self):
        self.cfg = Config(file(self._configuration_filename))
        print self.cfg

    def _prepare_reader(self):
        self._reader = vtk.vtkStructuredPointsReader()
        self._reader.SetFileName(self._image_filename)
        self._reader.Update()

    def _prepare_image_cast(self):
        self._cast = vtk.vtkImageCast()
        self._cast.SetInput(self._reader.GetOutput())
        self._cast.SetOutputScalarTypeToUnsignedChar()

        attrmap = self.cfg['mri_reader']['cast_image']
        for attr, val in attrmap.iteritems():
            getattr(self._cast, attr)(val)

        self._cast.Update()

    def _prepare_voi(self):
        self._extract = vtk.vtkExtractVOI()
        self._extract.SetInputConnection(self._cast.GetOutputPort())

        attrmap = self.cfg['mri_reader']['extract_voi']
        for attr, val in attrmap.iteritems():
            getattr(self._extract, attr)(*tuple(val))

        self._extract.Update()

    def _prepare_flip(self):
        f = self.cfg['mri_reader']['flip_image']['flip_xyz']
        o = self.cfg['mri_reader']['flip_image']['origin_xyz']

        flip = [0,0,0] # A stup

        self._flip_output = self._permute

        for i in range(3):
            if f[i]:
                flip[i] = vtk.vtkImageFlip()
                flip[i].SetInputConnection(self._flip_output.GetOutputPort())
                flip[i].SetFilteredAxis(i)
                if o[i]:
                    flip[i].FlipAboutOriginOn()
                self._flip_output = flip[i]
                self._flip_output.Update()

    def _prepare_permute(self):
        self._permute = vtk.vtkImagePermute()
        self._permute.SetInputConnection(self._extract.GetOutputPort())

        attrmap = self.cfg['mri_reader']['permute_image']
        for attr, val in attrmap.iteritems():
            getattr(self._permute, attr)(*tuple(val))

    def reload_configuration(self):
        self._load_config_file()
        self._prepare_reader()
        self._prepare_image_cast()
        self._prepare_voi()
        self._prepare_permute()
        self._prepare_flip()

        return self._flip_output

class vtk_light_kit():
    def __init__(self, configuration_file):
        self._configuration_filename = configuration_file
        self.light_kit = vtk.vtkLightKit()

        self.reload_configuration()

    def _load_config_file(self):
        self.cfg = Config(file(self._configuration_filename))

        attrmap = self.cfg['scene']['scene_lightning']
        for attr, val in attrmap.iteritems():
            getattr(self.light_kit, attr)(val)

    def _prepare_light_kit(self):
        self.light_kit.MaintainLuminanceOn()

    def reload_configuration(self):
        self._load_config_file()
        self._prepare_light_kit()

class vtk_orientation_marker():
    def __init__(self, configuration_file):
        self._configuration_filename = configuration_file
        self._annotated_cube = vtk.vtkAnnotatedCubeActor()
        self.orientation_widget = vtk.vtkOrientationMarkerWidget()

        self.reload_configuration()

    def _load_config_file(self):
        self.cfg = Config(file(self._configuration_filename))

    def _prepare_annotated_cube(self):
        attrmap = self.cfg['scene']['orientation_marker']['colors']
        for attr, val in attrmap.iteritems():
            getattr(self._annotated_cube, attr)().SetColor(*tuple(val))

        attrmap = self.cfg['scene']['orientation_marker']['face_text']
        for attr, val in attrmap.iteritems():
            getattr(self._annotated_cube, attr)(val)

    def _prepare_orientation_marker(self):
        self.orientation_widget.SetOrientationMarker(self._annotated_cube)

        attrmap = self.cfg['scene']['orientation_marker']['marker']
        for attr, val in attrmap.iteritems():
            getattr(self.orientation_widget, attr)(*tuple(val))

    def reload_configuration(self):
        self._load_config_file()
        self._prepare_annotated_cube()
        self._prepare_orientation_marker()

    def after_setting_interactor(self):
        self.orientation_widget.SetEnabled(1)
        self.orientation_widget.On()
        self.orientation_widget.InteractiveOff()

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
        self.volume_mapper.SetInput(self.image_data)
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

class vtk_single_renderer_scene():
    pass

# With almost everything else ready, its time to initialize the renderer and window, as well as creating a method for exiting the application
renderer = vtk.vtkRenderer()
renderWin = vtk.vtkRenderWindow()
renderWin.AddRenderer(renderer)
renderInteractor = vtk.vtkRenderWindowInteractor()
renderInteractor.SetRenderWindow(renderWin)

renderer.GetCullers().InitTraversal()
culler = renderer.GetCullers().GetNextItem()
culler.SetSortingStyleToBackToFront()

r = vtk_volume_image_reader('/home/pmajka/mri.vtk', 'a.cfg')

volume = vtk_volume_mapper_wrapper(r.reload_configuration().GetOutput(), 'a.cfg')
vol = volume.reload_configuration()

light_kit = vtk_light_kit('a.cfg')
light_kit.light_kit.AddLightsToRenderer(renderer)

orientation_widget = vtk_orientation_marker('a.cfg')
orientation_widget.orientation_widget.SetInteractor(renderInteractor)
orientation_widget.after_setting_interactor()


# We add the volume to the renderer ...
renderer.AddVolume(vol)
renderer.SetBackground(1.0, 1.0, 1.0)
renderWin.SetSize(400, 400)

def Keypress(obj, event):
    key = obj.GetKeySym()
    if key.startswith('k'):
        volume.image_data = r.reload_configuration().GetOutput()
        volume.reload_configuration()
        light_kit.reload_configuration()
        orientation_widget.reload_configuration()
        renderWin.Render()

# Tell the application to use the function as an exit check.
renderInteractor.AddObserver("KeyPressEvent", Keypress)

renderWin.Render()
renderInteractor.Initialize()
renderInteractor.Start()

for i in range(20):
    #renderer.GetActiveCamera().Azimuth(1)
    r._extract.SetVOI(0, 175, 0, 10*i, 00, 136)
    #renderer.ResetCameraClippingRange()
    renderWin.Render()
