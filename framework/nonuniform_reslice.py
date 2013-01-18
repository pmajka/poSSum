import os
import sys

import copy
import numpy as np
from scipy.interpolate import interp1d
from optparse import OptionParser, OptionGroup

from pos_parameters import generic_wrapper, filename_parameter, string_parameter, \
                           list_parameter, value_parameter,\
                           stack_slices_gray_wrapper, stack_slices_rgb_wrapper
from pos_wrapper_skel import generic_workflow
from pos_filenames import filename

class average_grayscale_images_list(generic_wrapper):
    _template = """c{dimension}d -verbose \
                    {input_image_1} {input_image_2} \
                    -weighted-sum {weight_1} {weight_2} \
                    -o {output_image}"""

    _parameters = {
        'dimension'    : value_parameter('dimension', 2),
        'weight_1'     : value_parameter('weight_1', None),
        'weight_2'     : value_parameter('weight_2', None),
        'input_image_1': filename_parameter('input_image_1', None),
        'input_image_2': filename_parameter('input_image_2', None),
        'output_image' : filename_parameter('output_image', None)
         }


class average_multichannel_images_list(generic_wrapper):
    _template = """c{dimension}d -verbose \
        -mcs {input_image_1}  -popas iblue -popas igreen -popas ired -clear \
        -mcs {input_image_2}  -popas oblue -popas ogreen -popas ored -clear \
        -clear \
        -push iblue  -push oblue   -weighted-sum {weight_1} {weight_2} -type uchar -popas bblue \
        -push igreen -push ogreen  -weighted-sum {weight_1} {weight_2} -type uchar -popas bgreen \
        -push ired   -push ored    -weighted-sum {weight_1} {weight_2} -type uchar -popas bred \
        -clear \
        -push bred -push bgreen -push bblue \
        -omc 3 {output_image}"""

    _parameters = {
        'dimension'    : value_parameter('dimension', 2),
        'weight_1'     : value_parameter('weight_1', None),
        'weight_2'     : value_parameter('weight_2', None),
        'input_image_1': filename_parameter('input_image_1', None),
        'input_image_2': filename_parameter('input_image_2', None),
        'output_image' : filename_parameter('output_image', None)
         }


