from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

import possum

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md', 'CHANGES.txt')

class run_tests(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import doctest

        verbose_flag = False
        print doctest.testmod(possum.pos_wrappers, verbose=verbose_flag)
        print doctest.testmod(possum.pos_parameters, verbose=verbose_flag)
        print doctest.testmod(possum.pos_wrapper_skel, verbose=verbose_flag)
        print doctest.testmod(possum.pos_common, verbose=verbose_flag)
        print doctest.testmod(possum.pos_color, verbose=verbose_flag)
        print doctest.testmod(possum.pos_segmentation_parser, verbose=verbose_flag)

setup(
    name='possum-reconstruction',
    version=possum.__version__,
    url='http://github.com/pmajka/possum/',
    license='MIT',
    author='Piotr Majka',
    install_requires=['config>=0.3.9', 'networkx>=1.6', 'numpy', 'scipy',
        'coveralls', 'xlrd', 'xlutils'],
    cmdclass={'test': run_tests},
    author_email='piotr.majka@op.pl',
    description='three dimensional image reconstruction from serial sections.',
    long_description=long_description,
    packages=['possum','bin'],
    scripts=['bin/pos_align_by_moments', 'bin/pos_coarse_fine',
             'bin/pos_deformable_histology_reconstruction',
             'bin/pos_pairwise_registration', 'bin/pos_reorder_volume',
             'bin/pos_sequential_alignment', 'bin/pos_slice_preprocess',
             'bin/pos_slice_volume', 'bin/pos_stack_sections',
             'bin/pos_stack_warp_image_multi_transform'],
    include_package_data=True,
    platforms='Linux',
    test_suite='possum.test.test_possum',
    classifiers = [
        'Programming Language :: Python :: 2.7',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        ],
    extras_require={
        'testing': ['setuptools.tests.doctest'],
    }
)
