import vtk
import os
import sys
import math
import pos_palette
from config import Config

class vtk_volume_image_reader():
    def __init__(self, filename, configuration_file, reader_name):
        self._configuration_filename = configuration_file
        self._reader_name = reader_name
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

        flip = [0,0,0] # A stub

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

        attrmap = self.cfg[self._reader_name]['permute_image']
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

    def __init__(self, image_data, configuration_file, reader_name):
        """
        vtk_volume_mapper_wrapper(image_data,configuration_file)
        """

        self._configuration_filename = configuration_file
        self._reader_name = reader_name
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
            setattr(self, attr, self.cfg[self._reader_name][attr])

    def _prepare_volume_property(self):
        self.volume_property.SetColor(self.color_transfer_function.color_transfer_function())
        self.volume_property.SetScalarOpacity(self.alpha_channel_function.piecewise_function())
        self.volume_property.SetGradientOpacity(self.gradient_opacity_function.piecewise_function())

        # Just an alias:
        attrmap = self.cfg[self._reader_name]['volume_property']
        for attr, val in attrmap.iteritems():
            getattr(self.volume_property, attr)(val)
            print  attr, val

        print self.volume_property.GetShade()
        if self.volume_property.GetShade():
            # Just an alias:
            attrmap = self.cfg[self._reader_name]['volume_property_shading']
            for attr, val in attrmap.iteritems():
                getattr(self.volume_property, attr)(val)
                print attr, val

        if self.use_multichannel_workflow == True:
            self.volume_property.IndependentComponentsOff()

    def _prepare_volume_mapper(self):
        self.volume_mapper.SetInput(self.image_data)
        self.volume_mapper.SetBlendModeToComposite()

        attrmap = self.cfg[self._reader_name]['volume_mapper']
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

class vtk_oblique_slice_mapper():
    def __init__(self, image, interactor):
        pass
        self.plane = vtk.vtkPlane()
        self.plane_widget = vtk.vtkImplicitPlaneWidget()
        self.plane_widget.SetInteractor(interactor)
        self.plane_widget.SetPlaceFactor(1)
        self.plane_widget.SetInput(image)
        self.plane_widget.PlaceWidget()
#       self.plane_widget.AddObserver("InteractionEvent", self.myCallback)
        self.plane_widget.DrawPlaneOff()
        self.plane_widget.SetOrigin(3.469, 12.37, 6.425)
        self.plane_widget.SetNormalToXAxis(1)
        self.plane_widget.OutlineTranslationOff()

        self.transform = vtk.vtkTransform()
        self.transform.PostMultiply()
        self.plane.SetOrigin(3.469, 12.37, 6.425)
        self.plane.SetTransform(self.transform)

        self._resample = vtk.vtkImageResample()
        self._resample.SetAxisMagnificationFactor(0,0.2)
        self._resample.SetAxisMagnificationFactor(1,0.2)
        self._resample.SetAxisMagnificationFactor(2,0.2)
        self._resample.SetInterpolationModeToCubic()
        self._resample.SetInput(image)

        planeCut = vtk.vtkCutter()
        planeCut.SetInput(self._resample.GetOutput())
        planeCut.SetCutFunction(self.plane)
        cutMapper = vtk.vtkPolyDataMapper()
        cutMapper.SetInputConnection(planeCut.GetOutputPort())

        self.cutActor = vtk.vtkActor()
        self.cutActor.SetMapper(cutMapper)
        self.cutActor.VisibilityOn()
        self.plane_widget.GetPlane(self.plane)

#       self.transform.Translate(*tuple(map(lambda x: -1*x, self.plane.GetOrigin())))
#       self.transform.RotateY(-45)
#       self.transform.Translate(*self.plane.GetOrigin())
        planeCut.Update()

    def reload_configuration(self):
        return self.cutActor

    def myCallback(self, obj, event):
        obj.GetPlane(self.plane)
        self.cutActor.VisibilityOn()

