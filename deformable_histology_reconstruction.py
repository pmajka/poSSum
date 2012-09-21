#!/usr/bin/python

import sys, os
import multiprocessing
import subprocess as sub

import time, datetime
from optparse import OptionParser, OptionGroup
import copy

#from pos_parameters import generic_parameter, filename_parameter, string_parameter, list_parameter
from pos_parameters import mkdir_wrapper, rmdir_wrapper, average_images, \
        ants_intensity_meric, ants_registration, ants_reslice, stack_slices_gray_wrapper
from pos_filenames import filename

def execute_callable(callable):
    return callable()

def getBasesame(path, withExtension = False):
    if withExtension == True:
        return os.path.basename(path)
    else:
        return os.path.splitext(os.path.basename(path))[0]

class generic_workflow(object):
    _f = {}
    
    # -----------------------------------------------
    # Directory templates - environmental
    # ----------------------------------------------
    _dirTemplates = {
            'sharedbf': '/dev/shm/',
            'tempbf'  : '/tmp/',
            'specimen_dir' : 'data',
            'processing_group_dir' : 'Undefined',
            }
     
    _usage = ""
    
    def __init__(self, options, args, pool = None):
        self.options = options
        self.args = args
        
        self.f = dict(self._f)
        
        # If no cpu pool is provided, create and 
        # assign a new pool
        if pool:
            self.pool = pool
        else:
            self.pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        
        self._initializeOptions()
        self._initializeDirectories()
        self._overrideDefaults()
    
    def _initializeOptions(self):
        """
        There is not many to process or initialize. Actually only jobID (if not
        provided) is processed automatically.
        """
        try:
            self.options.specimenId
        except:
            print >>sys.stderr, "No specimen ID provided. Please provide a specimen ID."
            sys.exit(1)
        
        if self.options.jobId == None:
            self.options.jobId  = self.__class__.__name__
            self.options.jobId += datetime.datetime.now().strftime("_%Y-%m-%d-%H_%M-%S_")
            self.options.jobId += str(os.getpid())
    
    def _overrideDefaults(self):
        pass
    
    def _initializeDirectories(self):
        """
        """
        # That's clever idea: When one don't want (or cannot) use shared memory,
        # the regular /tmp/ directory is used to support the computations.
        if self.options.disableSharedMemory:
           top_directory = self._dirTemplates['tempbf']
        else:
           top_directory = self._dirTemplates['sharedbf']
        # Ok, so that was for the very top directory
        
        # If the working directory (the directory holding all the 
        # job's calculations) is not defined, we define it automatically
        # When the working directory name IS provided we just use it
        if not self.options.workdir:
            self.options.workdir =  os.path.join(top_directory, self.options.jobId)
        self._ensureDir(self.options.workdir) 
        
        # Assign path to work dir to all templates:
        for k,v in self.f.iteritems():
            v.job_dir = self.options.workdir
        
        dirs_to_create = list(set(map(lambda v: v.base_dir,  self.f.itervalues())))
        map(self._ensureDir, dirs_to_create)
    
    def _ensureDir(self, path):
        return mkdir_wrapper(dir_list = [path])()
    
    def _rmdir(self, path):
        return rmdir_wrapper(dir_list = [path])()
    
    def _basesame(self, path, withExtension = False):
        return getBasesame(path, withExtension)
    
    def _cleanUp(self, immediate = False):
        self._rmdir(self.options.workdir)
    
    @classmethod
    def _getCommandLineParser(cls):
        
        parser = OptionParser(usage = cls._usage)
       
        workflowSettings = OptionGroup(parser, 'General workflow settings')
        workflowSettings.add_option('--jobId', '-j', dest='jobId', type='str',
                default=None, help='Job identifier')
        workflowSettings.add_option('--workDir', '-d', dest='workdir', type='str',
                default=None, help='Working directory')
        workflowSettings.add_option('--log', dest='log', type='str',
                default='WARNING', help='Loglevel: CRITICAL | ERROR | WARNING | INFO | DEBUG')
        workflowSettings.add_option('--logFilename', dest='logFilename',
                default=None, action='store', type='str',
                help='Sets printing log to stderr instead to a file')
        workflowSettings.add_option('--cleanup', default=False,
                dest='cleanup', action='store_const', const=True,
                help='Remove all temponary direcotries.')
        workflowSettings.add_option('--disableSharedMemory', default=False,
            dest='disableSharedMemory', action='store_const', const=True,
            help='Forces script to write data on the hard drive instaed of using shared memory')
        workflowSettings.add_option('--specimenId', '-s', default=None,
                dest='specimenId', action='store', type='str',
                help='Identifier of processed specimen')
        
        parser.add_option_group(workflowSettings)
        return parser
    
    @classmethod
    def parseArgs(cls):
        parser = cls._getCommandLineParser()
        (options, args) = parser.parse_args()
        return (options, args)

