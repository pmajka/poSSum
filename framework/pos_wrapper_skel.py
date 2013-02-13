#!/usr/bin/python
import sys, os
import multiprocessing
import subprocess as sub

import time, datetime
from optparse import OptionParser, OptionGroup
import copy
import pos_wrappers

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
            }

    _usage = ""

    def __init__(self, options, args, pool = None):
        self.options = options
        self.args = args

        self.f = dict(self._f)

        # Get number of cpus for parallel processing
        # even if parallel processing is disabled
        if not self.options.cpuNo:
            self.options.cpuNo = multiprocessing.cpu_count()

        # If no cpu pool is provided, create and
        # assign a new pool
        if pool:
            self.pool = pool
        else:
            self.pool = multiprocessing.Pool(processes=self.options.cpuNo)

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
        return pos_wrappers.mkdir_wrapper(dir_list = [path])()

    def _rmdir(self, path):
        return pos_wrappers.rmdir_wrapper(dir_list = [path])()

    @staticmethod
    def _basesame(path, withExtension = False):
        return getBasesame(path, withExtension)

    def _cleanUp(self, immediate = False):
        self._rmdir(self.options.workdir)

    def execute(self, commands, parallel = True):
        if not hasattr(commands, "__getitem__"):
            commands = [commands]

        if not self.options.dryRun:
            if parallel:
                command_filename = os.path.join(self.options.workdir, str(time.time()))
                open(command_filename, 'w').write("\n".join(map(str,commands)))
                os.system('cat %s | parallel -k -j %d ' % \
                        (command_filename, self.options.cpuNo))
            else:
                map(lambda x: x(), commands)
        else:
            print "\n".join(map(str,commands))

    def execute_callable(self, command):
        if self.options.dryRun:
            print command
        else:
            command()

    @classmethod
    def _getCommandLineParser(cls):
        """
        """
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
        workflowSettings.add_option('--dryRun', default=False,
                action='store_const', const=True, dest='dryRun',
                help='Prints commands instead of executing them')
        workflowSettings.add_option('--cpuNo', '-n', default=None,
                type='int', dest='cpuNo',
                help='Number of cpus during parallel processing')

        parser.add_option_group(workflowSettings)
        return parser

    @classmethod
    def parseArgs(cls):
        parser = cls._getCommandLineParser()
        (options, args) = parser.parse_args()
        return (options, args)


if __name__ == '__main__':
    pass
