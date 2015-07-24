#!/usr/bin/python
# -*- coding: utf-8 -*


import sys
import os
import subprocess as sub
import multiprocessing

import time
import datetime
import logging
from optparse import OptionParser, OptionGroup

import pos_common
import pos_wrappers


class generic_workflow(object):
    """
    A generic command-line workflow class. Workflow should be understood as a
    configurable pipeline with a configurable execution settings.

    The workflow / pipeline may consist of different stages use a numbser of
    different files, etc. The reason for this class is to use command line
    tools which functionality cannot be achieved in any other way.

    >>> options, args = generic_workflow.parseArgs()
    >>> options.dry_run = True

    >>> w = generic_workflow(options, args) #doctest: +ELLIPSIS
    Executing: mkdir -p /dev/shm/generic_workflow_...
    <BLANKLINE>
    <BLANKLINE>

    >>> w.execute(["some command", "another command"])
    some command
    another command

    >>> w.execute(["a batch comprising only one command"])
    a batch comprising only one command

    >>> w.execute("Bad_usage")
    B
    a
    d
    _
    u
    s
    a
    g
    e

    You have to provide some argument, at least one
    >>> w.execute()
    Traceback (most recent call last):
    TypeError: execute() takes at least 2 arguments (1 given)

    All arguments are mapped to strings
    >>> w.execute(1)
    1

    >>> w.execute([1, 2.3, False, None])
    1
    2.3
    False
    None


    # Now let's test the ability of the workflow to compress its own
    # workflow directory.
    >>> w.options.archive_work_dir = "/some/directory/to/archive/stuff/"
    >>> w._archive_workflow() #doctest: +ELLIPSIS
    tar -cvvzf /some/directory/to/archive/stuff/generic_workflow_...tgz /dev/shm/generic_workflow_...


    # Ok, let's remove the existing workflow object and create a new one with
    # slightly more settings. First of all, these settings cause the workflow
    # to use the local /tmp/ directory instead or the shared RAM memoru of the
    # system. Note that this is still machine-local directory and is not
    # shared between different execution nodes. This only replaces the
    # /dev/shm/ with the /tmp/ directory and that's it.

    # The next change is that the dry run option is actually turned on so the
    # commands will be actually executed not only printed. This may cause a lot
    # of mess - but hey - that's what you call testing!
    >>> options, args = generic_workflow.parseArgs()
    >>> options.disable_shared_memory = True
    >>> options.dry_run = False
    >>> options.cleanup = True
    >>> options.archive_work_dir = "/tmp/"

    >>> w = generic_workflow(options, args) #doctest: +ELLIPSIS
    Executing: mkdir -p /tmp/generic_workflow_...
    <BLANKLINE>
    <BLANKLINE>

    # To test out the execution routines one has to actually execute some
    # commands therefore below we execute a command which does not produce any
    # output.
    >>> w.execute(["sleep 1"]) ==  ('', '')
    True

    # Now we test archiving and cleanup routines by manually executing a pre
    # and postlaunch methods. In the meanwhile we want to test the archiving
    # feature as well
    >>> w._pre_launch()
    >>> w._post_launch() #doctest: +ELLIPSIS
    Executing: tar -cvvzf /tmp/generic_workflow_....tgz /tmp/generic_workflow_...
    ...
    Executing: rm -rfv /tmp/generic_workflow_...
    removed `/tmp/generic_workflow_...'
    removed directory: `/tmp/generic_workflow_...'
    <BLANKLINE>

    """

    # Define the name for GNU parallel executeble name.
    __PARALLEL_EXECUTABLE_NAME = "parallel"

    # _f is a dictionary holding definitions of files beeing a part of the
    # workflow. The purpose of this dictionary is to be able to easily access
    # and utilize filenames (from each stage of the workflow). You're gonna
    # like it.
    _f = {}

    # Override this attribute in the inherited classes.
    _usage = ""

    # Just to avoid hadcoded strings further
    _DO_NOT_CREATE_WORKDIR = 'skip'

    def __init__(self, options, args):
        """
        :param optionsDict: Command line options
        :type optionsDict: dict

        :param args: Command line arguments
        :type args: list
        """

        self.options = options
        self.args = args

        # Just an alias that assigns private attribute as a public. May be
        # changed in the future.
        self.f = dict(self._f)

        # Get number of cpus for parallel processing.
        # Multiprocessing modlue is used to determine the number of cpus. This
        # behavior can be overriden with --cpus switch.
        if not self.options.cpus:
            self.options.cpus = multiprocessing.cpu_count()

        self._initializeLogging()
        self._initializeOptions()
        self._validate_options()
        self._initializeDirectories()
        self._overrideDefaults()

    def _initializeLogging(self):
        """
        Seems to be self explaining - initialized the logging module using
        either ethe default logging settings or customized logging settings
        according to provided command line paramteres.
        """
        pos_common.setup_logging(self.options.log_filename,
                      self.options.loglevel)

        logging.debug("Logging module initialized. Saving to: %s, Loglevel: %s",
                      self.options.log_filename, self.options.loglevel)

        # Assign the the string that will identify all messages from this
        # script
        self._logger = logging.getLogger(self.__class__.__name__)

        self._logger.info("%s workflow options:", self.__class__.__name__)
        for k, v in self.options.__dict__.items():
            self._logger.info("%s : %s", k, v)

    def _initializeOptions(self):
        """
        There is not many to process or initialize. Actually only jobID (if not
        provided) is processed automatically.
        """

        # What the heck is a "specimen ID"? It is supposed to be at least
        # single value which will allow to assign an instance of the workflow
        # to particual animal. When you have multiple animals they can get
        # confused easily. In the future, specimen ID, will act as database ID
        # for given specimen. Thus, it is hardcoded to not allow any
        # computations without this ID. Simple as it is.

        # We need to check if the GNU parallel of availeble. If it's not, we
        # cannot perform parallel computations.
        if not pos_common.which(self.__PARALLEL_EXECUTABLE_NAME) and\
           self.options.cpus > 1:
            self._logger.error("Parallel execution was selected but GNU parallel is not available!")
            sys.exit(1)

        # Job ID is another value for accointing and managing. Oppoosite to the
        # specimen ID, this one may not be explicitly stated. In that case, it
        # is generated automatically based on current data and PID.
        if self.options.job_id is None:
            self.options.job_id = self.__class__.__name__
            self.options.job_id += datetime.datetime.now().strftime("_%Y-%m-%d-%H_%M-%S_")
            self.options.job_id += str(os.getpid())

    def _overrideDefaults(self):
        """
        A generic function for altering configuration that was set with
        default values. Should be reimplemented in subclasses.
        """
        pass

    def _validate_options(self):
        """
        A generic command line options validation function. Should be
        customized in subclasses. A lot of assertions is expected to be here!
        """
        pass

    def _initializeDirectories(self):
        """
        """
        # The directiories in the dictionary below are the potential working
        # dirs for the workflow. The 'sharedbf' is used when given mashine has
        # a ramdisk, otherwise 'tempbf'. These are the default locations for
        # the workdir. Typically, the working directory location is a custom
        # one.
        _dirTemplates = {
            'sharedbf': '/dev/shm/',
            'tempbf': '/tmp/'}

        # Sometimes we just don't want create any work_dir (e.g. out workflow
        # is done without creating any files. When 'workdir' command line
        # parameter is set to skip, we just skip it. Anything that happens
        # afterwards is a liability of the develeoper.
        if self.options.workdir == self._DO_NOT_CREATE_WORKDIR:
            return

        # That's clever idea: When one don't want (or cannot) use shared memory
        # on given mashine, the regular /tmp/ directory is used to support the
        # computations.  The tmp directory can be also set manually to, e.g.,
        # directory shared among whole computer cluster.
        if self.options.disable_shared_memory:
            top_directory = _dirTemplates['tempbf']
        else:
            top_directory = _dirTemplates['sharedbf']

        # If the working directory (the directory holding all the
        # job's calculations) is not defined, we define it automatically
        # When the working directory name IS provided we just use it.
        if not self.options.workdir:
            self.options.workdir =\
                os.path.join(top_directory, self.options.job_id)
        self._ensureDir(self.options.workdir)

        # Assign path to work dir to all templates:
        for k, v in self.f.iteritems():
            v.job_dir = self.options.workdir

        # And, as a last point, just create the directories.
        dirs_to_create = list(set(map(lambda v: v.base_dir,
                                      self.f.itervalues())))
        map(self._ensureDir, dirs_to_create)

    def _ensureDir(self, path):
        """
        Makes sure that the given directory exists and is avalilable.

        :param path: Location to be tested. Note that only directory names are
        valid paths. Passing filenames will probably end badly...
        :type path: str
        """
        return pos_wrappers.mkdir_wrapper(dir_list=[path])()

    def _rmdir(self, path):
        """
        Removes given location. Watch out as the files and/or directories are
        removed recursively and uninvertabely (as in `rm -rfv` command).

        :param path: Location to be removed.
        :type path: str
        """
        return pos_wrappers.rmdir_wrapper(dir_list=[path])()

    @staticmethod
    def _basename(path, withExtension=False):
        return pos_common.get_basename(path, withExtension)

    def execute(self, commands, parallel=True):
        """
        One of the most important methods in the whole class. Executes the
        workflow. The execution can be launched in parallel mode, and / or in
        the 'dry run' mode. With the latter, the commands to be executed are
        actually only printed.  The 'dry run' mode is selected / deselected
        using command line workflow settings.

        :param commands: The commands to be executed
        :type commands: An interable (in case of multiple commands - the usual
                        case), a string in case of a singe command.

        :param parallel: Enables execution in parallel mode
        :type parallel: bool
        """

        # (https://docs.loni.org/wiki/PBS_Job_Chains_and_Dependencies)
        # http://librarian.phys.washington.edu/athena/index.php/Job_Submission_Tutorial#NEW:_PBS_Job_Dependencies_.28advanced.29
        # http://beige.ucs.indiana.edu/I590/node45.html

        # If single command is provided, it is supposed to be a string. Convert
        # to list with a single element.
        if not hasattr(commands, "__getitem__"):
            commands = [commands]

        # In the regular execution mode (no dry-run) the commands can be
        # executed serially or parallelly. In the latter case, all the commands
        # are dumped into a file and executed with the GNU parallel.
        if not self.options.dry_run:

            command_filename = \
                os.path.join(self.options.workdir, str(time.time()))
            open(command_filename, 'w').write("\n".join(map(str, commands)))
            self._logger.info("Saving command file: %s", command_filename)

            if parallel:
                cluster_file = os.path.join(os.getenv("HOME"), '.pos_cluster')
                if os.path.isfile(cluster_file):
                    command_str = 'parallel --sshloginfile %s -a %s -k -j %d --env PATH --env PYTHONPATH --env LD_LIBRARY_PATH --workdir %s' %\
                        (cluster_file, command_filename, self.options.cpus, os.getcwd())
                else:
                    command_str = 'parallel -a %s -k -j %d' %\
                        (command_filename, self.options.cpus)
            else:
                command_str = 'bash -x %s' % command_filename

            self._logger.debug("Executing: %s", command_str)

            # Tested against execution of multiple commands
            stdout, stderr = sub.Popen(command_str,
                                stdout=sub.PIPE, stderr=sub.PIPE,
                                shell=True, close_fds=True).communicate()

            self._logger.debug("Last commands stdout: %s", stdout)
            self._logger.debug("Last commands stderr: %s", stderr)

            return stdout, stderr

        else:
            print "\n".join(map(str, commands))

    def launch(self):
        """
        The workflow execution routine. Has to be customized and documenten in
        every subclass A stub of method. Raise NotImplementedError. Every
        `lauch` method has to invoke _post_launch()`_pre_launch()` and
        `_post_launch()` as they are required to run the workflow properly.
        """
        raise NotImplementedError, "Virtual method executed."

    def _pre_launch(self):
        """
        A generic just-before-execution rutine. Should be customized in
        subclasses.
        """
        pass

    def _post_launch(self):
        """
        A generic pos-execution routine. Should be customized in subclasses. In
        its most basic form, it provides archiving the workflow and removing
        the job directory. If you want you can customize it so it will send you
        a notification email!
        """
        if self.options.archive_work_dir:
            self._archive_workflow()

        if self.options.cleanup:
            self._clean_up()

    def _archive_workflow(self):
        """
        This method archived the workdir of the current workflow. The archive
        name taken from the JobDir option while the dir of the archive is
        provided by the `archive_work_dir` command line parameter.

        There's nothing much more to tell about this method... well, watch out
        as the archive may be really (by which I mean really big). Be prepared
        for gigabytes.
        """
        archive_filename = os.path.join(self.options.archive_work_dir,
                                        self.options.job_id)

        self._logger.info("Archive basename: %s",
                          generic_workflow._basename(archive_filename))
        self._logger.info("Archiving the job directory to: %s",
                          archive_filename)

        compress_command = pos_wrappers.compress_wrapper(
            archive_filename=archive_filename,
            pathname=self.options.workdir)

        # Well, sometimes you don't want to execute the archive command
        # esspecially when not other command was executed.
        if not self.options.dry_run:
            compress_command()
        else:
            print compress_command

    def _clean_up(self):
        """
        Erases the job's working directory.
        """
        self._logger.info("Removing job directory.")

        self._rmdir(self.options.workdir)

    @classmethod
    def _getCommandLineParser(cls):
        """
        """
        parser = OptionParser(usage=cls._usage)

        workflowSettings = OptionGroup(parser, 'General workflow settings')
        workflowSettings.add_option('--job-id', '-j', dest='job_id', type='str',
                default=None, help='Job identifier. An optional value identyfying this particular workflow. If ommited, the job_id will be generated automatically.')
        workflowSettings.add_option('--work-dir', '-d', dest='workdir', type='str',
                default=None, help='Sets the working directory of the process. Overrides the "--disable-shared-memory" switch.')
        workflowSettings.add_option('--loglevel', dest='loglevel', type='str',
                default='WARNING', help='Loglevel: CRITICAL | ERROR | WARNING | INFO | DEBUG')
        workflowSettings.add_option('--log-filename', dest='log_filename',
                default=None, action='store', type='str',
                help='Sets dumping the execution log file instead stderr')
        workflowSettings.add_option('--disable-shared-memory', default=False,
            dest='disable_shared_memory', action='store_const', const=True,
            help='Forces script to use hard drive to store the worklfow data instaed of using RAM disk.')
        workflowSettings.add_option('--specimen-id', default=None,
                dest='specimen_id', action='store', type='str',
                help='Identifier of the specimen. Providing the ID is obligatory. Script will not run without providing specimen ID.')
        workflowSettings.add_option('--dry-run', default=False,
                action='store_const', const=True, dest='dry_run',
                help='Prints the commands to stdout instead of executing them')
        workflowSettings.add_option('--cpus', default=None,
                type='int', dest='cpus',
                help='Set a number of CPUs for parallel processing. If skipped, the number of CPUs will be automatically detected.')
        workflowSettings.add_option('--archive-work-dir', default=None,
                type='str', dest='archive_work_dir',
                help='Compresses (.tgz) and moves workdir to a given directory')
        workflowSettings.add_option('--cleanup', default=False,
                dest='cleanup', action='store_const', const=True,
                help='Remove the worklfow directory after calculations. Use when you are sure that the workflow will execute correctly.')
        parser.add_option_group(workflowSettings)
        return parser

    @classmethod
    def parseArgs(cls):
        parser = cls._getCommandLineParser()
        (options, args) = parser.parse_args()
        return (options, args)


