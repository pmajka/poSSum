from __future__ import print_function
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

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='possum',
    version=possum.__version__,
    url='http://github.com/pmajka/possum/',
    license='TODO: Define a licence',
    author='Piotr Majka',
    tests_require=['doctest>=2.6'],
    install_requires=['TODO:Provide some information hereFlask>=0.10.1',
                    'Flask-SQLAlchemy>=1.0',
                    'SQLAlchemy==0.8.2',
                    ],
    cmdclass={'test': doctest},
    author_email='piotr.majka@op.pl',
    description='Serial sections based three dimensional volume reconstruction.',
    long_description=long_description,
    packages=['possum'],
    include_package_data=True,
    platforms='Linux',
    test_suite='possum.test.test_possum',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'TODO:Natural Language :: English',
        'TODO:Environment :: Web Environment',
        'TODO:Intended Audience :: Developers',
        'TODO:License :: OSI Approved :: Apache Software License',
        'TODO:Operating System :: OS Independent',
        'TODO:Topic :: Software Development :: Libraries :: Python Modules',
        'TODO:Topic :: Software Development :: Libraries :: Application Frameworks',
        'TODO:Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    extras_require={
        'testing': ['doctest'],
    }
)

