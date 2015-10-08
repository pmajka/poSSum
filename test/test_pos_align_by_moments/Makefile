#==============================================================================
#description     : This example shows how one can apply align two dimensional
#                : images by their centres of gravity. 
#author          : Piotr Majka
#date            : 2015-10-07
#usage           : make all
#==============================================================================

all: verify_results

verify_results: results
	md5sum -c test_pos_align_by_moments.md5

results: clean
	bash -xe test_pos_align_by_moments.sh

clean:
	rm -rfv transformation-*.txt \
			resliced_*.nii.gz \
			comparison-*.nii.gz
