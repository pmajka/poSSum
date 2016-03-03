#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import itk

from possum.pos_common import r
from possum import pos_itk_core
from possum import pos_itk_transforms


# Try importing the vtk module. If the module cannot be imported some of the
# features of the workflow cannot be executed.
try:
    import vtk
except ImportError:
    pass

# TODO: Tests, logging.


def get_middle_points(itk_image):
    """
    This function introduces a workflow for calculating the middle midpoints of
    the labelled imags. The term 'middle midpoints' is used on purpose. You might
    think that we're calculating centroids here, but not. I use the term
    'middle midpoints' as it is not the centroids what is calculated here.

    Anyway, this function calculated middle midpoints of labels in the provided image.
    The midpoints are calculated in the following way:

    Now iterate over all available labels except the background label which
    has been removed. The overall idea of this loop is to:
    1) Extract given label from the segmentation
    2) Extract the largest patch of the segmentation as there
       might be multiple disjoint regions colored with given label
    3) Apply the distance transform to the largest path with
       given segmentation
    4) Pick the maximum of the distance transform for given segmentation
       and by this define the 'middle point' of given label.

    :param itk_image: Labelled image, the image is expected to be a labelled
                      image in which individual discrete values correspond
                      to individual structures. Formally this means that
                      the image has to be of `uchar` or `ushort` type,
                      to have a single component and to have
                      a dimensionality of two or three. Images having
                      different properties will not be processed.
    :type itk_image: `itk.Image`

    :return: Middle midpoints of the labels in the image.
    :rtype: {int: ((float, float, float), (float, float, float)), ...}
    """

    C_BACKGROUND_LABEL_IDX = 0
    # Define the dimensionality, data type and number of components
    # of the label image
    label_type = \
        pos_itk_core.io_image_type_to_component_string_name[
            itk_image.__class__]

    # Extract the details of the image provided and check if they are
    # ok to use in the routine.

    n_dim = len(itk_image.GetLargestPossibleRegion().GetSize())
    number_of_components = itk_image.GetNumberOfComponentsPerPixel()
    data_type = label_type[1]

    print n_dim, number_of_components, data_type

    assert n_dim in [2, 3], \
        "Incorrect dimensionality."

    assert number_of_components == 1, \
        "Only single component images are allowed."

    assert data_type in ["unsigned_char", "unsigned_short"], \
        "Incorrect data type for a labelled image."

    # t_label_img is the ITK image type class to be used in filters
    # templates.
    t_label_img = itk_image.__class__

    # We'll be also using another image type. This one is identical
    # in terms of size and dimensionality as the labelled image.
    # The differe is in data type: this one has to be float to handle
    # the distance transform well.
    float_type = list(label_type)
    float_type[1] = "float"
    t_float_img = \
        pos_itk_core.io_component_string_name_to_image_type[tuple(float_type)]

    # The purpose of the filter below is to define the unique labels
    # given segmentation contains.
    unique_labels = \
        itk.LabelGeometryImageFilter[(t_label_img, t_label_img)].New()
    unique_labels.SetInput(itk_image)
    unique_labels.CalculatePixelIndicesOn()
    unique_labels.Update()

    # This is where we'll collect the results. We collect, both, the physical
    # location as well as the
    middle_points = {}

    # We have to map the available labels returned by itk
    # as sometimes strange things happen and they are returned as longints
    # which are apparently incomparibile with python in type.
    # Consider it a safety precaution
    available_labels = map(int, unique_labels.GetLabels())

    # Now we need to remove the background label (if such
    # label actually exists)
    C_BACKGROUND_LABEL_IDX
    try:
        available_labels.remove(C_BACKGROUND_LABEL_IDX)
    except:
        pass

    # Now iterate over all available labels except the background label which
    # has been removed. The overall idea of this loop is to:
    # 1) Extract given label from the segmentation
    # 2) Extract the largest patch of the segmentation as there
    #    might be multiple disjoint regions colored with given label
    # 3) Apply the distance transform to the largest path with
    #    given segmentation
    # 4) Pick the maximum of the distance transform for given segmentation
    #    and by this define the 'middle point' of given label
    # I call the midpoints 'middle midpoints' not centroids as centroids
    # are something different and they are calculated in a different
    # way. Our center midpoints cannot be called centroids.
    for label_idx in available_labels:

        extract_label = \
            itk.BinaryThresholdImageFilter[
                (t_label_img, t_label_img)].New()
        extract_label.SetInput(itk_image)
        extract_label.SetUpperThreshold(label_idx)
        extract_label.SetLowerThreshold(label_idx)
        extract_label.SetOutsideValue(0)
        extract_label.SetInsideValue(1)
        extract_label.Update()

        patches = \
            itk.ConnectedComponentImageFilter[
                (t_label_img, t_label_img)].New()
        patches.SetInput(extract_label.GetOutput())
        patches.Update()

        largest_patch = \
            itk.LabelShapeKeepNObjectsImageFilter[t_label_img].New()
        largest_patch.SetInput(patches.GetOutput())
        largest_patch.SetBackgroundValue(0)
        largest_patch.SetNumberOfObjects(1)
        largest_patch.SetAttribute(100)
        largest_patch.Update()

        distance_transform = \
            itk.SignedMaurerDistanceMapImageFilter[
                (t_label_img, t_float_img)].New()
        distance_transform.SetInput(largest_patch.GetOutput())
        distance_transform.InsideIsPositiveOn()
        distance_transform.Update()

        centroid = itk.MinimumMaximumImageCalculator[t_float_img].New()
        centroid.SetImage(distance_transform.GetOutput())
        centroid.Compute()
        centroid.GetIndexOfMaximum()

        index = centroid.GetIndexOfMaximum()
        point = itk_image.TransformIndexToPhysicalPoint(index)

        # We need to slightly refine the results returned by itk
        # The results have to be processed in a slightly different way for
        # two dimensional results and slightly different for 3D resuls:
        # Again, we do a lot of explicit casting assure types
        # compatibility. The 2D midpoints are converted into 3D midpoints since
        # it is easier to use them in vtk if they're 3D midpoints.
        if n_dim == 2:
            point = map(float, point) + [0]
            index = map(int, index) + [0]
        if n_dim == 3:
            point = map(float, point)
            index = map(int, index)

        middle_points[label_idx] = (tuple(point), tuple(index))

    return middle_points


