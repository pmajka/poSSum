SHELL = /bin/bash

all:
	bash -xe step_01_workflow.sh

clean:
	rm -rfv 10_processed_sections/ \
		test_case_processed.xls test_case_processed.pickle
	git checkout header.sh
