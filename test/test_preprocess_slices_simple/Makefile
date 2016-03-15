SHELL = /bin/bash

all:
	bash -xe step_01_workflow.sh

clean:
	rm -rfv 10_input_data/ 11_sections_sequential_alignment/ 00_source_sections/
	rm -rfv sequential_alignment*.nii.gz
	git checkout brainmaps_s40_processed.xls header.sh



####clean:
####	rm -rfv 10_processed_sections/ \
####		test_case_processed.xls test_case_processed.pickle
####	git checkout header.sh
