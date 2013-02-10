PROGPATH=/opt/ANTs-1.9.y-Linux/bin/
JOB_EXECUTION_DIR=${HOME}/possum/testy_deformable/

REGION_DEFINITION_TEMPLATE[1]='-region 34%x8%x22%   20%x20%x20%'
REGION_DEFINITION_TEMPLATE[2]='-region 22%x22%x26%  20%x20%x20%'
REGION_DEFINITION_TEMPLATE[3]='-region 35%x25%x37%  20%x20%x20%'
REGION_DEFINITION_TEMPLATE[4]='-region 36%x28%x19%  20%x20%x20%'
REGION_DEFINITION_TEMPLATE[5]='-region 16%x38%x18%  20%x20%x20%'
REGION_DEFINITION_TEMPLATE[6]='-region 36%x38%x20%  20%x20%x20%'
REGION_DEFINITION_TEMPLATE[7]='-region 66%x42%x43%  20%x20%x20%'
REGION_DEFINITION_TEMPLATE[8]='-region 36%x42%x20%  20%x20%x20%'
REGION_DEFINITION_TEMPLATE[9]='-region 9%x42%x25%   20%x20%x20%'
REGION_DEFINITION_TEMPLATE[10]='-region 35%x33%x36% 20%x20%x20%'
REGION_DEFINITION_TEMPLATE[11]='-region 43%x39%x34% 20%x20%x20%'
REGION_DEFINITION_TEMPLATE[12]='-region 40%x43%x25% 20%x20%x20%'
REGION_DEFINITION_TEMPLATE[13]='-region 36%x48%x22% 20%x20%x20%'
REGION_DEFINITION_TEMPLATE[14]='-region 35%x54%x22% 20%x20%x20%'
REGION_DEFINITION_TEMPLATE[15]='-region 17%x60%x39% 20%x20%x20%'
REGION_DEFINITION_TEMPLATE[16]='-region 36%x69%x39% 20%x20%x20%'
REGION_DEFINITION_TEMPLATE[0]=' '

OUTPUT_SPACING=0.1x0.1x0.1mm
#OUTPUT_SPACING=0.05x0.05x0.05mm
SLICE_RESAMPLED_PLANE='y'
SLICE_RESAMPLED_SLICE='150'

IMG_DIM=3
PARAM_FILE=$1
REGION=$2
JOB_IDENTIFIER_PREFIX=deformable_registration_full_`date +%Y-%m-%d-%H-%M`_${BASHPID}_${REGION}_
ITERATIONLIMIT=$[`wc -l ${PARAM_FILE} | cut -f1 -d" "`-1]
REGION_DEFINITION=${REGION_DEFINITION_TEMPLATE[REGION]}

DROPBOX=/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/
DROPBOX_PRIV=/home/pmajka/Dropbox/
DIRECTORY_POSSUM_MASKS_BACKUP=/home/pmajka/possum/data/02_02_NN2/74_deformable_multimodal_registration/

#FIXED_RAW=${DROPBOX}/02_02_NN2_mri.nii.gz
FIXED_RAW=/home/pmajka/possum/testy_deformable/02_02_NN2_mri.nii.gz
FIXED_RAW_MASK=${DROPBOX}/mri_registration_mask.nii.gz

#MOVING_RAW=${DROPBOX}/02_02_NN2_deformable_hist_reconstruction_myelin_resliced.nii.gz
MOVING_RAW=/home/pmajka/possum/testy_deformable/02_02_NN2_deformable_hist_reconstruction_myelin_resliced.nii.gz
MOVING_RAW_MASK=${DROPBOX}/myelin_registration_mask.nii.gz

HISTOLOGY_MULTIPLIER_RAW=${DROPBOX}/02_02_NN2_mri_mask_histology_multiplier_straight.nii.gz

