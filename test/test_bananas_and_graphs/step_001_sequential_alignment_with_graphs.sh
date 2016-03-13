#!/bin/bash -xe

source header.sh

rm -rvf  001_sections_to_reconstruct
mkdir -p 001_sections_to_reconstruct

# ---------------------------------------------------------
# A several series of reconstructions are to be carried out.
# parameters for these reconstructions stored in the parameter
# file, one series per line.
# ---------------------------------------------------------
PARAM_FILE=attepmts_parameters

# ---------------------------------------------------------
# Extract the sections:
# ---------------------------------------------------------

pos_slice_volume \
   -s ${SLICING_PLANE_INDEX} \
   -i distorted_stack/distorted_stack_masked.nii.gz \
   -o 001_sections_to_reconstruct/%04d.nii.gz

# Determine the number of attempts by counting the number
# of line in the parameter file.
ITERATIONLIMIT=$[`wc -l ${PARAM_FILE} | cut -f1 -d" "`]

for ITERATION in `seq 1 1 ${ITERATIONLIMIT}`
do

    # ---------------------------------------------------------
    # Read reconstruction parameters from file
    # Note that the first line in the file is a header
    # and thus is it skipped
    # ---------------------------------------------------------
    PARAM_LAMBDA=`sed -n "${ITERATION} p" ${PARAM_FILE} | cut -f1 -d" "`
    PARAM_EPSILON=`sed -n "${ITERATION} p" ${PARAM_FILE} | cut -f2 -d" "`
    
    # ---------------------------------------------------------
    # Perform seqential alignment:
    # ---------------------------------------------------------
    
    pos_sequential_alignment \
        --enable-sources-slices-generation \
        --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
        --inputImageDir 001_sections_to_reconstruct/ \
        --registrationColor red \
        --enable-transformations \
            --useRigidAffine \
            --antsImageMetric CC \
            --reslice-backgorund 0 \
            --graphEdgeLambda ${PARAM_LAMBDA} \
            --graph-edge-epsilon ${PARAM_EPSILON} \
        --output-volumes-directory . \
            ${OV_SETTINGS} \
        --grayscale-volume-filename grayscale_l${PARAM_LAMBDA}_e${PARAM_EPSILON}.nii.gz \
        --loglevel DEBUG \
        --work-dir __workdir_sequential_reconstruction__ \
        --cleanup
done

# Remove directories with temporary results, so the next series
# of calculations could be carried out without any interference
# with the previous one.
rm -rv 001_sections_to_reconstruct
rm -rv sequential_alignment_*.nii.gz

# ------------------------------------------------------
# Verify if the calculations were performed correctly:
md5sum -c graphs_and_bananas_test.md5