class output_volume_workflow(generic_workflow):
    """
    This class is designed to support workflows providing volume as one of the
    outputs. It handles additional command line parameters for defining the
    origin, spacing, orientation, type, anatomical orientation and many many
    other.

    >>> options, args = output_volume_workflow.parseArgs()
    >>> options.parallel = False

    >>> w = output_volume_workflow(options, args) #doctest: +ELLIPSIS
    Executing: mkdir -p /dev/shm/output_volume_workflow_...
    <BLANKLINE>
    <BLANKLINE>

    >>> print w.execute(["sleep 1"], parallel=False)[0] == ''
    True

    >>> print w.execute(["sleep 1"], parallel=False)[1].strip() == "+ sleep 1"
    True

    """

    __output_vol_command_line_args_help = {}
    __output_vol_command_line_args_help['outputVolumeOrigin'] =\
"""Set the origin of the image --  the center of the voxel (0,0,0) in the image.
Should be specified in millimeters. Default: 0,0,0."""
    __output_vol_command_line_args_help['outputVolumeScalarType'] =\
"""Specifies the pixel type for the output image.  Data type for output volume's
voxels. The allowed values are: char | uchar | short | ushort | int | uint |
float | double. The default type, unlike in Convert3d is char."""
    __output_vol_command_line_args_help['outputVolumeSpacing'] =\
