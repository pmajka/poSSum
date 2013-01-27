PROGPATH=/opt/ANTs-1.9.y-Linux/bin/
JOB_EXECUTION_DIR=${HOME}/possum/testy/

OUTPUT_SPACING=0.08x0.08x0.08mm
OUTPUT_SPACING=0.1x0.1x0.1mm
#OUTPUT_SPACING=0.05x0.05x0.05mm
SLICE_RESAMPLED_PLANE='y'
SLICE_RESAMPLED_SLICE='150'

#REGION_DEFINITION='-region 00%x30%x00% 100%x5%x100%'
#REGION_DEFINITION="-slice ${SLICE_RESAMPLED_PLANE} ${SLICE_RESAMPLED_SLICE}"
#REGION_DEFINITION=" "

IMG_DIM=3
PARAM_FILE=$1
JOB_IDENTIFIER_PREFIX=deformable_registration_`date +%Y-%m-%d-%H-%M`_${BASHPID}_
ITERATIONLIMIT=$[`wc -l ${PARAM_FILE} | cut -f1 -d" "`-1]


DROPBOX=/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/
DROPBOX_PRIV=/home/pmajka/Dropbox/

FIXED_RAW=${DROPBOX}/02_02_NN2_mri.nii.gz
FIXED_RAW_MASK=${DROPBOX}/mri_registration_mask.nii.gz

#MOVING_RAW=${DROPBOX}/myelin.nii.gz
MOVING_RAW=${DROPBOX}/02_02_NN2_deformable_hist_reconstruction_myelin_resliced.nii.gz
MOVING_RAW_MASK=${DROPBOX}/myelin_registration_mask.nii.gz

HISTOLOGY_MULTIPLIER_RAW=${DROPBOX}/02_02_NN2_mri_mask_histology_multiplier_straight.nii.gz

ITERATION_PREFIX=iteration_
INITIAL_AFFINE_TRANSFORM_RAW=~/possum/processing_supplement/02_02_NN2_histology_myelin_to_straight_mri_affine.txt
INITIAL_DEFORMABLE_TRANSFORM_RAW=/home/pmajka/possum/testy/myelin_to_mri_step2_attempt_0/05_registration_raw/f__m__CC0005_SyN0.35_Gauss0,0_i1000x1000_mi32x1600_afi0_rigidfalse_amt_CC_psep1.0_psew1.000000_mw1.000000_ccw0.000000_syni02_syns0.010000_Warp.nii.gz

INITIAL_DEFORMABLE_TRANSFORM=initial_Warp.nii.gz
INITIAL_AFFINE_TRANSFORM=initial_Affine.txt

#==============================================================================
# Naming conventions. Not really for configuration.
#

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

function travel_to_work_directory {
    WORK_DIR=${JOB_EXECUTION_DIR}/${JOB_IDENTIFIER_PREFIX}
    mkdir -p ${WORK_DIR}
    cp    $0 ${PARAM_FILE} ${WORK_DIR}
    cd ${WORK_DIR}
    
    echo "We are in: `pwd`. Executing."
    sleep 5
}

function prepare_datasets {
    cp -v $FIXED_RAW       $FIXED_SRC
    cp -v $FIXED_RAW_MASK  $FIXED_MASK_SRC
    cp -v $MOVING_RAW      $MOVING_SRC
    cp -v $MOVING_RAW_MASK $MOVING_MASK_SRC
    cp -v $HISTOLOGY_MULTIPLIER_RAW          $HISTOLOGY_MULTIPLIER_SRC 
    cp -v $INITIAL_AFFINE_TRANSFORM_RAW $INITIAL_AFFINE_TRANSFORM
    cp -v $INITIAL_DEFORMABLE_TRANSFORM_RAW $INITIAL_DEFORMABLE_TRANSFORM
    
    # Prepare fixed images
    c3d -verbose \
        ${FIXED_SRC} -popas fixed \
        ${HISTOLOGY_MULTIPLIER_SRC} -popas hm \
        -clear \
        -push fixed -push hm \
        -times -round -replace 0 255 -type uchar \
        -resample-mm ${OUTPUT_SPACING} \
        ${REGION_DEFINITION} \
        -o ${FIXED}

    c3d -verbose \
        ${FIXED_MASK_SRC} \
        -interpolation NearestNeighbor \
        -resample-mm ${OUTPUT_SPACING} \
        -replace 4 0 2 0 -binarize \
        ${REGION_DEFINITION} \
        -o ${FIXED_MASK}

    c3d -verbose \
        ${FIXED_MASK_SRC} \
        -interpolation NearestNeighbor \
        -resample-mm ${OUTPUT_SPACING} \
        -replace 4 0 2 0\
        ${REGION_DEFINITION} \
        -o ${FIXED_SEG}
}

function warp_moving_from_source {
    local OUTPUT_FILENAME=$1
    
    WarpImageMultiTransform 3 \
        ${MOVING_SRC} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} \
        ${INITIAL_DEFORMABLE_TRANSFORM} `ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp"` ${INITIAL_AFFINE_TRANSFORM}
}

function warp_mask_from_source {
    local OUTPUT_FILENAME=$1
    
    WarpImageMultiTransform ${IMG_DIM} \
        ${MOVING_RAW_MASK} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} \
        ${INITIAL_DEFORMABLE_TRANSFORM} `ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp"` \
        --use-NN
        
    c${IMG_DIM}d -verbose ${WORKING_DIR}/${MOVING_MASK} \
        -replace 255 0 4 0 2 0 -binarize -o ${WORKING_DIR}/${MOVING_MASK}
}