class nonuniform_relice(generic_workflow):
    """
    Workflow to mappin nonuniformly spaced slices to a grid of regular spacing.
    
    python nonuniform_reslice.py \
        --referenceCoordinates /home/pmajka/the_whole_brain_connectivity_atlas/data/merge/R601_reference_planes \
        --probingCoordinates planes_reference \
        --negateReferenceCoordinates \
        --skipOutputVolumeGeneration \
        --useMultichannelWorkflow \
        --referenceInputDirectory /home/pmajka/the_whole_brain_connectivity_atlas/data/merge/R601/ \
        --interpolation nearest \
        --outputVolumeScalarType uchar \
        --outputVolumeSpacing 0.017062 0.04 0.017062 \
        --outputVolumeOrigin -9.622 -7.92 1.444 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeOrientationCode RAS \
        --rgbVolumeFilename /home/pmajka/601.nii.gz 
        
        #    --dryRun 
        #    --cleanup
        #    --useGrayscaleWorkflow \
        #    --useGrayscaleWorkflow \
        #    --useMultichannelWorkflow \
        #    --outputWeightedSlicesDir /home/pmajka/ \
    """
    _f = {
        'ref_input': filename('ref_input', work_dir='01_reference_input', str_template='{idx:04d}.png'),
        'ref_mask':  filename('ref_mask',  work_dir='02_reference_mask', str_template='{idx:04d}.png'),
        'weighted_grayscale'    : filename('weighted_grayscale', work_dir='04_weighted_grayscale', str_template='{idx:04d}.nii.gz'),
        'weighted_multichannel' : filename('weighted_multichannel', work_dir='05_weighted_multichannel', str_template='{idx:04d}.nii.gz'),
        'weighted_grayscale_mask'    : filename('weighted_grayscale_mask', work_dir='04_weighted_grayscale', str_template='????.nii.gz'),
        'weighted_multichannel_mask' : filename('weighted_multichannel_mask', work_dir='05_weighted_multichannel', str_template='%04d.nii.gz'),
        'output_volumes' : filename('output_volumes', work_dir='10_output_volumes', str_template='output_volume.nii.gz'),
        'tmp_gray_vol' : filename('tmp_gray_vol', work_dir='09_intermediate_results', str_template='__temp__vol.vtk'),
        }
    _usage = ""

    CONST_NOSLICE_INDEX = 9999

    def __init__(self, options, args, pool=None):
        super(self.__class__, self).__init__(options, args, pool)

        if not any([self.options.useMultichannelWorkflow,
                   self.options.useGrayscaleWorkflow]):
            print >> sys.stderr, "No workflow type selected (either grayscale or multichannel). Exiting."
            sys.exit(1)

        if not all([self.options.probingCoordinates,
                   self.options.referenceCoordinates]):
            print >> sys.stderr, "You need to provide file for both reference and probing coordinates. Exiting."
            sys.exit(1)

        if not self.options.referenceInputDirectory:
            print >>sys.stderr, "No input slices directory. Please provide such. Exiting"
            sys.exit(1)
        else:
            self.f['ref_input'].override_dir = self.options.referenceInputDirectory

        # Override directories if customized directories names are provided
        # Currntly, the only customizable directory is the output directory to
        # for weighted slices   .
        if self.options.outputWeightedSlicesDir:
            self.f['weighted_grayscale'].override_dir = self.options.outputWeightedSlicesDir
            self.f['weighted_multichannel'].override_dir = self.options.outputWeightedSlicesDir
        
        for out_type in (self.options.grayscaleVolumeFilename,\
                         self.options.rgbVolumeFilename):
            if out_type:
                self.f['output_volumes'].override_path = out_type
    
    def launch(self):
        # TODO: the script should be able to process the volumes instead of 
        # the extracted slices. Think about it :)
        
        # At first load the coordinates of reference volume
        # (the coordinates you map to)
        self.coords_from = self.load_coordinates_from_file(
                             self.options.referenceCoordinates,
                             negate=self.options.negateReferenceCoordinates)
        
        # Then load the probing coordinates
        # (the coordinates you map from)
        self.coords_to = self.load_coordinates_from_file(
                           self.options.probingCoordinates,
                           negate=self.options.negateProbingCoordinates)
        
        # Select the workflow type (one can choose between RGB - multichannel workflow
        # and classic, grayscale workflow).
        # Process the source data according to the selected workflow, 
        if self.options.useMultichannelWorkflow:
            self.reslice_generic(average_multichannel_images_list,
                                 weighting_output_dir='weighted_multichannel')

            self.prepare_output_multichannel_volume()
        
        if self.options.useGrayscaleWorkflow:
            self.reslice_generic(average_grayscale_images_list,
                                 weighting_output_dir='weighted_grayscale')
            self.prepare_output_grayscale_volume()

    def load_coordinates_from_file(self, filename, negate=False):
        multiplier = [1, -1][negate]

        coords = []
        for line in open(filename).readlines():
            coords.append(multiplier * float(line.strip()))

        return np.array(coords)

    def reslice_generic(self, reslice_command_wrapper=None, weighting_output_dir=None):
        interpolation_data = \
             self.interpolate(self.coords_from, self.coords_to,
                              kind=self.options.interpolation)

        commands = []

        for slice_idx, slice in enumerate(interpolation_data):
            # print slice
            command = reslice_command_wrapper(\
                        dimension = 2,
                        input_image_1 = self.f['ref_input'](idx=slice['slice_1']),
                        input_image_2 = self.f['ref_input'](idx=slice['slice_2']),
                        weight_1 = slice['weight_1'],
                        weight_2 = slice['weight_2'],
                        output_image = self.f[weighting_output_dir](idx=slice_idx))
            commands.append(copy.deepcopy(command))

        self.execute(commands)

    def interpolate(self, coords_from, coords_to, kind='nearest'):
        x = interp1d(coords_from, np.arange(coords_from.size), kind=kind)

        results = []

        for ref_coord in coords_to:
            try:
                i = ref_coord
                ip = x(ref_coord)

                # 'left' slice: slice_idx
                # 'right' slice: slice_idx + 1
                l_slice = int(ip)
                r_slice = int(ip) + 1

                r_weight = ip - int(ip)
                l_weight = 1 - r_weight

                # Avoid getting out of the range:
                if r_slice > len(coords_from)-1:
                    r_slice = l_slice
                
                # print i, l_slice, l_weight, r_slice, r_weight, len(coords_from)
                slice_results = {'status': True, 'coord': i,
                               'slice_1': l_slice, 'weight_1': l_weight,
                               'slice_2': r_slice, 'weight_2': r_weight}
                results.append(slice_results)
            except:
                slice_results = {'status': False, 'coord': i,
                               'slice_1': self.CONST_NOSLICE_INDEX, 'weight_1': 1.0,
                               'slice_2': self.CONST_NOSLICE_INDEX, 'weight_2': 1.0}
                results.append(slice_results)

        return results

    def prepare_output_grayscale_volume(self):
        stack_grayscale =  stack_slices_gray_wrapper(
                temp_volume_fn = self.f['tmp_gray_vol'](),
                stack_mask = self.f['weighted_grayscale_mask'](),
                permutation_order = self.options.outputVolumePermutationOrder,
                orientation_code = self.options.outputVolumeOrientationCode,
                output_type = self.options.outputVolumeScalarType,
                spacing = self.options.outputVolumeSpacing,
                origin = self.options.outputVolumeOrigin,
                interpolation = self.options.setInterpolation,
                resample = self.options.outputVolumeResample,
                output_volume_fn = self.f['output_volumes']())

        self.execute_callable(stack_grayscale)

    def prepare_output_multichannel_volume(self):
        stack_multichannel =  stack_slices_rgb_wrapper(
                stack_mask = self.f['weighted_multichannel_mask'](),
                slice_start= 0,
                slice_end  = len(self.coords_to)-1,
                temp_volume_fn = self.f['tmp_gray_vol'](),
                permutation_order = self.options.outputVolumePermutationOrder,
                orientation_code = self.options.outputVolumeOrientationCode,
                output_type = self.options.outputVolumeScalarType,
                spacing = self.options.outputVolumeSpacing,
                origin = self.options.outputVolumeOrigin,
                interpolation = self.options.setInterpolation,
                resample = self.options.outputVolumeResample,
                output_volume_fn = self.f['output_volumes']())

        self.execute_callable(stack_multichannel)

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        regSettings = \
                OptionGroup(parser, 'Processing settings.')

        regSettings.add_option('--referenceCoordinates', default=None,
                type='str', dest='referenceCoordinates',
                help='File with reference coordinates (the experimental one).')
        regSettings.add_option('--negateReferenceCoordinates', default=False,
                dest='negateReferenceCoordinates', action='store_const', const=True,
                help="Negate values of the reference coordinates.")
        regSettings.add_option('--probingCoordinates', default=None,
                type='str', dest='probingCoordinates',
                help='File with probing coordinates (the atlas one).')
        regSettings.add_option('--negateProbingCoordinates', default=False,
                dest='negateProbingCoordinates', action='store_const', const=True,
                help="Negate values of the probing coordinates.")
        regSettings.add_option('--interpolation', default='nearest', type='str',
                dest='interpolation', help='Slice interpolation method <nearest|linear>')
        regSettings.add_option('--referenceInputDirectory', default=None,
                type='str', dest='referenceInputDirectory',
                help='Input directory for reference slices (experimental slices).')
        regSettings.add_option('--outputWeightedSlicesDir', default=None,
                type='str', dest='outputWeightedSlicesDir',
                help='Output directory for the weighted slices.')
        regSettings.add_option('--useMultichannelWorkflow', default=False,
                dest='useMultichannelWorkflow', action='store_const', const=True,
                help="Use multichannel processing workflow.")
        regSettings.add_option('--useGrayscaleWorkflow', default=False,
                dest='useGrayscaleWorkflow', action='store_const', const=True,
                help="Use grayscale processing workflow.")
        regSettings.add_option('--skipOutputVolumeGeneration', default=False,
                dest='skipSlicePreprocess', action='store_const', const=True,
                help='Skip slice preprocessing.')

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
    options, args = nonuniform_relice.parseArgs()
    d = nonuniform_relice(options, args)
    d.launch()