"""Sets the voxel spacing of the image.  A vector of three positive values is
required (e.g. '0.5 0.5 0.5'). The spacing is assumed to be provided in
milimeters. The defaults spacing is 1x1x1mm."""
    __output_vol_command_line_args_help['outputVolumeResample'] =\
"""Requests additional resampling of the output volume. The resampling is
applied _before_ settting the output spacing. The resampling settings are
provided as three positive float values corresponding to the resampling factor
(e.g. 0.25 1.0 0.75). Watch out when combining this whith other parameters like
setting spacing. By default there is no resampling."""
    __output_vol_command_line_args_help['outputVolumePermutationOrder'] =\
"""Apply axes permutation. Permutation has to be provided as sequence of 3
integers separated by space. Identity (0,1,2) permutation is a default one."""
    __output_vol_command_line_args_help['outputVolumeOrientationCode'] =\
"""Set the orientation of the image using one of 48 canonical orientations. The
orientation describes the mapping from the voxel coordinate system (i,j,k) to
the physical coordinate system (x,y,z). In the voxel coordinate system, i runs
along columns of voxels, j runs along rows of voxels, and k runs along slices
of voxels. It is assumed (by the NIFTI convention) that the axes of the
physical coordinate system run as follows: x from (L)eft to (R)ight, y from
(P)osterior to (A)nterior, z from (I)nferior to (S)uperior.  (the explanation
is copied from Convert3D documentation:
http://www.itksnap.org/pmwiki/pmwiki.php?n=Convert3D.Documentation)"""
    __output_vol_command_line_args_help['setInterpolation'] =\
