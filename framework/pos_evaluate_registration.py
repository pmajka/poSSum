import os
import nifti
import numpy as np
from optparse import OptionParser, OptionGroup
import sys
import datetime, time

from pos_parameters import generic_wrapper, filename_parameter, string_parameter, list_parameter,\
                           value_parameter
from pos_deformable_wrappers import gnuplot_wrapper 

#signal.correlate2?
# http://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.correlate2d.html

def norm_corr_coeff_2d(a1, a2):
    """
    Calculate normalized cross correlation coefficient:
    http://en.wikipedia.org/wiki/Cross-correlation#Normalized_cross-correlation
    
    .. math::
    
    \frac{1}{n} \sum_{x,y}\frac{(f(x,y) - \overline{f})(t(x,y) - \overline{t})}{\sigma_f \sigma_t}
    
    """
    a1m, a2m = np.mean(a1),  np.mean(a2)
    
    num = np.sum( (a1 - a1m) * (a2 - a2m) )
    den = np.std(a1) * np.std(a2) 
    
    return  num / den  * (1./a1.size)

def msq(a1, a2):
    """
    Return mean square difference of the two arrays
    """
    return np.sum(np.square(a1 - a2)) / a1.size

def avg_norm_corr_coeff_2d(a1, a2, a3):
    """
    Return cormalized correlation coefficient of a2 and (a1+a3)/2
    """
    
    p1 = a2
    p2 = 0.5 * ( a1 + a3)
    
    return norm_corr_coeff_2d(p1, p2)

def avg_msq(a1, a2, a3):
    """
    Return mean square difference of a2 and (a1+a3)/2 
    """
    
    p1 = a2
    p2 = 0.5 * ( a1 + a3)
    
    return msq(p1, p2)

class evaluation_plot(generic_wrapper):
    _template = """
    set terminal svg size 700,450 dynamic enhanced fname "Verdana" fsize 12 
    set out '{output_filename}'
    
    set title "Deformable registration evaluation plot\\n {title}"
    
    set autoscale y
    set autoscale x
    
    set xlabel "{xlabel}"
    set ylabel "{ylabel}"
    
    set format y "{yformat}"
    
    plot for [n=1:{args_len}] '{input_filename}' u 0:n w lines ls n title sprintf("%d",n)
    """
    
    _parameters = {
            'output_filename' : filename_parameter('output_filename', None),
            'title' : string_parameter('title', None),
            'xlabel' : string_parameter('xlabel', None),
            'ylabel' : string_parameter('ylabel', None),
            'yformat' : string_parameter('yformat', None),
            'args_len' : value_parameter('args_len', None),
            'input_filename' : string_parameter('input_filename', None),
            }
    
    _io_pass = { \
            'input_filename' : 'output_filename'
            }

