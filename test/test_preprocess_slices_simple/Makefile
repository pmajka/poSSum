SHELL = /bin/bash

all:
	bash -xe step_01_workflow.sh

clean:
	rm -rfv 10_input_data/ 11_sections_sequential_alignment/ 00_source_sections/
	rm -rfv sequential_alignment*.nii.gz
	git checkout brainmaps_s40_processed.xls header.sh
