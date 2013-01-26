import vtk
import sys
import numpy as np

def array2vtk(a):
    """ Build a vtkfloatarray from a numpy array"""
    data = a.astype('f').tostring() # hold on to the _data attribute, vtk uses this reference
    vtkt = vtk.vtkFloatArray()
    vtkt.SetNumberOfTuples(len(a.flat))
    vtkt.SetNumberOfComponents(1)
    vtkt.SetVoidArray(data,len(a.flat), 1)

    vtka = vtk.vtkFloatArray()
    vtka.DeepCopy(vtkt)
    return vtka

def read_src_vtk_image(filename):
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(filename)
    reader.Update()
    #print reader.GetOutput()
    return reader.GetOutput()

grid = vtk.vtkRectilinearGrid()

src_filename = sys.argv[1]
src_image = read_src_vtk_image(src_filename)

d = src_image.GetDimensions()
o = src_image.GetOrigin()
s = src_image.GetSpacing()

print d,o
#zxc=[-6.6, -6.12, -5.64, -5.16, -4.68, -4.20, -3.72] * 50
zxc=[6.12, 5.64, 5.16, 4.68, 4.20, 3.72, 3.24, 3.00, 2.76, 2.52, 2.28, 2.16, 2.04, 1.92, 1.80, 1.68, 1.56, 1.44, 1.28, 1.20, 1.08, 0.96, 0.84, 0.72, 0.60, 0.48, 0.36, 0.24, 0.12, 0.00, 0.24, 0.12, 0.00, -0.12, -0.24, -0.36, -0.48, -0.60, -0.72, -0.84, -0.96, -1.08, -1.20, -1.32, -1.44, -1.56, -1.72, -1.80, -1.92, -2.04, -2.16, -2.28, -2.40, -2.52, -2.64, -2.76, -2.92, -3.00, -3.13, -3.24, -3.36, -3.48, -3.60, -3.72, -3.84, -3.96, -4.08, -4.20, -4.38, -4.44, -4.56, -4.68, -4.80, -4.92, -5.04, -5.20, -5.28, -5.40, -5.52, -5.64]
print zxc
xcoords=map(lambda x: o[0] + s[0]*x, range(d[0]))
#ycoords=map(lambda x: o[1] + s[1]*x, range(d[1]))
ycoords=map(lambda x: -1*zxc[x], range(d[1]))
zcoords=map(lambda x: o[2] + s[2]*x, range(d[2]))
#print xcoords ycoords zcoords

xc = array2vtk(np.array(xcoords))
yc = array2vtk(np.array(ycoords))
zc = array2vtk(np.array(zcoords))

grid.SetDimensions(src_image.GetDimensions())
grid.SetXCoordinates(xc)
grid.SetYCoordinates(yc)
grid.SetZCoordinates(zc)

grid.UpdateData()
grid.UpdateInformation()

#print src_image.GetDimensions()
#print src_image.GetSpacing()
grid.GetPointData().SetScalars(src_image.GetPointData().GetScalars())
grid.Update()


geometry = read_src_vtk_image('geometry.vtk')

probe = vtk.vtkProbeFilter()
probe.SetInput(geometry)
probe.SetSource(grid)
probe.Update()
print "sfdvg"

w=vtk.vtkStructuredPointsWriter()
w.SetInput(probe.GetImageDataOutput())
w.SetFileName(sys.argv[2])
w.Update()
