import os
import sys
import datetime, time
from optparse import OptionParser, OptionGroup

import nifti
import numpy as np
from scipy import stats

from pos_parameters import filename_parameter, string_parameter, list_parameter, value_parameter
from pos_deformable_wrappers import gnuplot_wrapper 
import pos_wrappers

#signal.correlate2?
# http://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.correlate2d.html

def dice_coefficient(x, y, xay):
    """
    Calculate the Dice's coefficient according to definition provided on wiki:
    http://en.wikipedia.org/wiki/Dice%27s_coefficient
    
    .. math::
    
    s = \frac{2 | X \cap Y |}{| X | + | Y |} 
    
    """
    return 2.0*(xay+0.0)/(x+0.0+y+0.0)

def count_items(a, value_to_count = 1):
    """
    Return number of occurences of 'value_to_count' in array 'a'
    """
    return np.where(a==value_to_count, 1, 0).sum()

def count_overlap(a1, a2, value_to_count = 1):
    """
    Return overlap of a1 and a2
    """
    return np.where(a1 * a2 == value_to_count, 1, 0).sum()

class evaluation_plot(pos_wrappers.generic_wrapper):
    _template = """
    set terminal svg size 700,450 dynamic enhanced fname "Verdana" fsize 12 
    set out '{output_filename}'
    
    set title "Dice's coefficient"
    
    set autoscale y
    set autoscale x
    
    set xlabel "{xlabel}"
    set ylabel "{ylabel}"
    
    set format y "{yformat}"
     
    plot '{input_filename}' u 1:2 w lines lc rgb "blue" lw 0.3 notitle
    """
    
    _parameters = {
            'output_filename' : filename_parameter('output_filename', None),
            'title' : string_parameter('title', None),
            'xlabel' : string_parameter('xlabel', None),
            'ylabel' : string_parameter('ylabel', None),
            'yformat' : string_parameter('yformat', None),
            'input_filename' : string_parameter('input_filename', None),
            }
    
    _io_pass = { \
            'input_filename' : 'output_filename'
            }

class candlestick_plot(pos_wrappers.generic_wrapper):
    _template = """
    set terminal svg size 700,450 dynamic enhanced fname "Verdana" fsize 12 
    set out '{output_filename}'
    
    set border 2
    set style fill solid
    unset grid
    
    set title "Dice's coefficient"
    
    set boxwidth 0.2 absolute
    set format x ""
    set xlabel ""
    set format y "%1.1f"
    set ylabel ""
    
    set xtics scale 0
    set ytics border in scale 2,0.5 nomirror norotate  offset character 0, 0, 0
    set yrange [0:1]
    set mytics 2
    
    lines=system(" cat '{input_filename}' | wc -l")
    set xrange[0:lines+1]

#    factors = "Coarse Fine Final Deformable"
#    set for [i=1:lines] xtics add (word(factors,i) i) 

    {upper_limit_name} = "{upper_limit}"
    {lower_limit_name} = "{lower_limit}"

    plot '{input_filename}' using ($0+1):2:1:5:4 with candlesticks notitle whiskerbars lw 2 lc rgb "#aabbcc", \
         '{input_filename}' using ($0+1):3:3:3:3 with candlesticks lt -1 lw 2 lc rgb "#445566" notitle,\
         for [n=2:{args_len}] '{input_data_filename}' u (n):( (column(n)> word({upper_limit_name},n)+0.01) || (column(n) <  word({lower_limit_name},n)-0.01) && column(n) > 0 ? column(n) : 1/0) w p pt 7 lc rgb "#444444" ps 0.5 notitle
    """
    
    _parameters = {
            'output_filename' : filename_parameter('output_filename', None),
            'input_data_filename' : filename_parameter('input_data_filename', None),
            'input_filename' : filename_parameter('input_filename', None),
            'lower_limit_name' : string_parameter('lower_limit_name', None),
            'upper_limit_name' : string_parameter('lower_limit_name', None),
            'lower_limit' : list_parameter('lower_limit', None),
            'upper_limit' : list_parameter('upper_limit', None),
            'args_len' : value_parameter('args_len', None),
            }
    
    _io_pass = { \
            'input_filename' : 'output_filename'
            }

