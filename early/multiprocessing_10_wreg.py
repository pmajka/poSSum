import os, sys
from multiprocessing_9_wreg import antsIntensityMetric, antsLinearRegistrationWrapper, \
       antsReslice, averageImages

eps   = int(sys.argv[4])
start = 0
end   = 260

dirdic = {}
dirdic['src_slices'] = '02_source_slices'
dirdic['prc_slices'] = '03_process_slices'
dirdic['transf']     = '04_transformations'
dirdic['resliced']   = '05_resliced_grayscale'

prefix = 'iteration_%04d' % int(sys.argv[6])
metricName = str(sys.argv[1])
metricParam  = int(sys.argv[2])
regural = tuple(map(float, sys.argv[3]))

tplt = {}
tplt['file_to_average'] = os.path.join(prefix, dirdic['src_slices'], "%04d.png")
tplt['weighted_out']    = os.path.join(prefix, dirdic['prc_slices'], "w%04d.png")
tplt['moving_images']   = os.path.join(prefix, dirdic['prc_slices'], "%04d.png")
tplt['out_prefix']      = os.path.join(prefix, dirdic['transf'])

dirdic['src_slices'] = '02_source_slices'
dirdic['prc_slices'] = '03_process_slices'
dirdic['transf']     = '04_transformations'
dirdic['resliced']   = '05_resliced_grayscale'


# --------------------------------
# Define registration parameters

def _get_images_to_average(slice_index):
    i = sliced_index
    
    images_to_average = []
    for j in range(i - eps, i + eps+1):
        if j >= start and j <= end and i!=j:
            images_to_average.append(tplt['file_to_average'] % j)
    
    return images_to_average

def _get_target_images():
    return self._get_images_to_average()

registrationParameters = { \
        'transformation' : ('SyN', (0.15,)),
        'regularization' : ('Gauss', regular)
        }

metricParameters = { \
        'wieght' : 1,
        'param'  : metricParam,
        'metric' : metricName
        }

for i in range(start, end + 1):
    for j in range(i - eps, i + eps+1):
        if j >= start and j <= end and i!=j:
            ww

