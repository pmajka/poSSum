#==============================================================================
#description     :This makefile carries out all necessary calculations
#                :related to the 2d -> 3d images stacking examples
#author          :Piotr Majka
#date            :2014-12-16
#usage           :make all
#==============================================================================

all: stacked_axial_exmaple.nii.gz stacked_coronal_exmaple.nii.gz stacked_sagital_exmaple.nii.gz

stacked_axial_exmaple.nii.gz: stack_axial_example.sh
	bash -xe stack_axial_example.sh

stacked_coronal_exmaple.nii.gz: stack_coronal_example.sh
	bash -xe stack_coronal_example.sh

stacked_sagital_exmaple.nii.gz: stack_sagital_example.sh 
	bash -xe stack_sagital_example.sh

clean:
	rm -vrf  \
		stacked_axial_exmaple.nii.gz \
		stacked_coronal_exmaple.nii.gz \
		stacked_sagital_exmaple.nii.gz \
		stacked_coronal_exmaple_downsampled.nii.gz