ITERATION_PREFIX=iteration_
INITIAL_AFFINE_TRANSFORM_RAW=~/possum/processing_supplement/02_02_NN2_histology_myelin_to_straight_mri_affine.txt
#INITIAL_DEFORMABLE_TRANSFORM_RAW=/home/pmajka/possum/testy/myelin_to_mri_step2_attempt_0/05_registration_raw_v2/f__m__CC0005_SyN0.35_Gauss0,0_i1000x1000_mi32x1600_afi0_rigidfalse_amt_CC_psep1.0_psew1.000000_mw1.000000_ccw0.000000_syni02_syns0.010000_Warp.nii.gz
INITIAL_DEFORMABLE_TRANSFORM_RAW=/home/pmajka/possum/testy_deformable/initial_deformable.nii.gz

INITIAL_DEFORMABLE_TRANSFORM=initial_Warp.nii.gz
INITIAL_AFFINE_TRANSFORM=initial_Affine.txt

#==============================================================================
# Naming conventions. Not really for configuration.
#==============================================================================

FIXED_SRC=fixed_src.nii.gz
FIXED_MASK_SRC=fixed_mask_src.nii.gz

MOVING_SRC=moving_src.nii.gz
MOVING_MASK_SRC=moving_mask_src.nii.gz

FIXED_SEG=fixed_seg.nii.gz
MOVING_SEG=moving_seg.nii.gz

#==============================================================================

FIXED=fixed.nii.gz
FIXED_MASK=fixed_mask.nii.gz

MOVING=moving.nii.gz
MOVING_MASK=moving_mask.nii.gz

HISTOLOGY_MULTIPLIER_SRC=hm.nii.gz

#==============================================================================

function backup_masks_from_dropbox {
    cp -v ${FIXED_RAW_MASK}           ${DIRECTORY_POSSUM_MASKS_BACKUP}/mri_registration_mask.nii.gz
    cp -v ${MOVING_RAW_MASK}          ${DIRECTORY_POSSUM_MASKS_BACKUP}/myelin_registration_mask.nii.gz
    cp -v ${HISTOLOGY_MULTIPLIER_RAW} ${DIRECTORY_POSSUM_MASKS_BACKUP}/02_02_NN2_mri_mask_histology_multiplier_straight.nii.gz
}

function travel_to_work_directory {
    WORK_DIR=${JOB_EXECUTION_DIR}/${JOB_IDENTIFIER_PREFIX}
    mkdir -p ${WORK_DIR}
    cp    $0 ${PARAM_FILE} ${WORK_DIR}
    cd ${WORK_DIR}
    
    echo "We are in: `pwd`. Executing."
}

function prepare_datasets {
    cp -v $FIXED_RAW       $FIXED_SRC
    cp -v $FIXED_RAW_MASK  $FIXED_MASK_SRC
    cp -v $MOVING_RAW      $MOVING_SRC
    cp -v $MOVING_RAW_MASK $MOVING_MASK_SRC
    cp -v $HISTOLOGY_MULTIPLIER_RAW          $HISTOLOGY_MULTIPLIER_SRC 
    
    # Prepare fixed images
    c3d -verbose \
        ${FIXED_SRC} -popas fixed \
        ${HISTOLOGY_MULTIPLIER_SRC} -popas hm \
        -clear \
        -push fixed -push hm \
        -times -round -replace 0 255 \
        ${REGION_DEFINITION} \
        -o ${FIXED}

    c3d -verbose \
        ${FIXED_MASK_SRC} \
        -interpolation NearestNeighbor \
        -replace 4 0 2 0 -binarize \
        ${REGION_DEFINITION} \
        -o ${FIXED_MASK}

    c3d -verbose \
        ${FIXED_MASK_SRC} \
        -interpolation NearestNeighbor \
        -replace 4 0 2 0 12 1\
        ${REGION_DEFINITION} \
        -o ${FIXED_SEG}

    cp -v $INITIAL_AFFINE_TRANSFORM_RAW $INITIAL_AFFINE_TRANSFORM
    
    if [ -e ${INITIAL_DEFORMABLE_TRANSFORM_RAW} ]
    then
        c3d -mcs ${INITIAL_DEFORMABLE_TRANSFORM_RAW} -popas z -popas y -popas x -clear \
            ${FIXED} -popas f \
            -push f -push x -reslice-identity -popas fx -clear \
            -push f -push y -reslice-identity -popas fy -clear \
            -push f -push z -reslice-identity -popas fz -clear \
            -push fx -push fy -push fz -omc 3 ${INITIAL_DEFORMABLE_TRANSFORM}
    else
        # Create dummy one
        c3d ${FIXED} -scale 0 -dup -dup -omc 3 ${INITIAL_DEFORMABLE_TRANSFORM}
    fi
}