def points_to_vtk_points(points_list):
    """
    The function converts the location of the middle points into a vtkPolyData
    structure and assigns appropriate label IDs to the individual points of the
    vtk points structure. Basically, you can use the resulting vtkPolyData() and
    know where is a centre of a particular structure.

    ... note ::
        This function will not work if the vtk module is not loaded.

    :param point_list: List of points to turn into vtk points
    :type point_list: {int: ((float, float, float), (float, float, float)), ...}

    :return: Midpoints of the individual structures expressed as
             vtk.vtkPolyData()
    :rtype: `vtk.vtkPolyData`
    """

    try:
        vtk.vtkVersion()
    except:
        return

    n_points = len(points_list.keys())

    points = vtk.vtkPoints()
    vertices = vtk.vtkCellArray()

    id_array = vtk.vtkUnsignedCharArray()
    id_array.SetName("Label_ID")
    id_array.SetNumberOfComponents(1)
    id_array.SetNumberOfTuples(n_points)

    for (i, (pt, idx)) in points_list.items():
        id_ = points.InsertNextPoint(pt)
        vertices.InsertNextCell(1)
        vertices.InsertCellPoint(id_)
        id_array.SetTuple1(id_, i)

    point = vtk.vtkPolyData()
    point.SetPoints(points)
    point.SetVerts(vertices)
    point.GetPointData().AddArray(id_array)

    return point

if __name__ == '__main__':
    input_filename = sys.argv[1]
    output_vtk_points_filename = sys.argv[2]
    itk_image = pos_itk_transforms.read_itk_image(input_filename)
    midpoints = get_middle_points(itk_image)

    vtk_points_writer = vtk.vtkPolyDataWriter()
    vtk_points_writer.SetFileName(output_vtk_points_filename)
    vtk_points_writer.SetInput(points_to_vtk_points(midpoints))
    vtk_points_writer.Update()