"""Specifies the interpolation method for resampling the output volume. Be
default the linear interpolation is set. The other allowed values are:
    NearestNeighbor | Linear | Cubic | Sinc | Gaussian."""
    __output_vol_command_line_args_help['setFlip'] =\
"""Select axes to flip. Selection has to be provided as sequence of three
numbers. E.g. \'0 0 1\' will flip the z axis."""


    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        outputVolumeSettings = \
            OptionGroup(parser, 'Output volumes settings')
        outputVolumeSettings.add_option('--output-volume-origin',
            dest='outputVolumeOrigin',
            default=[0., 0., 0.], action='store', type='float', nargs=3,
            help=cls.__output_vol_command_line_args_help['outputVolumeOrigin'])
        outputVolumeSettings.add_option('--outputVolumeScalarType', default='uchar',
            type='choice', dest='outputVolumeScalarType',
            choices=['char','uchar','short','ushort','int','uint','float','double'],
            help=cls.__output_vol_command_line_args_help['outputVolumeScalarType'])
        outputVolumeSettings.add_option('--output-volume-spacing', default=[1, 1, 1],
            type='float', nargs=3, dest='outputVolumeSpacing',
            help=cls.__output_vol_command_line_args_help['outputVolumeSpacing'])
        outputVolumeSettings.add_option('--outputVolumeResample',
            dest='outputVolumeResample', type='float', nargs=3, default=None,
            help=cls.__output_vol_command_line_args_help['outputVolumeResample'])
        outputVolumeSettings.add_option('--output-volume-permute-axes', default=[0, 1, 2],
            type='int', nargs=3, dest='outputVolumePermutationOrder',
            help=cls.__output_vol_command_line_args_help['outputVolumePermutationOrder'])
        outputVolumeSettings.add_option('--output-volume-orientation',
            dest='outputVolumeOrientationCode', type='str', default='RAS',
            help=cls.__output_vol_command_line_args_help['outputVolumeOrientationCode'])
        outputVolumeSettings.add_option('--setInterpolation',
            dest='setInterpolation', type='str', default=None,
            help=cls.__output_vol_command_line_args_help['setInterpolation'])
        outputVolumeSettings.add_option('--flip',
            dest='setFlip', type='str', default=None,
            help=cls.__output_vol_command_line_args_help['setFlip'])

        parser.add_option_group(outputVolumeSettings)
        return parser


class enclosed_workflow(generic_workflow):
    """
    A base for workflows not utilizing temporary direcotries.

    This workflow is deditacted for pipelines that don't use working
    directories and which do not store temponary data aduring processing. It
    has disabled some features regarding jobdirs, parallel execution, cleaning
    up the working directories, etc.

    >>> options, args = enclosed_workflow.parseArgs()
    >>> w = enclosed_workflow(options, args) #doctest: +ELLIPSIS

    """
    def _initializeOptions(self):
        super(enclosed_workflow, self)._initializeOptions()

        # Force workdir to be 'skip' as we do not want to create
        # A job directory for this script. Alse, we set dry_run and
        # cleanup to false, as this workflow does not use any
        # directories. Everything is done iin the memory.
        # Moreover, we set cpuNo to 1 as it does not matter :)
        self.options.workdir = self._DO_NOT_CREATE_WORKDIR
        self.options.dry_run = False
        self.options.cleanup = False
        self.options.cpus = 1

if __name__ == 'possum.pos_wrapper_skel':
    import doctest
    doctest.testmod()