function warp_segmentation_from_source {
    local OUTPUT_FILENAME=$1
    
    WarpImageMultiTransform ${IMG_DIM} \
        ${MOVING_RAW_MASK} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} \
        ${INITIAL_DEFORMABLE_TRANSFORM} `ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp"` \
        --use-NN
    
    c${IMG_DIM}d -verbose ${WORKING_DIR}/${MOVING_SEG} \
        -replace 255 0 4 0 2 0 -o ${WORKING_DIR}/${MOVING_SEG}
}

function cumulative_wrap {
    local OUTPUT_FILENAME=$1
    
    WarpImageMultiTransform ${IMG_DIM} \
        ${OUTPUT_FILENAME} \
        -R ${FIXED} \
        ${INITIAL_DEFORMABLE_TRANSFORM} `ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp"`
}

function self_archive {
    tar -cvvzf ${JOB_IDENTIFIER_PREFIX}.tgz .
    mv ${JOB_IDENTIFIER_PREFIX}.tgz ~/backup/
}

function determine_smoothing_sigmas {
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
#   local PARAM_SMOOTHING_SIGMAS=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f7 -d" " | awk '$1!="FALSE" { print "--smoothing-sigmas " $1 }'`
#   local PARAM_FIXED_IMAGE_MASK=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f8 -d" " | awk '$1!="FALSE" { print "--mask-image " $1 }'`
    
    warp_moving_from_source ${WORKING_DIR}/${MOVING}
    warp_mask_from_source   ${WORKING_DIR}/${MOVING_MASK} 
    warp_segmentation_from_source ${WORKING_DIR}/${MOVING_SEG}
    
    echo "---------------------------------------------------------------------"
    echo "`date` `pwd`"
    echo "---------------------------------------------------------------------"
    
    ANTS ${IMG_DIM} \
        -m CC[${FIXED},${WORKING_DIR}/${MOVING},           ${PARAM_CC_WEIGHT},0005] \
        -m MSQ[${FIXED_MASK},${WORKING_DIR}/${MOVING_MASK},${PARAM_MSQ_WEIGHT},0004] \
        -m PSE[${FIXED},${WORKING_DIR}/${MOVING},${FIXED_SEG},${WORKING_DIR}/${MOVING_SEG},${PARAM_PSE_WEIGHT},1.0,1,0,10]\
        -t ${PARAM_TRANSFORMATION} -r ${PARAM_REGULARIZATION} \
        -o ${WORKING_DIR}/${OUTPUT_PREFIX} \
        -i ${PARAM_ITERATIONS} \
        --MI-option 32x1600 \
        --number-of-affine-iterations 0 \
        --use-Histogram-Matching \
        --affine-metric-type CC \
        --rigid-affine false \
        --use-all-metrics-for-convergence
    
    local DEFORMED_FILENAME=${WORKING_DIR}/${OUTPUT_PREFIX}Deformed.nii.gz
    local DEFORMED_MASK_FILENAME=${WORKING_DIR}/${OUTPUT_PREFIX}_mask_Deformed.nii.gz
    local DEFORMED_SEGMENTATION_FILENAME=${WORKING_DIR}/${OUTPUT_PREFIX}_seg_Deformed.nii.gz
    local CUMULATIVE_WARP=${WORKING_DIR}/${OUTPUT_PREFIX}_cumulative_Warp.nii.gz
    
    warp_moving_from_source ${DEFORMED_FILENAME}
    warp_mask_from_source   ${DEFORMED_MASK_FILENAME}
    warp_segmentation_from_source ${DEFORMED_SEGMENTATION_FILENAME}
    cumulative_wrap ${CUMULATIVE_WARP}
    ANTSJacobian ${IMG_DIM} ${CUMULATIVE_WARP} ${WORKING_DIR}/${OUTPUT_PREFIX}_
    
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${DEFORMED_MASK_FILENAME} -overlap 1 >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${DEFORMED_MASK_FILENAME} -msq  >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${DEFORMED_MASK_FILENAME} -ncor >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED} ${DEFORMED_FILENAME} -ncor >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED} ${DEFORMED_FILENAME} -nmi  >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    LabelOverlapMeasures ${IMG_DIM} ${FIXED_SEG} ${DEFORMED_SEGMENTATION_FILENAME}   >> ${WORKING_DIR}/${OUTPUT_PREFIX}_seg.txt
    
    echo "---------------------------------------------------------------------"
    echo "`date` `pwd`"
    echo "---------------------------------------------------------------------"
    
    # When the last iteration is being processed:
    if [ "$ITERATION" -eq "$ITERATIONLIMIT" ]
    then
        cp -v ${DEFORMED_FILENAME}               ${JOB_IDENTIFIER_PREFIX}_${MOVING}
        cp -v ${DEFORMED_MASK_FILENAME}          ${JOB_IDENTIFIER_PREFIX}_${MOVING_MASK}
        cp -v ${DEFORMED_SEGMENTATION_FILENAME}  ${JOB_IDENTIFIER_PREFIX}_${MOVING_SEG}
        cp -v ${DEFORMED_FILENAME}               ${DROPBOX_PRIV}/${JOB_IDENTIFIER_PREFIX}_${MOVING}
    fi
}

travel_to_work_directory
prepare_datasets
for i in `seq 1 1 ${ITERATIONLIMIT}`
do
    prepare_iteration $i
done
self_archive
