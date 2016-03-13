#!/bin/bash -xe

# -------------------------------------------------------------------
# Iterative pairwise reconstruction workflow with a reference volume.
# -------------------------------------------------------------------
source header.sh


# Setup the filenames and the directories.
DIR_COARSE_ALIGNMENT=calculations/
DIR_PAIRWISE_ITERATION=iteration/
VOL_RGB_SLICE_TO_SLICE_MASKED=distorted_stack.nii.gz

# Set the number of the pairwise iterations
# (presumably, the more the better. Not proven, though.)
MAX_PAIRWISE_ITERATIONS=10

# -------------------------------------------------------------------
# Remove the calculations from the previous iteration
# (if they exist). In some cases the data from previous iterations
# may cause errors in the current run. Hence, there should be no
# data from any previous run.
rm -rfv ${DIR_COARSE_ALIGNMENT}

# -------------------------------------------------------------------
# And then create the actual directory structure.
mkdir -p ${DIR_COARSE_ALIGNMENT}


# -------------------------------------------------------------------
# Enough configuration. Let's start off
# -------------------------------------------------------------------

# Iterative reconstruction routine
iteration=1
first_iteration_index=1

function iterfile_with_prefix {
    prefix="--transform"
    sec=$1

    return=""
     
    for f in  `ls -1 ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}????/transformations/tr_m${sec}_Affine.txt`
    do
        return+=" --transform $f "
    done
     
    echo ${return}
}

while [  $iteration -le ${MAX_PAIRWISE_ITERATIONS} ];
do

    ii=`printf %04d $iteration`
    first_iteration=`printf %04d ${first_iteration_index}`

    DIR_WORK=${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}${ii}/
    DIR_EXP=${DIR_WORK}/exp/
    DIR_REF=${DIR_WORK}/ref/
    DIR_TRANSF=${DIR_WORK}/transformations/
    mkdir -p ${DIR_EXP} ${DIR_REF} ${DIR_TRANSF}

    if [ ${iteration} -eq ${first_iteration_index} ]
    then
        AFFINE_FIXED_IMAGE=${VOL_RGB_SLICE_TO_SLICE_MASKED}
        pos_slice_volume \
            -i ${VOL_RGB_SLICE_TO_SLICE_MASKED} \
            -o ${DIR_EXP}/%04d.nii.gz \
            -s ${SLICING_PLANE_INDEX}
    else
        PREVIOUS_ITER=`printf %04d $((iteration-1))`
        AFFINE_FIXED_IMAGE=${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}${PREVIOUS_ITER}/slices_to_reference_${PREVIOUS_ITER}.nii.gz
    fi

    OUTPUT_NAMING=${DIR_COARSE_ALIGNMENT}/referece_to_slice_${iteration}_

    # Well here's why we remove the results from previous runs.
    # The cacultations are performed only and only if the resulting files
    # are not present. Thus, if files from previous runs are present, the
    # calculations are not updated. Please be aware of that.
    if [ ! -f ${OUTPUT_NAMING}deformed.nii.gz ]
    then
        ANTS 3 \
            -m MI[${AFFINE_FIXED_IMAGE},${FILE_REFERENCE_MASK},1,32] \
            -o ${OUTPUT_NAMING} \
            -i 0 \
            --use-Histogram-Matching \
            --number-of-affine-iterations 10000x10000x10000x10000x10000 \
            --rigid-affine false
        
        WarpImageMultiTransform 3 \
            ${FILE_REFERENCE_MASK} \
            ${OUTPUT_NAMING}deformed.nii.gz \
            ${OUTPUT_NAMING}Affine.txt \
            -R ${VOL_RGB_SLICE_TO_SLICE_MASKED}
    fi

    # Similarly as above, if the old results are present, the alignment
    # is not performed. Thus, the resulting file musn't be present.
    if [ ! -f ${DIR_WORK}/slices_to_reference_${ii}.nii.gz ]
    then
        pos_slice_volume \
            -i ${OUTPUT_NAMING}deformed.nii.gz \
            -o ${DIR_REF}/%04d.nii.gz \
            -s ${SLICING_PLANE_INDEX} \
            --output-filenames-offset ${IDX_FIRST_SLICE}
        
        for j in `seq ${IDX_FIRST_SLICE} 1 ${IDX_LAST_SLICE}`
        do
            jj=`printf %04d $j`

            antsApplyTransforms -d 2 \
                --input ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}${first_iteration}/exp/${jj}.nii.gz \
                --reference-image ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}${first_iteration}/exp/${jj}.nii.gz \
                --output ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}${ii}/exp/${jj}.nii.gz \
                `iterfile_with_prefix ${jj}` \
                --default-value ${RESLICE_BACKGROUND}
        done

        pos_pairwise_registration \
            --antsImageMetric CC \
            --movingSlicesRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
            --fixedSlicesRange  ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
            --resliceBackgorund ${RESLICE_BACKGROUND} \
            --fixedImagesDir ${DIR_REF} \
            --movingImagesDir ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}${ii}/exp/ \
            --outputVolumesDirectory ${DIR_WORK}/ \
            --grayscale-volume-filename slices_to_reference_${ii}.nii.gz \
            --transformationsDirectory ${DIR_TRANSF}/ \
            --skipColorReslice \
            ${OV_SETTINGS} \
            --loglevel DEBUG \
            --useRigidAffine \
            --cleanup
    fi

    let iteration=iteration+1 
done

lastiter=`printf %04d ${MAX_PAIRWISE_ITERATIONS}`
antsApplyTransforms -d 3 \
     -i ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}/${lastiter}/slices_to_reference_${lastiter}.nii.gz \
     -o "final_reconstruction.nii.gz" \
     -t [calculations/referece_to_slice_${MAX_PAIRWISE_ITERATIONS}_Affine.txt,1] \
     -r ${FILE_REFERENCE_MASK}
     
rm -rfv ${DIR_COARSE_ALIGNMENT}


# ---------------------------------------------------------
# Just simply measure the dicrepancy between the the 
# reconstructed image and the reference one.
# ---------------------------------------------------------

c3d reference.nii.gz final_reconstruction.nii.gz -msq > discrepancy_measurements.txt
# Should give MSQ = 186, verified later by the md5 checksum.

# --------------------------------------------------------
# Validate md5 sums of the obtained files
# --------------------------------------------------------
md5sum -c test_banana_pairwise.md5