class vtk_single_renderer_scene():
    def __init__(self, configuration_file):
        self._configuration_filename = configuration_file

        self._renderer = vtk.vtkRenderer()
        self._renderer2 = vtk.vtkRenderer()
        self._renderer3 = vtk.vtkRenderer()
        self._renderer4 = vtk.vtkRenderer()

        self._renderer.SetViewport(   0, 0,   0.5, 0.5)
        self._renderer2.SetViewport(  0.5, 0,  1.0, 0.5)
        self._renderer3.SetViewport(0.5, 0.5, 1  ,   1)
        self._renderer4.SetViewport(0, 0.5,   0.5,   1.0)

        self._render_win = vtk.vtkRenderWindow()
        self._render_interactor = vtk.vtkRenderWindowInteractor()

    def _load_config_file(self):
        self.cfg = Config(file(self._configuration_filename))

    def _prepare_rendering_env(self):
        self._render_win.AddRenderer(self._renderer)
        self._render_win.AddRenderer(self._renderer2)
        self._render_win.AddRenderer(self._renderer3)
        self._render_win.AddRenderer(self._renderer4)
        self._render_interactor.SetRenderWindow(self._render_win)

        self._renderer.GetCullers().InitTraversal()
        culler = self._renderer.GetCullers().GetNextItem()
        culler.SetSortingStyleToBackToFront()

        self._renderer2.GetCullers().InitTraversal()
        culler = self._renderer2.GetCullers().GetNextItem()
        culler.SetSortingStyleToBackToFront()

        self._renderer3.GetCullers().InitTraversal()
        culler = self._renderer3.GetCullers().GetNextItem()
        culler.SetSortingStyleToBackToFront()

        self._renderer4.GetCullers().InitTraversal()
        culler = self._renderer4.GetCullers().GetNextItem()
        culler.SetSortingStyleToBackToFront()

        if self.cfg['scene']['general_settings']['use_light_kit']:
            self.light_kit = vtk_light_kit(self._configuration_filename)
            self.light_kit.light_kit.AddLightsToRenderer(self._renderer)
            self.light_kit.light_kit.AddLightsToRenderer(self._renderer2)
            self.light_kit.light_kit.AddLightsToRenderer(self._renderer3)
            self.light_kit.light_kit.AddLightsToRenderer(self._renderer4)

        if self.cfg['scene']['general_settings']['use_orientation_marker']:
            self.orientation_widget = vtk_orientation_marker(self._configuration_filename)
            self.orientation_widget.orientation_widget.SetInteractor(self._render_interactor)
            self.orientation_widget.after_setting_interactor()

    def _prepare_renderer(self):
        self._renderer.SetBackground(1.0, 1.0, 1.0)
        self._renderer2.SetBackground(1.0, 1.0, 1.0)
        self._renderer3.SetBackground(1.0, 1.0, 1.0)
        self._renderer4.SetBackground(1.0, 1.0, 1.0)

    def _prepare_render_window(self):
        self._render_win.SetSize(1200, 800)

    def _prepare_camera(self):
        self._camera = self._renderer.GetActiveCamera()
        self._renderer2.SetActiveCamera(self._camera)
        self._renderer3.SetActiveCamera(self._camera)
        self._renderer4.SetActiveCamera(self._camera)

        if self.cfg['scene']['general_settings']['use_manual_camera']:
            attrmap = self.cfg['scene']['camera_settings']['manual']
            for attr, val in attrmap.iteritems():
                try:
                    getattr(self._camera, attr)(*tuple(val))
                except TypeError:
                    getattr(self._camera, attr)(val)
            self._camera.ParallelProjectionOn()
            self._renderer.ResetCameraClippingRange()
            self._renderer2.ResetCameraClippingRange()
            self._renderer3.ResetCameraClippingRange()
            self._renderer4.ResetCameraClippingRange()

    def _take_screenshot(self):
        template_dictionary = {
            'pid' : os.getpid(),
            'timestep' : self._global_time,
            'screenshot_idx' : self._screenshot_index
        }

        filename_template = \
                self.cfg['scene']['screenshots_settings']['screenshot_template']
        magnification = \
                self.cfg['scene']['screenshots_settings']['SetMagnification']

        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetMagnification(magnification)
        w2i.SetInput(self._render_win)
        w2i.Update()

        writer = vtk.vtkPNGWriter()
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.SetFileName(filename_template.format(**template_dictionary))
        writer.Write()

        self._screenshot_index += 1

    def _prepare_render_interactor(self):
        vtk.vtkInteractorStyleTrackballCamera()
        self._render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    def add_actors(self):
        volume_filename = '/home/pmajka/myelin_rgb.vtk'
        volume_filename2 = '/home/pmajka/nissl_rgb.vtk'
        volume_filename3 = '/home/pmajka/mri.vtk'
        volume_filename4 = '/home/pmajka/blockface_rgb.vtk'

        self.reader = vtk_volume_image_reader( \
                   volume_filename, self._configuration_filename, 'myelin_reader')

        self.reader2 = vtk_volume_image_reader( \
                   volume_filename2, self._configuration_filename, 'nissl_reader')

        self.reader3 = vtk_volume_image_reader( \
                   volume_filename3, self._configuration_filename, 'mri_reader')

        self.reader4 = vtk_volume_image_reader( \
                   volume_filename4, self._configuration_filename, 'blockface_reader')

        self.volume = vtk_volume_mapper_wrapper( \
                self.reader.reload_configuration().GetOutput(), self._configuration_filename,\
                'myelin_volume')
        self._renderer.AddVolume(self.volume.reload_configuration())

        self.volume2 = vtk_volume_mapper_wrapper( \
                self.reader2.reload_configuration().GetOutput(), self._configuration_filename,\
                'nissl_volume')
        self._renderer2.AddVolume(self.volume2.reload_configuration())

        self.volume3 = vtk_volume_mapper_wrapper( \
                self.reader3.reload_configuration().GetOutput(), self._configuration_filename,\
                'mri_volume')
        self._renderer3.AddVolume(self.volume3.reload_configuration())

        self.volume4 = vtk_volume_mapper_wrapper( \
                self.reader4.reload_configuration().GetOutput(), self._configuration_filename,\
                'blockface_volume')
        self._renderer4.AddVolume(self.volume4.reload_configuration())

       #self._cut = vtk_oblique_slice_mapper( \
       #        self.reader.reload_configuration().GetOutput(),\
       #        self._render_interactor)

       #self._cutActor = self._cut.reload_configuration()
       #self._renderer.AddActor(self._cutActor)

    def _assign_events(self):
        pass
        self._render_interactor.AddObserver("KeyPressEvent", self.key_press_dispather)
