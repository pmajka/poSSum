all: coarse_to_fine.nii.gz

distorted_stack.nii.gz:
	bash -xe step_001_distort_reference_image.sh

coarse_to_fine.nii.gz: distorted_stack.nii.gz
	bash -xe step_002_reconstruct.sh

clean:
	rm -v distorted_stack.nii.gz \
	sections_to_shape_prior.nii.gz \
	sequential_alignment.nii.gz \
	coarse_to_fine.nii.gz \
	reference_image.nii.gz \
	shape_prior.nii.gz \
	reconstruction_discrepancy.nii.gz \
	test_banana_effect.md5
	
