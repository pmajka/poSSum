#!/bin/bash -x

# -------------------------------------------------------------------
# Iterative pairwise reconstruction workflow with a reference volume.
# -------------------------------------------------------------------

source header.sh


# Setup the filenames and the directories.
DIR_PAIRWISE_ITERATION=iteration/
FILE_REFERENCE_MASK=input_for_reconstruction.nii.gz
VOL_RGB_SLICE_TO_SLICE_MASKED=${DIR_SOURCE_STACKS}/rgb_slice_to_slice_masked_stack_downsampled_gray.nii.gz


# -------------------------------------------------------------------
# And then create the actual directory structure.
# -------------------------------------------------------------------

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
	# First, calculate an initial affine transformation
	# Note that this produces a very rough, translation
	# transformation.
	pos_align_by_moments \
	    -m ${FILE_REFERENCE_MASK} \
	    -f ${AFFINE_FIXED_IMAGE} \
	    -t ${OUTPUT_NAMING}initial_affine.txt \
	
	ANTS 3 \
	    -m MI[${AFFINE_FIXED_IMAGE},${FILE_REFERENCE_MASK},1,32] \
	    -o ${OUTPUT_NAMING} \
	    -i 0 \
	    --use-Histogram-Matching \
	    --initial-affine ${OUTPUT_NAMING}initial_affine.txt \
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
	    --work-dir __pairwise__$iteration \
	    --ants-image-metric CC \
	    --movingSlicesRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
	    --fixedSlicesRange  ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
	    --reslice-backgorund ${RESLICE_BACKGROUND} \
	    --fixedImagesDir ${DIR_REF} \
	    --movingImagesDir ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}${ii}/exp/ \
	    --output-volumes-directory ${DIR_WORK}/ \
	    --grayscale-volume-filename slices_to_reference_${ii}.nii.gz \
	    --transformationsDirectory ${DIR_TRANSF}/ \
	    --skipColorReslice \
	    --enable-moments \
	    ${OV_SETTINGS} \
	    --loglevel DEBUG \
	    --use-rigid-affine \
	    --cleanup
    fi

    let iteration=iteration+1 
done



# -------------------------------------------------------------------
# Now, once we have calculated the iterative pairwise transformations
# it is time to reslice the source rgb images.
# ---------------------------------------------------------

# This is just a helper function.
function get_transformations {
    sec=$1
    return=""
     
    for f in  `ls -1 ${DIR_COARSE_ALIGNMENT}/${DIR_PAIRWISE_ITERATION}????/transformations/tr_m${sec}_Affine.txt`
    do
        return+=" $f "
    done
     
    echo ${return}
}

# Merge all the individual transformations into a sigle
# one and store it in a dedicated directory:
mkdir -p ${DIR_FINAL_PAIRWISE}

for j in `seq ${IDX_FIRST_SLICE} 1 ${IDX_LAST_SLICE}`
do
    jj=`printf %04d $j`
    ComposeMultiTransform 2 \
        ${DIR_FINAL_PAIRWISE}/${jj}.txt \
        `get_transformations ${jj}`
done

# And now, simply reslice the source rgb images:
pos_stack_warp_image_multi_transform \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedImageInputDirectory ${DIR_SLICE_TO_SLICE_MASKED}/ \
    --movingImageInputDirectory ${DIR_SLICE_TO_SLICE_MASKED}/ \
    --appendTransformation 0 ${DIR_FINAL_PAIRWISE}/%04d.txt \
    ${OV_SETTINGS} \
    --output-volumes-directory . \
    --volumeFilename rgb_after_pairwise.nii.gz \
    --work-dir __pairwise__rgb_after_pairwise \
    --loglevel DEBUG \
    --cleanup

# ---------------------------------------------------------
