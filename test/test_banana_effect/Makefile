all: coarse_to_fine.nii.gz

distorted_stack.nii.gz:
	bash -xe step_001_distort_reference_image.sh

coarse_to_fine.nii.gz: distorted_stack.nii.gz
	bash -xe step_002_reconstruct.sh

clean:
	rm -vrf  \
	sections_to_shape_prior.nii.gz \
	sequential_alignment.nii.gz \
	coarse_to_fine.nii.gz \
	reference_image.nii.gz \
	shape_prior.nii.gz \
	reconstruction_discrepancy.nii.gz \
	sequential_alignment_s-0_*.nii.gz \
	002_distorted_data \
	003_shape_prior_sections \
	004_distorted_sections \
	005_pairwise_alignment \
	006_sections_to_shape_prior \
	007_sequential_alignment \
	008_coarse_to_fine
