#==============================================================================
#description     :This makefile carries out all necessary calculations
#                :related to the 'test_banana_pairwise' test
#author          :Piotr Majka, Konrad Solarz
#date            :2014-09-30
#usage           :make all
#==============================================================================

all: step1 step2 step3 step4

step1:
	bash -x step_001_initialize_workflow.sh

step2: 
	bash -x step_002_perform_reconstruction.sh

step3:
	bash -x step_003_reconstruction_sequential.sh

step4:
	bash -x step_004_deformable_reconstruction.sh

clean:
	rm -rf \
	final_image_mask.nii.gz final_image.nii.gz \
	gray_after_pairwise.nii.gz \
	input_for_deformable_reconstruction.nii.gz \
	input_for_reconstruction.nii.gz \
	rgb_after_pairwise.nii.gz \
	sequential_alignment.nii.gz \
	sequential_alignment_s-0_e-311_r-110_ROI-None_Resize-None_Color-red_Median-None_Metric-MI_MetricOpt-32_Affine-True_eps-5_lam0.00outROI-None_gray.nii.gz \
	transforms_01_pairwise transforms_02_sequential \
	__calculations__01_iterative_pariwise_alignment \
        __calculations__02_sequential_alignment \
	__calculations__03_deformable_reconstruction \
	01_input_data/01_rgb_to_resample \
	01_input_data/02_sections_to_shape_prior \
	01_input_data/03_masks_to_resample 
