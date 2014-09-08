#==============================================================================
#description     :This makefile carries out all necessary calculations
#                :related to the 'test_banana_pairwise' test
#author          :Konrad Solarz, Piotr Majka
#date            :2014-08-29
#usage           :make all
#==============================================================================


all: final_reconstruction.nii.gz

distorted_stack.nii.gz:
	bash -xe step_001_distort_reference_data.sh

final_reconstruction.nii.gz: distorted_stack.nii.gz
	bash -xe step_002_perform_reconstruction.sh
    
clean:
	rm -rfv distorted_stack.nii.gz final_reconstruction.nii.gz reference.nii.gz \
		discrepancy_measurements.txt
