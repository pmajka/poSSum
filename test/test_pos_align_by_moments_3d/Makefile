#==============================================================================
#description     : This example shows how one can align two three dimensional
#                : images  (i.e. volumes) by their centres of masses.
#   			 : The example uses 3D images  however it will work equally
#   			 : well when provided with two dimensional images as well.
#   			 : Such usage is ilustrated in other examples.
#author          : Piotr Majka
#date            : 2015-10-07
#usage           : make all
#==============================================================================

all: verify_results

verify_results: results
	md5sum -c test_pos_align_by_moments_3d.md5

results: clean
	bash -xe test_pos_align_by_moments_3d.sh

clean:
	rm -rfv moving_image_aligned_to_fixed_image.nii.gz \
    	    transformation_moving_image_to_fixed_image.txt