class deformable_reconstruction_iteration(generic_workflow):
    _f = { \
        'src_slice'  : filename('src_slice',  work_dir = '00_src_slices',      str_template =  '{idx:04d}.nii.gz'),
        'processed'  : filename('processed',  work_dir = '01_process_slices',  str_template =  '{idx:04d}.nii.gz'),
        'labelling'  : filename('labelling',  work_dir = '02_labelling',       str_template =  '{idx:04d}.nii.gz'),
        'transform'  : filename('transform',  work_dir = '11_transformations', str_template =  '{idx:04d}Warp.nii.gz'),
        'out_naming' : filename('out_naming', work_dir = '11_transformations', str_template = '{idx:04d}')
        }
    
    _usage = ""
    
    def get_weight(self, i, j):
        return 1
    
    def _assign_weights(self):
        start = self.options.startSlice
        end = self.options.endSlice
        eps = self.options.neighbourhood
        
        self.weights = {}
        for i in range(start, end +1):
            for j in range(i - eps, i + eps+1):
                if j!=i and j<=end and j>=start:
                    self.weights[(i,j)] = self.get_weight(i,j)
    
    def _average_images(self):
        start = self.options.startSlice
        end = self.options.endSlice
        eps = self.options.neighbourhood
        
        commands = []
        
        for i in range(start, end +1):
            files_to_average = []
            
            for j in range(i - eps, i + eps+1):
                if j!=i and j<=end and j>=start:
                   files_to_average.append(self.f['src_slice'](idx=j))
            
            command = average_images(dimension = 2,
                               input_images = files_to_average,
                               output_image = self.f['processed'](idx=i))
            commands.append(copy.deepcopy(command))
        
        self.pool.map(execute_callable, commands)
    
    def _calculate_transformations(self):
        start = self.options.startSlice
        end = self.options.endSlice
        eps = self.options.neighbourhood
        
        commands = []
        metrics = []
        
        for i in range(start, end +1):
            metric = ants_intensity_meric(
                        fixed_image  = self.f['processed'](idx=i),
                        moving_image = self.f['src_slice'](idx=i),
                        metric = self.options.antsImageMetric,
                        weight = 1,
                        parameter = self.options.antsImageMetricOpt)
            
            registration = ants_registration(
                        dimension = 2,
                        outputNaming = self.f['out_naming'](idx=i),
                        iterations = self.options.antsIterations,
                        transformation = ('SyN', [self.options.antsTransformation]),
                        regularization = (self.options.antsRegularizationType, self.options.antsRegularization),
                        affineIterations = [0],
                        continueAffine = False,
                        rigidAffine = False,
                        imageMetrics = [metric])
            
            commands.append(copy.deepcopy(registration))
        
        self.pool.map(execute_callable, commands)
    
    def launch(self):
        self._assign_weights()
        self._average_images()
        self._calculate_transformations()
     
    def __call__(self, *args, **kwargs):
        return self.launch()
    
