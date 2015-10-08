#!/bin/sh

# -------------------------------------------------------------------
# This example shows how one can align two three dimensional images
# (i.e. volumes) by their centres of masses. The example uses 3D images
# however it will work equally well when provided with two dimensional
# images as well. Such usage is ilustrated in other examples.
#
# The MR images of the bananas were obtained by the curtesy
# of Dr Artur Marchewka and Mr Bartosz Kossowski
# from the Labloratory of Brain Imaging (http://lobi.nencki.gov.pl)
# at the Nencki Istitute of Experimental Biology, Warsaw, Poland
# (http://nencki.gov.pl)
# -------------------------------------------------------------------

pos_align_by_moments \
    -f fixed_banana.nii.gz \
    -m moving_banana.nii.gz \
    -o moving_image_aligned_to_fixed_image.nii.gz \
    -t transformation_moving_image_to_fixed_image.txt

