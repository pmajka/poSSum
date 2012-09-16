import numpy as np
from itertools import izip
import datetime, time
from optparse import OptionParser, OptionGroup

from pos_parameters import generic_wrapper, filename_parameter, string_parameter, list_parameter

txtdata = open('/home/pmajka/03_01_NN3_rejestracja.txt', 'r').readlines()
plotfile = 'a.plt'

# Define numpy datatype in order to read reconrdings from the file
# Supported input file format: TSV format with a number of header lines starting
# with hash character
record_data = np.dtype([
        ('seconds', np.uint64),
        ('bpm', np.float),
        ('resp_m', np.float),
        ('temp', np.float)])

class range_parameter(list_parameter):
    _delimiter = ":"

class anesthesia_plot(generic_wrapper):
    _template = """
    set terminal svg size 700,450 dynamic fname "Verdana" fsize 12 
    set out '{output_filename}'
    
    set title "Recording of the life functions during anesthesia during MRI imaging\\n specimen {specimen_name} \\n date: {plot_date}, start: {plot_start}, stop: {plot_stop}"
    
    set xdata time
    set timefmt "%Y-%m-%d %H:%M:%S"
    set nomxtics
    
    set datafile separator "\\t"
    
    set yrange [{respiration_range}]
    
    set y2tics
    set ytics nomirror
    set y2range [{temperature_range}]
    
    set format x "%1H:%M"
    set xtics nomirror
    set xlabel "experiment time [h:m]"
    
    set ylabel "respiration rate [rpm]"
    set y2label "body temperature [deg. C]"
    
    plot '{input_filename}' u 1:3 w l           title 'respiration rate' lc rgb '#79aff5' lw 2,\
                         '' u 1:4 w l axes x1y2 title 'body temperature' lc rgb '#ff6b68' lw 2
    """
     
    _parameters = {
            'output_filename' : filename_parameter('output_filename', None),
            'specimen_name' : filename_parameter('specimen_name', None),
            'respiration_range' : range_parameter('respiration_range', None),
            'temperature_range' : range_parameter('temperature_range', None),
            'plot_date' : string_parameter('plot_date', None),
            'plot_start' : string_parameter('plot_start', None),
            'plot_stop' : string_parameter('plot_stop', None),
            'input_filename' : filename_parameter('input_filename', None)
            }
    
    _io_pass = { \
            'input_filename' : 'output_filename'
            }

class gnuplot_wrapper(generic_wrapper):
    _template = "gnuplot {plot_file}; convert {svg_file} -density 300 {output_file}; rm -rfv {plot_file}"
    
    _parameters = {
            'plot_file' : filename_parameter('plot_file', None),
            'svg_file' : filename_parameter('svg_file', None),
            'output_file' : filename_parameter('output_file', None),
            }

class draw_anesthesia_plot(object):
    def __init__(self, options, args):
        self._options = options
        self._args = args
    
    def _prepare_dataset(self):
        # Load data with loadtxt
        txtdata = open(self._args[0]).readlines()
        datafile = self._options.dataTempFilename

        data = np.loadtxt(txtdata, dtype=record_data, skiprows=4, delimiter=',')
        
        # Extract self._metadata information
        self._metadata = map(lambda x: x.strip().replace('"',""), txtdata[0].strip().split(","))
        self._metadata = dict(list(izip(*[iter(self._metadata)]*2)))
        
        date_start_day = datetime.datetime.strptime(self._metadata['Date'], '%m/%d/%y')
        date_start = datetime.datetime.strptime(self._metadata['Date'] + " " + self._metadata['Start'], '%m/%d/%y %H:%M:%S')
        
        global_time_points   = map(lambda x: date_start + datetime.timedelta(seconds=int(x)), data['seconds'])
        relative_time_points = map(lambda x: date_start_day + datetime.timedelta(seconds=int(x)), data['seconds'])
        
        final_array = np.array([relative_time_points, global_time_points, data['resp_m'], data['temp']]).T
        
        fh = open(datafile, 'w')
        for i in range(final_array.shape[0])    :
            line = "\t".join(map(str, final_array[i])) + "\n"
            fh.write(line)
        fh.close()
    
    def _plot_chart(self):
        print self._options
        plot_file_kwargs = { \
                'specimen_name'     : self._options.specimenName,
                'output_filename'   : self._options.outputFilename,
                'respiration_range' : self._options.respirationRange,
                'temperature_range' : self._options.temparatureRange,
                'input_filename'     : self._options.dataTempFilename,
                'plot_date' : self._metadata['Date'],
                'plot_start': self._metadata['Start'],
                'plot_stop' : self._metadata['Stop']
                }
        
        gnuplot_kwargs = {
                'plot_file'   : self._options.tempFilename,
                'svg_file'    : self._options.outputFilename,
                'output_file' : self._options.outputImageFilename
                }
        
        plot_file = anesthesia_plot(**plot_file_kwargs)
        
        gnuplot = gnuplot_wrapper(**gnuplot_kwargs)
        
        # Execute plotting
        plotfile = self._options.tempFilename
        open(plotfile, 'w').write(str(plot_file))
        gnuplot()
    
    def run(self):
        self._prepare_dataset()
        self._plot_chart()
    
    @staticmethod
    def parseArgs():
        usage = "python draw_aneshesia_plot.py input_file [options]"
        
        parser = OptionParser(usage = usage)
         
        parser.add_option('--specimenName', default=None,
                dest='specimenName', action='store', type='str',
                help='Name of the specimen')
        parser.add_option('--outputFilename', default='plot.svg',
                dest='outputFilename', action='store', type='str',
                help='Name of the output svg image.')
        parser.add_option('--outputImageFilename', default='plot.png',
                dest='outputImageFilename', action='store', type='str',
                help='Name of the output svg image.')
        parser.add_option('--respirationRange', default=(15,40),
                dest='respirationRange', action='store', type='int',
                nargs = 2, help='Range of respiration range scale')
        parser.add_option('--temparatureRange', default=(25,30),
                dest='temparatureRange', action='store', type='int',
                nargs = 2, help='Range of temperature range scale')
        parser.add_option('--tempFilename', default='temp.plt',
                dest='tempFilename', action='store', type='str',
                help="Name of the temponary file. Do not change it if you don't need to")
        parser.add_option('--dataFilename', default='data_temp.txt',
                dest='dataTempFilename', action='store', type='str',
                help="Name of the temponary data file. Do not change it if you don't need to")
        
        (options, args) = parser.parse_args()
        return (options, args)

if __name__ == '__main__':
    options, args = draw_anesthesia_plot.parseArgs()
    plotter = draw_anesthesia_plot(options, args)
    plotter.run()

"""
python draw_aneshesia_plot.py 03_01_NN3_rejestracja.txt  --specimenName '03_01_NN3'  --outputImageFilename 03_01_NN3.png --outputFilename 03_01_NN3.sv

 python draw_aneshesia_plot.py 03_02_NN4_rejestracja.txt  --specimenName '03_02_NN4'  --outputImageFilename 03_02_NN4.png --outputFilename 03_02_NN4.svg  --temparatureRange 25 31
 --respirationRange 15 50

 python draw_aneshesia_plot.py 03_03_NN5_rejestracja.txt  --specimenName '03_03_NN5'  --outputImageFilename 03_03_NN5.png --outputFilename 03_03_NN5.svg  --temparatureRange 27 31
 --respirationRange 13 35
"""
