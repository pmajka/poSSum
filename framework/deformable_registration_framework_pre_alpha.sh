PROGPATH=/opt/ANTs-1.9.y-Linux/bin/

OUTPUT_SPACING=0.1x0.1x0.1mm
#OUTPUT_SPACING=0.05x0.05x0.05mm
SLICE_RESAMPLED_PLANE='y'
SLICE_RESAMPLED_SLICE='150'

#REGION_DEFINITION='-region 00%x30%x00% 100%x5%x100%'
#REGION_DEFINITION="-slice ${SLICE_RESAMPLED_PLANE} ${SLICE_RESAMPLED_SLICE}"
#REGION_DEFINITION=" "

IMG_DIM=3
ITERATIONLIMIT=5

DROPBOX=/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/

FIXED_RAW=${DROPBOX}/02_02_NN2_mri.nii.gz
FIXED_RAW_MASK=${DROPBOX}/mri_registration_mask.nii.gz

#MOVING_RAW=${DROPBOX}/myelin.nii.gz
MOVING_RAW=${DROPBOX}/02_02_NN2_deformable_hist_reconstruction_myelin_resliced.nii.gz
MOVING_RAW_MASK=${DROPBOX}/myelin_registration_mask.nii.gz

HISTOLOGY_MULTIPLIER_RAW=${DROPBOX}/02_02_NN2_mri_mask_histology_multiplier_straight.nii.gz

ITERATION_PREFIX=iteration_
INITIAL_AFFINE_TRANSFORM_RAW=~/possum/processing_supplement/02_02_NN2_histology_myelin_to_straight_mri_affine.txt
INITIAL_DEFORMABLE_TRANSFORM_RAW=/home/pmajka/possum/testy/myelin_to_mri_step2_attempt_0/05_registration_raw/f__m__CC0005_SyN0.35_Gauss0,0_i1000x1000_mi32x1600_afi0_rigidfalse_amt_CC_psep1.0_psew1.000000_mw1.000000_ccw0.000000_syni02_syns0.010000_Warp.nii.gz

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
function prepare_datasets {

    cp -v $FIXED_RAW       $FIXED_SRC
    cp -v $FIXED_RAW_MASK  $FIXED_MASK_SRC
    cp -v $MOVING_RAW      $MOVING_SRC
    cp -v $MOVING_RAW_MASK $MOVING_MASK_SRC
    cp -v $HISTOLOGY_MULTIPLIER_RAW          $HISTOLOGY_MULTIPLIER_SRC 
    cp -v $INITIAL_AFFINE_TRANSFORM_RAW $INITIAL_AFFINE_TRANSFORM
    cp -v $INITIAL_DEFORMABLE_TRANSFORM_RAW $INITIAL_DEFORMABLE_TRANSFORM
    
    #==============================================================================
    
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
#==============================================================================
# Prepare iteration 0

function prepare_iteration {
    local ITERATION=$1
    local WORKING_DIR=${ITERATION_PREFIX}`printf %02d ${ITERATION}`/
    local OUTPUT_PREFIX=${ITERATION_PREFIX}`printf %02d ${ITERATION}`
    
    mkdir -p ${WORKING_DIR}
    
    local PARAM_FILE=parameters
    local PARAM_CC_WEIGHT=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f1 -d" "`
    local PARAM_MSQ_WEIGHT=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f2 -d" "`
    local PARAM_PSE_WEIGHT=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f3 -d" "`
    local PARAM_TRANSFORMATION=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f4 -d" "`
    local PARAM_REGULARIZATION=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f5 -d" "`
    local PARAM_ITERATIONS=`sed -n "$[$ITERATION+1] p" ${PARAM_FILE} | cut -f6 -d" "`
    
    WarpImageMultiTransform 3 \
        ${MOVING_SRC} \
        ${WORKING_DIR}/${MOVING} \
        -R ${FIXED} \
        ${INITIAL_DEFORMABLE_TRANSFORM} `ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp"` ${INITIAL_AFFINE_TRANSFORM}
    
    WarpImageMultiTransform ${IMG_DIM} \
        ${MOVING_RAW_MASK} \
        ${WORKING_DIR}/${MOVING_MASK} \
        -R ${FIXED} \
        ${INITIAL_DEFORMABLE_TRANSFORM} `ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp"` \
        --use-NN
        
    c${IMG_DIM}d -verbose ${WORKING_DIR}/${MOVING_MASK} \
        -replace 255 0 4 0 2 0 -binarize -o ${WORKING_DIR}/${MOVING_MASK}
    
    WarpImageMultiTransform ${IMG_DIM} \
        ${MOVING_RAW_MASK} \
        ${WORKING_DIR}/${MOVING_SEG} \
        -R ${FIXED} \
        ${INITIAL_DEFORMABLE_TRANSFORM} `ls ${ITERATION_PREFIX}*/*Warp.nii.gz | grep -v "InverseWarp"` \
        --use-NN
    
    c${IMG_DIM}d -verbose ${WORKING_DIR}/${MOVING_SEG} \
        -replace 255 0 4 0 2 0 -o ${WORKING_DIR}/${MOVING_SEG}
    
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
    
    WarpImageMultiTransform ${IMG_DIM} ${WORKING_DIR}/${MOVING} ${WORKING_DIR}/${OUTPUT_PREFIX}Deformed.nii.gz -R ${FIXED} \
        ${WORKING_DIR}/${OUTPUT_PREFIX}Warp.nii.gz
    WarpImageMultiTransform ${IMG_DIM} ${WORKING_DIR}/${MOVING_MASK} ${WORKING_DIR}/${OUTPUT_PREFIX}_mask_Deformed.nii.gz -R ${FIXED} --use-NN \
        ${WORKING_DIR}/${OUTPUT_PREFIX}Warp.nii.gz
    WarpImageMultiTransform ${IMG_DIM} ${WORKING_DIR}/${MOVING_SEG} ${WORKING_DIR}/${OUTPUT_PREFIX}_seg_Deformed.nii.gz -R ${FIXED} --use-NN \
        ${WORKING_DIR}/${OUTPUT_PREFIX}Warp.nii.gz
    
    ANTSJacobian ${IMG_DIM} ${WORKING_DIR}/${OUTPUT_PREFIX}Warp.nii.gz ${WORKING_DIR}/${OUTPUT_PREFIX}_

    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${WORKING_DIR}/${OUTPUT_PREFIX}_mask_Deformed.nii.gz -overlap 1 >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${WORKING_DIR}/${OUTPUT_PREFIX}_mask_Deformed.nii.gz -msq  >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED_MASK} ${WORKING_DIR}/${OUTPUT_PREFIX}_mask_Deformed.nii.gz -ncor >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED} ${WORKING_DIR}/${OUTPUT_PREFIX}Deformed.nii.gz -ncor >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    /opt/c3d-0.8.2-Linux-x86_64/bin/c${IMG_DIM}d ${FIXED} ${WORKING_DIR}/${OUTPUT_PREFIX}Deformed.nii.gz -nmi  >> ${WORKING_DIR}/${OUTPUT_PREFIX}_eval.txt
    LabelOverlapMeasures ${IMG_DIM} ${FIXED_SEG} ${WORKING_DIR}/${OUTPUT_PREFIX}_seg_Deformed.nii.gz           >> ${WORKING_DIR}/${OUTPUT_PREFIX}_seg.txt

}

prepare_datasets
for i in `seq 1 1 ${ITERATIONLIMIT}`
do
    prepare_iteration $i
done