class deformable_reconstruction_workflow(generic_workflow):
    _f = { \
        'init_slice' : filename('init_slice', work_dir = '01_init_slices', str_template = '{idx:04d}.nii.gz'),
        'iteration'  : filename('iteraltion', work_dir = '05_iterations',  str_template = '{iter:04d}'),
        'iteration_out_naming' : filename('iteration_out_naming', work_dir = '05_iterations', str_template = '{iter:04d}/11_transformations/{idx:04d}'),
        'iteration_transform'  : filename('iteration_transform', work_dir = '05_iterations', str_template =  '{iter:04d}/11_transformations/{idx:04d}Warp.nii.gz'),
        'iteration_resliced'   : filename('iteration_resliced' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/'),
        'iteration_resliced_slice' : filename('iteration_resliced_slice' , work_dir = '05_iterations', str_template  = '{iter:04d}/21_resliced/{idx:04d}.nii.gz'),
        'inter_res'  : filename('inter_res',  work_dir = '08_intermediate_results', str_template = ''),
        'tmp_gray_vol' : filename('tmp_gray_vol', work_dir = '08_intermediate_results', str_template = '__temp__vol__gray.vtk'),
        'inter_res_gray_vol'   : filename('inter_res_gray_vol',   work_dir = '08_intermediate_results', str_template = 'intermediate_{iter:04d}.nii.gz'),
        'iteration_stack_mask' : filename('iteration_stack_mask', work_dir = '05_iterations', str_template = '{iter:04d}/21_resliced/????.nii.gz')
        }
    
    _usage = ""
    
    def prepare_slices(self):
        pass
    
    def transform(self):
        pass
    
    def intermediate_results(self):
        pass
    
    def launch(self):
        """
        """
        for iteration in range(self.options.iterations):
            self.current_iteration = iteration
            
            step_options = copy.deepcopy(self.options)
            step_args = copy.deepcopy(self.args)
            
            step_options.workdir = os.path.join(self.f['iteration'](iter=iteration))
            single_step = deformable_reconstruction_iteration(step_options, step_args, pool = self.pool)
            
            if iteration == 0:
                single_step.f['src_slice'].override_dir = self.f['init_slice'].base_dir
            else:
                single_step.f['src_slice'].override_dir = self.f['iteration_resliced'](iter=iteration-1)
            
            # Do registration
            single_step()
            self._reslice() 
            self._stack_intermediate()
            
            # Reslice registration results
    
    def _reslice(self):
        start = self.options.startSlice
        end = self.options.endSlice
        iteration = self.current_iteration
        
        commands = []
        for i in range(start, end +1):
            deformable_list = map(lambda j: self.f['iteration_transform'](idx=i,iter=j), range(iteration+1))
            moving_image = self.f['init_slice'](idx=i)
            
            command = ants_reslice(
                    dimension = 2,
                    moving_image = moving_image,
                    output_image = self.f['iteration_resliced_slice'](idx=i,iter=iteration),
                    reference_image = moving_image,
                    deformable_list = deformable_list,
                    affine_list = [])
            commands.append(copy.deepcopy(command))
        
        self.pool.map(execute_callable, commands)
    
    def _stack_intermediate(self):
        iteration = self.current_iteration
        
        stack_grayscale =  stack_slices_gray_wrapper(
                temp_volume_fn = self.f['tmp_gray_vol'](),
                output_volume_fn = self.f['inter_res_gray_vol'](iter=iteration),
                stack_mask = self.f['iteration_stack_mask'](iter=iteration),
                permutation_order = self.options.outputVolumePermutationOrder,
                orientation_code = self.options.outputVolumeOrientationCode,
                output_type = self.options.outputVolumeScalarType,
                spacing = self.options.outputVolumeSpacing,
                origin = self.options.outputVolumeOrigin,
                interpolation = self.options.setInterpolation,
                resample = self.options.outputVolumeResample)
        stack_grayscale()
    
    def prepare_calculations(self):
        pass
    
    def process_results(self):
        pass
    
    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()
        
        parser.add_option('--startSlice', default=0,
                type='int', dest='startSlice',
                help='Index of the first slice of the stack')
        parser.add_option('--endSlice', default=None,
                type='int', dest='endSlice',
                help='Index of the last slice of the stack')
        parser.add_option('--neighbourhood', default=1, type='int',
                dest='neighbourhood',  help='Epsilon')
        parser.add_option('--iterations', default=10,
                type='int', dest='iterations',
                help='Number of iterations')
        parser.add_option('--inputVolume','-i', default=None,
                type='str', dest='inputVolume',
                help='Input grayscale volume to be reconstructed')
#       parser.add_option('--labelledVolume','-l', default=None,
#               type='str', dest='labelledVolume',
#               help='Labels for driving the registration')
#       parser.add_option('--maskedVolume','-m', default=None,
#               type='str', dest='maskedVolume',
#               help='Slice mask for driving the registration')
        parser.add_option('--inputSlicesDir', default = None,
                type='str', dest = 'inputSlicesDir',
                help = 'Directory with the input slices')
        
        regSettings = \
                OptionGroup(parser, 'Registration setttings.')
        
        regSettings.add_option('--antsImageMetric', default='CC',
                type='str', dest='antsImageMetric',
                help='ANTS image to image metric. See ANTS documentation.')
        regSettings.add_option('--antsImageMetricOpt', default=8,
                type='int', dest='antsImageMetricOpt',
                help='Parameter of ANTS i2i metric.')
        regSettings.add_option('--antsTransformation', default=0.15, type='float',
                dest='antsTransformation', help='Tranformations gradient step.'),
        regSettings.add_option('--antsRegularizationType', default='Gauss',
                type='str', dest='antsRegularizationType',
                help='Ants regulatization type.')
        regSettings.add_option('--antsRegularization', default=[3.0,1.0],
                type='float', nargs =2, dest='antsRegularization',
                help='Ants regulatization.')
        regSettings.add_option('--antsIterations', default=[100]*5,
                type='int', nargs = 5, dest='antsIterations',
                help='Number of deformable registration iterations.')
        
        outputVolumeSettings = \
                OptionGroup(parser, 'OutputVolumeSettings.')
        outputVolumeSettings.add_option('--outputVolumeOrigin', dest='outputVolumeOrigin',
                default=[0.,0.,0.], action='store', type='float', nargs =3, help='')
        outputVolumeSettings.add_option('--outputVolumeScalarType', default='uchar',
                type='str', dest='outputVolumeScalarType', 
                help='Data type for output volume\'s voxels. Allowed values: char | uchar | short | ushort | int | uint | float | double')
        outputVolumeSettings.add_option('--outputVolumeSpacing', default=[1,1,1],
            type='float', nargs=3, dest='outputVolumeSpacing',
            help='Spacing of the output volume in mm (both grayscale and color volume).')
        outputVolumeSettings.add_option('--outputVolumeResample',
                          dest='outputVolumeResample', type='float', nargs=3, default=None,
                          help='Apply additional resampling to the volume')
        outputVolumeSettings.add_option('--outputVolumePermutationOrder', default=[0,1,2],
            type='int', nargs=3, dest='outputVolumePermutationOrder',
            help='Apply axes permutation. Permutation has to be provided as sequence of 3 integers separated by space. Identity (0,1,2) permutation is a default one.')
        outputVolumeSettings.add_option('--outputVolumeOrientationCode',  dest='outputVolumeOrientationCode', type='str',
                default='RAS', help='')
        outputVolumeSettings.add_option('--grayscaleVolumeFilename',  dest='grayscaleVolumeFilename',
                type='str', default=None)
        outputVolumeSettings.add_option('--rgbVolumeFilename',  dest='rgbVolumeFilename',
                type='str', default=None)
        outputVolumeSettings.add_option('--setInterpolation',
                          dest='setInterpolation', type='str', default=None,
                          help='<NearestNeighbor|Linear|Cubic|Sinc|Gaussian>')
        
        parser.add_option_group(regSettings)
        parser.add_option_group(outputVolumeSettings)
        
        return parser

if __name__ == '__main__':
    options, args = deformable_reconstruction_workflow.parseArgs()
    d = deformable_reconstruction_workflow(options, args)
    d.launch()
    d.pool.close()
    d.pool.join()
