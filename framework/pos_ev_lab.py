import os, sys
import codecs
import numpy as np
import re
from optparse import OptionParser, OptionGroup

import pos_wrappers
from pos_deformable_wrappers import gnuplot_wrapper
from pos_parameters import filename_parameter, string_parameter, list_parameter, value_parameter

f1="/home/pmajka/x.txt"
f2="/home/pmajka/y.txt"
ld="/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/label_descriptions.txt"

class evaluation_plot(pos_wrappers.generic_wrapper):
    _parameters = {
            'number_of_structures' : value_parameter('number_of_structures', None),
            'input_filename' : filename_parameter('input_filename', None),
            'output_filename' : filename_parameter('output_filename', None)
            }

    _template = """
    reset
    set terminal svg size 700,500 dynamic enhanced fname "Verdana" fsize 12
    set out '{output_filename}'

    set datafile separator "\t"

    set style line 3 \
        linecolor rgb "#000088" \
        linetype 1 \
        linewidth 1 \
        pointtype 7

    set style fill transparent solid 0.25    #fillstyle

    set tmargin 2.0
    set border 3
    set key at 5,0.2 nobox

    box_width = 0.33
    set boxwidth box_width

    set xtics border in scale 0,0 nomirror rotate by -45 offset character 0.0, -0.5 autojustify

    set xrange [-1:{number_of_structures}]

    set yrange[0:1.0]
    set ytics nomirror
    set format y "%1.1f"
    set mytics 2

    unset y2tics

    plot '< sort -t"	" -k2,2 -r {input_filename}' u 2:xtic(1) w boxes title "Korejestracja liniowa" ls 3 fill pattern 4,\
        '' u ($0 + box_width):3 w boxes title "Korejestracja nieliniowa" ls 3 fill transparent solid 0.25,\
        '' u ($0+  box_width/2.0):(1.0):(sprintf("%2d%%",($3/$2-1)*100)) w labels  font "11" notitle
    """

class overlap_comparison_summary(object):
    """Class for managing the comparison of the
    label overlap measurements

    Usage example: python pos_ev_lab.py \
            --base /home/pmajka/x.txt \
            --compare /home/pmajka/y.txt \
            --labels /home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/label_descriptions.txt \
            --plotComparisonNaming /home/pmajka/p
    """

    idx = 0
    target = 1
    jaccard = 2
    dice = 3
    volume_sim = 4
    false_negative = 5
    false_positive = 6

    def __init__(self, options, args):
        self.options = options
        self.args = args

        self.base = self.options.base
        self.compare = self.options.compare
        self.labelfile = self.options.labels

    def read_overlay_data(self, filename):
        file_contents = open(filename).readlines()

        table_str = [re.sub('\s\s+','|', line.strip()) \
                     for line in file_contents]

        measurements = [column.split("|") for column in table_str][5:]
        measure_all  = [column.split("|") for column in table_str][2]
        measure_all.insert(0,"0")
        measurements.append(measure_all)

        shape = len(measurements), len(measurements[0])

        results = np.zeros(shape, np.float)

        for i in range(shape[0]):
            for j in range(shape[1]):
                results[i,j] = float(measurements[i][j])
        return results

    def read_label_descriptions(self, filename):
        file_contents = codecs.open(filename, 'r', 'utf-8').readlines()
        table_str = [re.sub('\s\s+','|', line.strip()) \
                     for line in file_contents]

        measurements = [column.split("|") for column in table_str][14:]

        results = {}
        shape = len(measurements)

        for i in range(shape):
            label_id = int(measurements[i][0])
            label_name = measurements[i][-1].strip().replace("\"","")
            label_color = tuple(map(int,measurements[i][1:4]))

            results[label_id] = {"name" : label_name,\
                                 "color": label_color}
        return results

    def results(self):
        a1 = self.read_overlay_data(self.base)
        a2 = self.read_overlay_data(self.compare)
        lab= self.read_label_descriptions(self.labelfile)

        types = [self.jaccard, self.dice]

        self.number_of_structures = a1.shape[0]

        result_string = ""

        for i in range(self.number_of_structures):
            structure_id = int(a1[i][self.idx])

            try:
                structure_name = lab[structure_id]['name']
                structure_color = lab[structure_id]['color']
            except:
                structure_name = "no_name"
                structure_color = (0,0,0)

            r = ["%s" % structure_name.encode('utf-8')]
            for t in types:
                r+= map(str, [(a1[i][t]), a2[i][t]])

            result_string+="\t".join(r) + "\n"

        results_filename = self.options.plotComparisonNaming + "_results"
        open(results_filename, 'w').write(result_string)

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
        """

        # Get names of the gnuplot plot file, output svg file,
        # and output png file for the the normalized correlation coefficient
        # plot
        plot_file, svg_file, png_file, = \
                self._get_plot_filenames(self.options.plotComparisonNaming)
        results_filename = self.options.plotComparisonNaming + "_results"

        evaluation_plot_kwargs = { \
                'output_filename' : svg_file,
                'number_of_structures' : self.number_of_structures + 1,
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

    def launch(self):
        self.results()
        self._plot_results()

    @staticmethod
    def parseArgs():
        usage = ""

        parser = OptionParser(usage = usage)

        parser.add_option('--base', default=None,
                dest='base', action='store', type='str',
                help='Reference overlap measure.')
        parser.add_option('--compare', default=None,
                dest='compare', action='store', type='str',
                help='Overlap measure for comparison.')
        parser.add_option('--labels', default=None,
                dest='labels', action='store', type='str',
                help='File with label description.')
        parser.add_option('--plotComparisonNaming', default=None,
                dest='plotComparisonNaming', action='store', type='str',
                help='Naming of the output files.')

        (options, args) = parser.parse_args()
        return (options, args)

if __name__ == '__main__':
    options, args = overlap_comparison_summary.parseArgs()
    evaluate = overlap_comparison_summary(options, args)
    evaluate.launch()
