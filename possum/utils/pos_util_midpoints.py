#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import itk

from possum import pos_itk_core
from possum import pos_itk_transforms
from possum.pos_common import r


"""
.. note::

    Some of the non-cruical, optional functions in this module require vtk
    module to be installed. If it is not available the VTK support will be
    disabled.
"""


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

    .. note :: Please have in ming that this procedure returns position of the
    first (index-wise) voxel with the maimum value. This means that if there is
    more than one pixels with the maximum value of the distance transform,
    location of the first one is returned. One could think that probably a
    centre of mass of the max voxels should be returned, but no. It is unknown
    is such centre would be located in the actual structure or outside the
    structure. Therefore some of the results may look wired but they are
    actually ok.

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

    And now it it a time to do some unit testing. Please also consited this set
    of unittests as an example how to use this function.

    >>> import base64
    >>> from possum import pos_itk_transforms
    >>> example_two_dimensions='H4sIAAAAAAAAA4thZCACFDEwMWgAISMcogImBg44u8EegdHBBmdUPosTNtvCizJLSlLzFJIqFQIq/TzTQjwVylKLijPz8xQM9IwMDA0MzAzM9QyJcfiAgTxtdPcxwgETHDDDwag6+qjjggNuOOCBA144GFVHH3UicCAKB2JwIA4Ho+roo04ODuThQAEOFOFgVB191AEAXtGveKAHAAA='

    >>> open("/tmp/pos_itk_centroids_example_two_dimensions.nii.gz", "w").write(base64.decodestring(example_two_dimensions))
    >>> input_filename="/tmp/pos_itk_centroids_example_two_dimensions.nii.gz"
    >>> itk_image = pos_itk_transforms.read_itk_image(input_filename)
    >>> midpoints = get_middle_points(itk_image)

    >>> sorted(midpoints.keys()) == [1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23, 30, 31, 32, 33]
    True

    >>> map(int, midpoints[1][0]) == [14, 0, 0]
    True

    >>> map(int, midpoints[21][0]) == [14, 24, 0]
    True

    >>> midpoints[30] == ((0.0, 39.0, 0), (0, 39, 0))
    True

    >>> type(midpoints[30][1][1]) == type(1)
    True

    >>> type(midpoints[30][0][1]) == type(1)
    False

    >>> type(midpoints[30][0][1]) == type(1.0)
    True

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

    assert n_dim in [2, 3], \
        "Incorrect dimensionality."

    assert number_of_components == 1, \
        "Only single component images are allowed."

    assert data_type in ["unsigned_char", "unsigned_short"], \
        r("Incorrect data type for a labelled image only unsigned_char\
          and unsigned_short are accepted.")

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
    unique_labels.CalculatePixelIndicesOff()
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

    # Below there is some debugging code. Not really important for everyday
    # use.
    # print middle_points.__repr__()

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
        return None

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
    import doctest
    print doctest.testmod(verbose=True)
