import numpy as np
from itertools import izip
import datetime, time

from pos_parameters import generic_wrapper, filename_parameter, string_parameter, list_parameter

txtdata = open('/home/pmajka/03_01_NN3_rejestracja.txt', 'r').readlines()
datafile = 'a.txt'
plotfile = 'a.plt'

# Define numpy datatype in order to read reconrdings from the file
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
    set ytics
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
    def __init__(self):
        pass
    
    def run(self):
        # Load data with loadtxt
        data = np.loadtxt(txtdata, dtype=record_data, skiprows=4, delimiter=',')
        
        # Extract metadata information
        metadata = map(lambda x: x.strip().replace('"',""), txtdata[0].strip().split(","))
        metadata = dict(list(izip(*[iter(metadata)]*2)))
        
        date_start_day = datetime.datetime.strptime(metadata['Date'], '%m/%d/%y')
        date_start = datetime.datetime.strptime(metadata['Date'] + " " + metadata['Start'], '%m/%d/%y %H:%M:%S')
        date_stop  = datetime.datetime.strptime(metadata['Date'] + " " + metadata['Stop'], '%m/%d/%y %H:%M:%S')
        
        global_time_points   = map(lambda x: date_start + datetime.timedelta(seconds=int(x)), data['seconds'])
        relative_time_points = map(lambda x: date_start_day + datetime.timedelta(seconds=int(x)), data['seconds'])
        
        final_array = np.array([relative_time_points, global_time_points, data['resp_m'], data['temp']]).T
        
        fh = open(datafile, 'w')
        for i in range(final_array.shape[0])    :
            line = "\t".join(map(str, final_array[i])) + "\n"
            fh.write(line)
        fh.close()
        
        plot_file = anesthesia_plot(specimen_name = '02\_02\_NN2',
                                    respiration_range = (15,40),
                                    temperature_range = (25,30),
                                    output_filename = 'a.svg',
                                    input_filename = 'a.txt',
                                    plot_date = metadata['Date'],
                                    plot_start = metadata['Start'],
                                    plot_stop = metadata['Stop'])
        
        gnuplot = gnuplot_wrapper(plot_file='a.plt',
                                  svg_file ='a.svg',
                                  output_file = 'a.png')
        
        fh = open(plotfile, 'w').write(str(plot_file))
        gnuplot()
