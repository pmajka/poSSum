all:
	pos_reorder_volume \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping valid_mapping

	pos_reorder_volume \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_long

	pos_reorder_volume \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_not_uniqe

	pos_reorder_volume \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_short_begin

	pos_reorder_volume \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_short_end

	pos_reorder_volume \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_short_middle
	
	rm -vf out_test_image.nii.gz
