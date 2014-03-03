all:
	python ../../pos_reorder_volume.py \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping valid_mapping

	python ../../pos_reorder_volume.py \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_long

	python ../../pos_reorder_volume.py \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_not_uniqe

	python ../../pos_reorder_volume.py \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_short_begin

	python ../../pos_reorder_volume.py \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_short_end

	python ../../pos_reorder_volume.py \
		-i test_image.nii.gz \
		-o out_test_image.nii.gz \
		--mapping invalid_mapping_to_short_middle
	
	rm -vf out_test_image.nii.gz