class serial_alignment_evaluation(object):
    def __init__(self, options, args):
        self.options = options
        self.args = args
    
    def _extract_slice_to_average(self, sliceIndex):
        """
        Extract and return slice with given index as well as neighbouring
        slices according to provided slicing plane.
        """
        
        if self.options.slicingPlane == 0:
            slice1 = self._data[sliceIndex    , :, :]
            slice2 = self._data[sliceIndex + 1, :, :]
            slice3 = self._data[sliceIndex - 1, :, :]
        
        if self.options.slicingPlane == 1:
            slice1 = self._data[:, sliceIndex     , :]
            slice2 = self._data[:, sliceIndex + 1 , :]
            slice3 = self._data[:, sliceIndex - 1 , :]
        
        if self.options.slicingPlane == 2:
            slice1 = self._data[:, :, sliceIndex    ]
            slice2 = self._data[:, :, sliceIndex + 1]
            slice3 = self._data[:, :, sliceIndex - 1]
        
        return (slice1, slice2, slice3)
    
    def _extract_slice_pair(self, sliceIndex):
        """
        Extract slice with the given index as well as the slice with index +1 
        according provided slicing plane.
        """
        
        if self.options.slicingPlane == 0:
            slice1 = self._data[sliceIndex    , :, :]
            slice2 = self._data[sliceIndex + 1, :, :]
        
        if self.options.slicingPlane == 1:
            slice1 = self._data[:, sliceIndex     , :]
            slice2 = self._data[:, sliceIndex + 1 , :]
        
        if self.options.slicingPlane == 2:
            slice1 = self._data[:, :, sliceIndex    ]
            slice2 = self._data[:, :, sliceIndex + 1]
        
        return (slice1, slice2)
    
    def _loadVolume(self, filename):
        """
        Load volume and from given filename and extract some information from
        header.
        """
        print >>sys.stderr, ""
        print >>sys.stderr, "_loadVolume: "
        print >>sys.stderr, "_loadVolume: Loading volume %s" % filename
        
        self._volume = nifti.NiftiImage(filename)
        
        self._data = self._volume.data
        self.volumeShape = self._data.shape
   
    def _define_similiarity_measures(self):
        """
        Define, assing proper metric and slice extraction functions according to
        provided command line parameters. Functions defined here are then used
        to evaluate image image simmilarities.
        """
        
        # The assignment is made for three functions: 
        # - function for assigning mean square functions
        # - functions for calculating normalized cross correlation
        # - slice extraction function
        
        # If we want to use 'smoothness evaluation'
        if self.options.useSmoothnesMeasure == False:
            msq_function   = msq
            ncorr_function = norm_corr_coeff_2d
            get_slice_function = self._extract_slice_pair
        
        # If we want just to simply calculate difference
        # without evaluating 'smoothness measure'
        if self.options.useSmoothnesMeasure == True:
            msq_function   = avg_msq
            ncorr_function = avg_norm_corr_coeff_2d
            get_slice_function = self._extract_slice_to_average
        
        return msq_function, ncorr_function, get_slice_function
    
    def _initialize_results(self):
        """
        Initialize arrays for storing the results of the evaluation. Initialize
        source volume slicing range as well.
        """
        
        # Here we define slicing range. The slicing range depends on the
        # provided command line parameter - slicing plane.
        self.options.slicingRange = \
                range(1, self.volumeShape[self.options.slicingPlane] -1)
        
        # Arrays holding the results depend on the number of volumes to evaluate
        # and on the number of the slides.
        args_len  = len(self.args)
        slices_no = len(self.options.slicingRange)
        
        # Just define the arrays for the results
        self.results_msq =  np.zeros((args_len, slices_no))
        self.results_ncor = np.zeros((args_len, slices_no))    
    
    def launch(self):
        """
        Launch all of the calculations!
        """
        
        # Get the image simmilarity metrics and slice assignment functions based
        # on the provided command line parameters:
        msq_function, ncorr_function, get_slice_function =\
                self._define_similiarity_measures()
        
        for file_index, file in enumerate(self.args):
            print >>sys.stderr, ""
            print >>sys.stderr, "#---------------------------------------------"
            print >>sys.stderr, "Processing %d of %d:\n%s" % (file_index + 1, len(self.args), file)
            print >>sys.stderr, "#---------------------------------------------"
            
            self._loadVolume(file)
            
            # If the file that is currently processed is the first one
            # we need to initialize the results arrays:
            if file_index == 0:
                self._initialize_results()
            
            # Then evaluate the alignment quality for the each pair (or triple)
            # of slices:
            for sliceIndex in self.options.slicingRange:
                planes = get_slice_function(sliceIndex)
                
                # Check if the script is asked for caculating particular 
                # simmilarity measure, if it is, calulate it.
                
                # I need to substract 1 from sliceIndex to make it fit
                # into the results array.
                if self.options.msqFilename:
                    self.results_msq[file_index, sliceIndex -1]  = msq_function(*planes)
                
                # The same (-1) here:
                if self.options.ncorrFilename:
                    self.results_ncor[file_index, sliceIndex -1] = ncorr_function(*planes)
        
        # Save the results at the end of the calculations:
        self.save_results()
        
        # After saving the results, plot them
        self.plot_results()
    
    def save_results(self):
        """
        Save the results according to provided command line parameters.
        """
        
        if self.options.msqFilename:
            np.savetxt(self.options.msqFilename, self.results_msq.T)
        
        if self.options.ncorrFilename:
            np.savetxt(self.options.ncorrFilename, self.results_ncor.T)
    
    def plot_results(self):
        """
        Plot the evaluation results according to provided command line
        parameters.
        """
        
        if self.options.plotMsqFilename:
            self._plot_results_msq()
        
        if self.options.plotNcorrFilename:
            self._plot_results_ncorr()
    
    def _get_plot_filenames(self, naming_base):
        """
        Prepare the names for the particular plot.
        """
        
        plot_file = naming_base + ".plt"
        svg_file = naming_base + ".svg"
        png_file = naming_base + ".png"
        
        return plot_file, svg_file, png_file
    
    def _plot_results_msq(self):
        """
        Plot the results for mean square difference metric.
        """
        
        # Get names of the gnuplot plot file, output svg file,
        # and output png file for the the MSQ evaluation plot.
        plot_file, svg_file, png_file, = \
                self._get_plot_filenames(self.options.plotMsqFilename)
        #        'yformat' : '%.0s*10^{%S}',
        
        evaluation_plot_kwargs = { \
                'output_filename' : svg_file,
                'xlabel' : 'Slice index',
                'ylabel' : 'MSQ',
                'yformat' : '%2.2f',
                'title' : 'Mean sqare difference between slice n and n + 1',
                'args_len' : len(self.args),
                'input_filename' : self.options.msqFilename}
        
        gnuplot_kwargs = {
                'plot_file'   : plot_file,
                'svg_file'    : svg_file,
                'output_file' : png_file}
        
        plot    = evaluation_plot(**evaluation_plot_kwargs)
        gnuplot = gnuplot_wrapper(**gnuplot_kwargs)
        
        # Execute plotting
        open(plot_file, 'w').write(str(plot))
        gnuplot()
    
    def _plot_results_ncorr(self):
        """
        Plot the results for the normalized corelation coefficient.
        """        
        
        # Get names of the gnuplot plot file, output svg file,
        # and output png file for the the normalized correlation coefficient
        # plot
        plot_file, svg_file, png_file, = \
                self._get_plot_filenames(self.options.plotNcorrFilename)
        
        evaluation_plot_kwargs = { \
                'output_filename' : svg_file,
                'xlabel' : 'Slice index',
                'ylabel' : 'NCORR',
                'yformat' : '%1.2f',
                'title' : 'Correlation coeff between slice n and n + 1',
                'args_len' : len(self.args),
                'input_filename' : self.options.ncorrFilename}
        
        gnuplot_kwargs = {
                'plot_file'   : plot_file,
                'svg_file'    : svg_file,
                'output_file' : png_file}
        
        plot    = evaluation_plot(**evaluation_plot_kwargs)
        gnuplot = gnuplot_wrapper(**gnuplot_kwargs)
        
        # Execute plotting
        open(plot_file, 'w').write(str(plot))
        gnuplot()
    
    @staticmethod
    def parseArgs():
        usage = ""
        
        parser = OptionParser(usage = usage)
        
        parser.add_option('--msqFilename', default=None,
                dest='msqFilename', action='store', type='str',
                help='MSQ output file.')
        parser.add_option('--ncorrFilename', default=None,
                dest='ncorrFilename', action='store', type='str',
                help='NCORR filename')
        parser.add_option('--slicingPlane', default=1,
                dest='slicingPlane', action='store', type='int',
                help='Slicing plane')
        parser.add_option('--useSmoothnesMeasure', default=False, const=True,
                dest='useSmoothnesMeasure', action='store_const',
                help='Use smoothness measure instead of regular similarity metric.')
        parser.add_option('--plotMsqFilename', default=None,
                dest='plotMsqFilename', action='store', type='str',
                help='Name of the output svg image.')
        parser.add_option('--plotNcorrFilename', default=None,
                dest='plotNcorrFilename', action='store', type='str',
                help='Name of the output svg image.')
        
        (options, args) = parser.parse_args()
        return (options, args)

if __name__ == '__main__':
    options, args = serial_alignment_evaluation.parseArgs()
    evaluate = serial_alignment_evaluation(options, args)
    evaluate.launch()
