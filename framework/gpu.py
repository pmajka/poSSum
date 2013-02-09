# An example from scipy cookbook demonstrating the use of numpy arrys in vtk

import vtk
import os,sys
import pos_palette

imread = vtk.vtkStructuredPointsReader()
imread.SetFileName('/home/pmajka/a.vtk')
#imread.SetFileName('/home/pmajka/d.vtk')
#imread.SetFileName('/home/pmajka/z.vtk')
#imread.SetFileName('/home/pmajka/x.vtk')
imread.Update()

cast = vtk.vtkImageCast()
cast.SetInput(imread.GetOutput())
cast.SetOutputScalarTypeToUnsignedChar()
cast.Update()

extract = vtk.vtkExtractVOI()
extract.SetInputConnection(cast.GetOutputPort())
extract.SetVOI(00, 175, 0, 255, 0, 136)
extract.SetSampleRate(1, 1, 1)

class vtk_volume_mapper_wrapper():

    def __init__(self, image_data, use_multichannel_workflow=False):
        self.acf = None
        self.ctf = None
        self.gof = None

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

        if self.use_multichannel_workflow == True:
            self.volume_property.IndependentComponentsOff()

    def _prepare_volume_mapper(self):
        self.volume_mapper.SetSampleDistance(0.05)
        self.volume_mapper.SetInputConnection(self.image_data.GetOutputPort())
        self.volume_mapper.SetBlendModeToComposite()

    def _prepare_volume(self):
        self.volume.SetMapper(self.volume_mapper)
        self.volume.SetProperty(self.volume_property)

    def _load_transfer_functions(self):
        if os.path.isfile(self.acf):
            self.alpha_channel_function = \
                    pos_palette.pos_palette.from_gnuplot_file(self.acf, min=self._min, max=self._max)
        else:
            self.alpha_channel_function = \
                    pos_palette.pos_palette.lib(self.acf, min=self._min, max=self._max)

        if os.path.isfile(self.ctf):
            self.color_transfer_function = \
                    pos_palette.pos_palette.from_gnuplot_file(self.ctf, min=self._min, max=self._max)
        else:
            self.color_transfer_function = \
                    pos_palette.pos_palette.lib(self.ctf, min=self._min, max=self._max)

        if os.path.isfile(self.gof):
            self.gradient_opacity_function = \
                    pos_palette.pos_palette.from_gnuplot_file(self.gof, min=self._min, max=self._max)
        else:
            self.gradient_opacity_function = \
                    pos_palette.pos_palette.lib(self.gof, min=self._min, max=self._max)

    def reload_configuration(self):
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

volume = vtk_volume_mapper_wrapper(extract)
###############################################################################
volume.acf = '/home/pmajka/02_02_NN2_mri_alpha_surface.gpf'
volume.ctf = '/home/pmajka/02_02_NN2_mri_color_surface.gpf'
volume.gof = '/home/pmajka/02_02_NN2_mri_gradient_surface.gpf'
###############################################################################


vol = volume.reload_configuration()

# We add the volume to the renderer ...
renderer.AddVolume(vol)
renderer.SetBackground(1.0, 1.0, 1.0)
renderWin.SetSize(400, 400)


def Keypress(obj, event):
    key = obj.GetKeySym()
    if key.startswith('k'):
        volume.reload_configuration()
        renderWin.Render()


# Tell the application to use the function as an exit check.
renderInteractor.AddObserver("KeyPressEvent", Keypress)

renderInteractor.Initialize()
renderWin.Render()
renderInteractor.Start()