class serial_alignment_evaluation(object):
    def __init__(self, options, args):
        self.options = options
        self.args = args
       
    def _extract_slice_pair(self, sliceIndex):
        """
        Extract slice with the given index as well as the slice with index +1 
        according provided slicing plane.
        """
        
        if self.options.slicingPlane == 0:
            slice1 = self._volume_data[0][sliceIndex    , :, :]
            slice2 = self._volume_data[1][sliceIndex + 1, :, :]
        
        if self.options.slicingPlane == 1:
            slice1 = self._volume_data[0][:, sliceIndex     , :]
            slice2 = self._volume_data[1][:, sliceIndex + 1 , :]
        
        if self.options.slicingPlane == 2:
            slice1 = self._volume_data[0][:, :, sliceIndex    ]
            slice2 = self._volume_data[1][:, :, sliceIndex + 1]
        
        return (slice1, slice2)
    
    def _load_volumes(self):
        """
        Load volume and from given filename and extract some information from
        header.
        """
        
        self._volumes = map( lambda x: \
                nifti.NiftiImage(self.args[x]),range(2))
        self._volume_data  = map(lambda x: x.data, self._volumes) 
        self._volume_shape = self._volume_data[0].shape
    
    def _initialize_results(self):
        """
        Initialize arrays for storing the results of the evaluation. Initialize
        source volume slicing range as well.
        """
        
        # Here we define slicing range. The slicing range depends on the
        # provided command line parameter - slicing plane.
        self.options.slicingRange = \
                range(0, self._volume_shape[self.options.slicingPlane] -1)
        
        opts_len  = 5
        slices_no = len(self.options.slicingRange)
        
        # Just define the arrays for the results
        self.results =  np.zeros((opts_len, slices_no))
    
    def launch(self):
        """
        Launch all of the calculations!
        """
        self._load_volumes()
        self._initialize_results()
        
        # Then evaluate the alignment quality for the each pair (or triple)
        # of slices:
        for sliceIndex in self.options.slicingRange:
            print sliceIndex
            
            x, y = self._extract_slice_pair(sliceIndex)
            
            count1  = count_items(x)
            count2  = count_items(y)
            overlap = count_overlap(x,y)
            dices   = dice_coefficient(count1, count2, overlap)
            
            self.results[:, sliceIndex] = \
                    np.array([sliceIndex, dices, count1, count2, overlap])
        
        # Save the results at the end of the calculations:
        self.save_results()
        
        # After saving the results, plot them
        self.plot_results()
    
    def save_results(self):
        """
        Save the results according to provided command line parameters.
        """
        results_filename = self.options.plotComparisonNaming + "_results"
        np.savetxt(results_filename, self.results.T)
    
    def plot_results(self):
        """
        Plot the evaluation results according to provided command line
        parameters.
        """
        self._plot_results()
        self._plot_reaults_ncorr_boxplot()
    
    def _get_plot_filenames(self, naming_base):
        """
        Prepare the names for the particular plot.
        """
        
        plot_file = naming_base + ".plt"
        svg_file = naming_base + ".svg"
        png_file = naming_base + ".png"
        
        return plot_file, svg_file, png_file
    
    def _plot_results(self):
        """
        Plot the results for the normalized corelation coefficient.
        """        
        
        # Get names of the gnuplot plot file, output svg file,
        # and output png file for the the normalized correlation coefficient
        # plot
        plot_file, svg_file, png_file, = \
                self._get_plot_filenames(self.options.plotComparisonNaming)
        results_filename = self.options.plotComparisonNaming + "_results"
        
        evaluation_plot_kwargs = { \
                'output_filename' : svg_file,
                'xlabel' : 'Slice index',
                'ylabel' : ' ',
                'yformat' : '%1.1f',
                'title' : 'Dices coefficient between slice n and n + 1',
                'input_filename' : results_filename}
        
        gnuplot_kwargs = {
                'plot_file'   : plot_file,
                'svg_file'    : svg_file,
                'output_file' : png_file}
        
        plot    = evaluation_plot(**evaluation_plot_kwargs)
        gnuplot = gnuplot_wrapper(**gnuplot_kwargs)
        
        # Execute plotting
        open(plot_file, 'w').write(str(plot))
        gnuplot()
    
    def _plot_reaults_ncorr_boxplot(self):
        """
        Plot the normalized correlation coefficient as boxplot.
        """        
        
        # Get names of the gnuplot plot file, output svg file,
        # and output png file for the the normalized correlation coefficient
        # plot
        box_data_file = self.options.plotComparisonNaming + '_box'
        plot_file, svg_file, png_file, = \
                self._get_plot_filenames(box_data_file)
        
        results_filename = self.options.plotComparisonNaming + "_results"
        
        # Generate data for the boxplot and save it to disk
        box_plot_data = self._get_boxplot_data()
        np.savetxt(box_data_file, box_plot_data)
        upper_limit = list(box_plot_data[:,4].flatten())
        lower_limit = list(box_plot_data[:,0].flatten())
        
        plot_kwargs = { \
                'output_filename' : svg_file,
                'input_data_filename' : results_filename,
                'input_filename' : box_data_file,
                'args_len'   : 2,
                'lower_limit_name' : os.path.basename(self.options.plotComparisonNaming) + "_lower",
                'upper_limit_name' : os.path.basename(self.options.plotComparisonNaming) + "_upper",
                'upper_limit' : upper_limit,
                'lower_limit' : lower_limit}
        
        gnuplot_kwargs = {
                'plot_file'   : plot_file,
                'svg_file'    : svg_file,
                'output_file' : png_file}
        
        plot    = candlestick_plot(**plot_kwargs)
        gnuplot = gnuplot_wrapper(**gnuplot_kwargs)
        
        # Execute plotting
        open(plot_file, 'w').write(str(plot))
        gnuplot()
    
    def _get_boxplot_data(self):
        """
        Calculate the data for the boxplot:
        min, 1st quartile, mean,  3rd quartile and max value from the array
        """
        
        # Just create aliases to make the code less obscured
        f  = stats.scoreatpercentile
        a  = self.results
        
        ar = range(a.shape[0])
        pc = [5, 25, 50, 75, 95]
        
        # Calculate data for the boxplot: min, 1st quartile, mean
        # 3rd quartile and max value from the array
        result = np.array( \
                 map(lambda y: \
                     map(lambda x: f(a[y,:],x),  pc), \
                 ar)\
                 )
        
        # And return the result
        return result
    
    @staticmethod
    def parseArgs():
        usage = ""
        
        parser = OptionParser(usage = usage)
        
        parser.add_option('--plotComparisonNaming', default=None,
                dest='plotComparisonNaming', action='store', type='str',
                help='Output naming of the files and plots.')
        parser.add_option('--slicingPlane', default=1,
                dest='slicingPlane', action='store', type='int',
                help='Slicing plane')
        
        (options, args) = parser.parse_args()
        return (options, args)

if __name__ == '__main__':
    options, args = serial_alignment_evaluation.parseArgs()
    evaluate = serial_alignment_evaluation(options, args)
    evaluate.launch()
