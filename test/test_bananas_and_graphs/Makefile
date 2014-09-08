all: grayscale_l0.0_e10.nii.gz

grayscale_l0.0_e10.nii.gz:
	bash -xe step_001_sequential_alignment_with_graphs.sh

clean:
	rm -vrf  \
		grayscale_l0.0_e10.nii.gz \
		grayscale_l0.2_e1.nii.gz \
		grayscale_l0.5_e1.nii.gz 