#       self._cut.plane_widget.AddObserver("InteractionEvent", self._cut.myCallback)

    def _reload_configuration(self):
        self.volume.image_data = self.reader.reload_configuration().GetOutput()
        self.volume.reload_configuration()

    def start(self):
        self._load_config_file()
        self._prepare_rendering_env()
        self._prepare_renderer()
        self._prepare_render_window()
        self._prepare_camera()
        self._prepare_render_interactor()
        self.add_actors()
        self._assign_events()

        self._render_win.Render()
        self._renderer.ResetCamera()
        self._pre_animate()
        self._render_win.Render()

        self._render_interactor.Initialize()
        self._render_interactor.Start()

        self.animate()

    def _pre_animate(self):
        # Initialize global timer and screenshot iterator
        self._global_time = 0
        self._screenshot_index=0

        # Setup initial camera location
        self._camera.Azimuth(90)
        self._camera.Zoom(2.0)
        pass

    def animate(self):

        for i in range(576):
            if i < 360:
                self._camera.Azimuth(1)
            elif 360 <= i < 400:
                pass
            else:
                self.reader._extract.SetVOI(i-400,350, 0, 1250, 0, 1136)
                self.reader2._extract.SetVOI(i-400,350, 0, 1250, 0, 1136)
                self.reader3._extract.SetVOI(i-400,350, 0, 1250, 0, 1136)
                self.reader4._extract.SetVOI(i-400,350, 0, 1250, 0, 1136)

            self._render_win.Render()
            self._global_time += 1
            self._take_screenshot()

    def key_press_dispather(self, obj, event):
        key = obj.GetKeySym()
        if key.startswith('k'):

            self._reload_configuration()

            try:
                self.light_kit.reload_configuration()
            except:
                pass

            try:
                self.orientation_widget.reload_configuration()
            except:
                pass
        if key.startswith('s'):
            self._take_screenshot()

        self._render_win.Render()

if __name__ == '__main__':
    app = vtk_single_renderer_scene('multiple_rgb.cfg')
    app.start()