function list_computed_warps_this_step {
    echo "`ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp" | grep -v "cumulative_Warp"`"
}

function list_computed_warps {
    echo "${INITIAL_DEFORMABLE_TRANSFORM} `list_computed_warps_this_step`"
}

function warp_moving_from_source {
    local OUTPUT_FILENAME=$1
    
    WarpImageMultiTransform 3 \
        ${MOVING_SRC} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} \
        `list_computed_warps` ${INITIAL_AFFINE_TRANSFORM}
}

function warp_mask_from_source {
    local OUTPUT_FILENAME=$1
    
    WarpImageMultiTransform ${IMG_DIM} \
        ${MOVING_RAW_MASK} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} `list_computed_warps` \
        --use-NN
        
    c${IMG_DIM}d -verbose ${OUTPUT_FILENAME} \
        -replace 255 0 4 0 2 0 -binarize -o ${OUTPUT_FILENAME}
}

function warp_segmentation_from_source {
    local OUTPUT_FILENAME=$1
    
    WarpImageMultiTransform ${IMG_DIM} \
        ${MOVING_RAW_MASK} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} `list_computed_warps` \
        --use-NN
    
    c${IMG_DIM}d -verbose ${OUTPUT_FILENAME} \
        -replace 255 0 4 0 2 0 12 1 -o ${OUTPUT_FILENAME}
}

function cumulative_wrap {
    local OUTPUT_FILENAME=$1
   
    ComposeMultiTransform ${IMG_DIM} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} `list_computed_warps`
}

function self_archive {
    tar -cvvzf ${JOB_IDENTIFIER_PREFIX}.tgz .
    mv ${JOB_IDENTIFIER_PREFIX}.tgz ~/backup/
}

function print_calculation_identifier {
    echo "---------------------------------------------------------------------"
    echo "`date` `pwd`"
    echo "---------------------------------------------------------------------"
}

function prepare_iteration {
    local ITERATION=$1
    local WORKING_DIR=${ITERATION_PREFIX}`printf %02d ${ITERATION}`/
    local OUTPUT_PREFIX=${ITERATION_PREFIX}`printf %02d ${ITERATION}`
    
    mkdir -p ${WORKING_DIR}
    
    local PARAM_CC_WEIGHT=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f1 -d" "`
    local PARAM_MSQ_WEIGHT=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f2 -d" "`
    local PARAM_PSE_WEIGHT=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f3 -d" "`
    local PARAM_TRANSFORMATION=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f4 -d" "`
    local PARAM_REGULARIZATION=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f5 -d" "`
    local PARAM_ITERATIONS=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f6 -d" "`
    local PARAM_SMOOTHING_SIGMAS=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f7 -d" " | awk '$1!="FALSE" { print "--gaussian-smoothing-sigmas " $1 }'`
    local PARAM_FIXED_IMAGE_MASK=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f8 -d" " | awk '$1!="FALSE" { print "--mask-image " $1 }'`
    local PARAM_USE_ALL_TO_CONVERGE=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f9 -d" " | awk '$1!="FALSE" { print "--use-all-metrics-for-convergence"}'`
    
    warp_moving_from_source ${WORKING_DIR}/${MOVING}
    warp_mask_from_source   ${WORKING_DIR}/${MOVING_MASK} 
    warp_segmentation_from_source ${WORKING_DIR}/${MOVING_SEG}
    
    print_calculation_identifier 
    
    ANTS ${IMG_DIM} \
        -m PSE[${FIXED},${WORKING_DIR}/${MOVING},${FIXED_SEG},${WORKING_DIR}/${MOVING_SEG},${PARAM_PSE_WEIGHT},1.0,1,0,10]\
        -m MSQ[${FIXED_MASK},${WORKING_DIR}/${MOVING_MASK},${PARAM_MSQ_WEIGHT},0004] \
        -m CC[${FIXED},${WORKING_DIR}/${MOVING},${PARAM_CC_WEIGHT},0005] \
        -t ${PARAM_TRANSFORMATION} \
        -r ${PARAM_REGULARIZATION} \
        -o ${WORKING_DIR}/${OUTPUT_PREFIX} \
        -i ${PARAM_ITERATIONS} \
        --MI-option 32x1600 \
        --number-of-affine-iterations 0 \
        --use-Histogram-Matching \
        --affine-metric-type CC \
        --rigid-affine false ${PARAM_USE_ALL_TO_CONVERGE} ${PARAM_SMOOTHING_SIGMAS} ${PARAM_FIXED_IMAGE_MASK}
    
    local DEFORMED_FILENAME=${WORKING_DIR}/${OUTPUT_PREFIX}Deformed.nii.gz
    local DEFORMED_MASK_FILENAME=${WORKING_DIR}/${OUTPUT_PREFIX}_mask_Deformed.nii.gz
    local DEFORMED_SEGMENTATION_FILENAME=${WORKING_DIR}/${OUTPUT_PREFIX}_seg_Deformed.nii.gz
    local CUMULATIVE_WARP=${WORKING_DIR}/${OUTPUT_PREFIX}_cumulative_Warp.nii.gz
    
    warp_moving_from_source ${DEFORMED_FILENAME}
    warp_mask_from_source   ${DEFORMED_MASK_FILENAME}
    warp_segmentation_from_source ${DEFORMED_SEGMENTATION_FILENAME}
    cumulative_wrap ${CUMULATIVE_WARP}
    
    ANTSJacobian ${IMG_DIM} ${WORKING_DIR}/${OUTPUT_PREFIX}Warp.nii.gz ${WORKING_DIR}/${OUTPUT_PREFIX}_step_
    ANTSJacobian ${IMG_DIM} ${CUMULATIVE_WARP} ${WORKING_DIR}/${OUTPUT_PREFIX}_
    
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${DEFORMED_MASK_FILENAME} -overlap 1 >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${DEFORMED_MASK_FILENAME} -msq  >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${DEFORMED_MASK_FILENAME} -ncor >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED} ${DEFORMED_FILENAME} -ncor >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED} ${DEFORMED_FILENAME} -nmi  >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    LabelOverlapMeasures ${IMG_DIM} ${FIXED_SEG} ${DEFORMED_SEGMENTATION_FILENAME}   >> ${WORKING_DIR}/${OUTPUT_PREFIX}_seg.txt
    
    print_calculation_identifier
    
    # When the last iteration is being processed:
    if [ "$ITERATION" -eq "$ITERATIONLIMIT" ]
    then
        cp -v ${DEFORMED_FILENAME}               ${JOB_IDENTIFIER_PREFIX}_${MOVING}
        cp -v ${DEFORMED_MASK_FILENAME}          ${JOB_IDENTIFIER_PREFIX}_${MOVING_MASK}
        cp -v ${DEFORMED_SEGMENTATION_FILENAME}  ${JOB_IDENTIFIER_PREFIX}_${MOVING_SEG}
        cp -v ${DEFORMED_FILENAME}               ${DROPBOX_PRIV}/${JOB_IDENTIFIER_PREFIX}_${MOVING}
        touch done_`date +%Y-%m-%d-%H-%M`
    fi
}

#backup_masks_from_dropbox
travel_to_work_directory
prepare_datasets
for i in `seq 1 1 ${ITERATIONLIMIT}`
do
    prepare_iteration $i
done
self_archive
