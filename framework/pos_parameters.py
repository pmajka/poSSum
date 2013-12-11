import os

"""
pos parameters
"""

class generic_parameter(object):
    """
    """
    _str_template = None

    def __init__(self, name, value=None, str_template=None):

        # Obligatory
        self.name = name

        # Initialize default value to None. If any no-None value is provided
        # override the default one.
        self._value = None
        if value:
            self.value = value

        # Override default serialization template if non-None template is
        # provided.
        if str_template:
            self._str_template = str_template

    def _serialize(self):
        raise NotImplementedError, "Reimplement this method in a subclass"

    def __str__(self):
        return self._serialize()

    def _validate(self):
        raise NotImplementedError, "Reimplement this method in a subclass"

    def _set_value(self, value):
        self._value = value

    def _get_value(self):
        return self._value

    def _set_str_template(self, value):
        self._str_template = value

    def _get_str_template(self):
        return self._str_template

    def _set_name(self, value):
        self._name = value

    def _get_name(self):
        return self._name

    value = property(_get_value, _set_value)
    template = property(_get_str_template, _set_str_template)
    name = property(_get_name, _set_name)

class boolean_parameter(generic_parameter):
    """
    >>> p=boolean_parameter('parameter')
    >>> p #doctest: +ELLIPSIS
    <__main__.boolean_parameter object at 0x...>

    >>> print p
    <BLANKLINE>

    >>> p.value = True
    >>> print p
    True

    >>> p.name = 'something'
    >>> print p
    True

    >>> p.value = False
    >>> print p
    False

    >>> p.template
    '{_value}'

    """
    _str_template = "{_value}"

    def _serialize(self):
        if self.value is not None:
             return self._str_template.format(**self.__dict__)
        else:
            return ""

class switch_parameter(boolean_parameter):
    """
    >>> p=switch_parameter('a_switch', False, "--{_name}")
    >>> p #doctest: +ELLIPSIS
    <__main__.switch_parameter object at 0x...>

    >>> print p
    <BLANKLINE>

    >>> p.value = True
    >>> p.name = 'something'
    >>> print p
    --something

    >>> p.name = 'sth'
    >>> print p
    --sth

    >>> p.template
    '--{_name}'

    >>> p.template = '--{_value} --{_name}'
    >>> print p
    --True --sth
    """


class string_parameter(generic_parameter):
    """
    >>> p=string_parameter('a_name')

    >>> p #doctest: +ELLIPSIS
    <__main__.string_parameter object at 0x...>

    >>> print p
    <BLANKLINE>

    >>> p.value

    >>> p.value = "a_value"

    >>> print p
    a_value

    >>> del p
    >>> p=string_parameter('a_name', value="a_value")
    >>> print p
    a_value

    >>> del p
    >>> p=string_parameter('a_name', value="a_value")
    >>> print p
    a_value

    >>> p=string_parameter('a_name', value="a_value", str_template="__{_value}__ __{_name}__")
    >>> print p
    __a_value__ __a_name__
    """
    _str_template = "{_value}"

    def _serialize(self):
        if self.value is not None:
            return self._str_template.format(**self.__dict__)
        else:
            return ""

class filename_parameter(string_parameter):
    """
    This class is designed to be used as a filename.
    When creating filename parameter this class should be used instead of generic class :class:`string_parameter`.
    """
    _str_template = "{_value}"


class value_parameter(string_parameter):
    """
    This class sould be used to handle any string parameter. This class should be used instead
    """
    _str_template = "{_value}"


class list_parameter(generic_parameter):
    """

    A generic class for storing list parameters. The class accepts a list as a
    value.  During serialization, the list is mapped to string and joined with a
    delimiter. The default delimiter is a space. Note that only strings can be
    delimiters. Passing other types (such as ints, floats or other lists) will
    cause exceptions.

    >>> p=list_parameter()
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 arguments (1 given)

    >>> p=list_parameter(value=[1,2,3])
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 non-keyword arguments (1 given)

    >>> p=list_parameter(name='test')
    >>> p #doctest: +ELLIPSIS
    <__main__.list_parameter object at 0x...>

    >>> p=list_parameter(name='test', value=[1,2,3,4])
    >>> print p
    1 2 3 4

    >>> p.name
    'test'
    >>> p.value
    [1, 2, 3, 4]
    >>> p._delimiter
    ' '

    >>> p._delimiter='-'
    >>> print p
    1-2-3-4

    >>> p._delimiter=str
    >>> print p
    Traceback (most recent call last):
    TypeError: descriptor 'join' requires a 'str' object but received a 'list'

    >>> p._delimiter=9
    >>> print p
    Traceback (most recent call last):
    AttributeError: 'int' object has no attribute 'join'

    """
    _str_template = "{_list}"
    _delimiter = " "

    def _serialize(self):
        if self.value:
            self._list = self._delimiter.join(map(str, self.value))
            return self._str_template.format(**self.__dict__)
        else:
            return ""

class vector_parameter(list_parameter):
    """
    A specialized class for holding lists which are intended to be a vector.  A
    default delimiter for this class is an "x" character. Otherwise it is a
    regular :class:`list_parameter`

    >>> p=vector_parameter('number-of-iterations', [10000,10000,10000], "--{_name} {_list}")
    >>> p #doctest: +ELLIPSIS
    <__main__.vector_parameter object at 0x...>

    >>> print p
    --number-of-iterations 10000x10000x10000

    >>> p.name
    'number-of-iterations'

    >>> p.template
    '--{_name} {_list}'

    >>> p._list
    '10000x10000x10000'

    >>> p.name = 'any_name'
    >>> print p
    --any_name 10000x10000x10000

    >>> p.value
    [10000, 10000, 10000]
    >>> p.value = (0,0,0,0)
    >>> print p
    --any_name 0x0x0x0

    """
    _delimiter = 'x'


class ants_specific_parameter(generic_parameter):
    """
    This class cannot be instantized. Use one of the subclasses instead.
    """
    _switch = None

    def _serialize(self):
        meaning = self.value[0]
        values = self.value[1]

        retStr = " " + self._switch + " " + meaning + "["
        retStr += ",".join(map(str, values))
        retStr += "] "

        return retStr

class ants_transformation_parameter(ants_specific_parameter):
    """
    >>> ants_transformation_parameter
    <class '__main__.ants_transformation_parameter'>

    >>> p=ants_transformation_parameter(value=['Gauss',(0,0)])
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 non-keyword arguments (1 given)

    >>> p=ants_transformation_parameter('test', value=['Gauss',(0,0)])
    >>> p #doctest: +ELLIPSIS
    <__main__.ants_transformation_parameter object at 0x...>

    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -t Gauss[0,0]

    >>> p.value=['Gauss', (1.0, 1)]
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -t Gauss[1.0,1]

    >>> p.value=['reg_type', (1.0, 1)]
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -t reg_type[1.0,1]

    >>> p._switch
    '-t'

    """
    _switch = '-t'


class ants_regularization_parameter(ants_specific_parameter):
    """
    >>> ants_regularization_parameter
    <class '__main__.ants_regularization_parameter'>

    >>> p=ants_regularization_parameter()
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 arguments (1 given)

    >>> print ants_regularization_parameter('a_parameter')
    Traceback (most recent call last):
    TypeError: 'NoneType' object is unsubscriptable

    >>> print ants_regularization_parameter(value=['s'])
    Traceback (most recent call last):
    TypeError: __init__() takes at least 2 non-keyword arguments (1 given)

    >>> print ants_regularization_parameter('a_parameter', value=[9,0])
    Traceback (most recent call last):
    TypeError: cannot concatenate 'str' and 'int' objects

    >>> print ants_regularization_parameter('a_parameter', value=['s'])
    Traceback (most recent call last):
    IndexError: list index out of range

    >>> p=ants_regularization_parameter('a_parameter', value=['s',(2,2)])
    >>> p #doctest: +ELLIPSIS
    <__main__.ants_regularization_parameter object at 0x...>

    >>> p=ants_regularization_parameter('a_parameter', value=['Gauss',(2,2)])
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -r Gauss[2,2]

    >>> p.name
    'a_parameter'

    >>> p.name='xxxx'
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -r Gauss[2,2]

    >>> p.value
    ['Gauss', (2, 2)]

    >>> p.value=['Regularization', (0.0, 0.2)]
    >>> print p #doctest: +NORMALIZE_WHITESPACE
    -r Regularization[0.0,0.2]

    >>> p._switch
    '-r'
    """
    _switch = '-r'


class filename(generic_parameter):
    """
    >>> filename('name', job_dir="", work_dir="", str_template="{value}") #doctest: +SKIP

    Class representing a filename template for files being a part of some
    workflow. The template can be customized, the class is callable and returns
    filename according to prvided arguments.

    The only legal way of invocating this class is the one shown with above.
    Following parameters are required to make this class behave properly: :py:attr:`name`,
    :py:attr:`job_dir`, :py:attr:`work_dir`, :py:attr:`str_template`.

    :param name: Required but very rarely used in real applications. One can use
        it by putting `{_name}` string into the :py:attr:`str_template`. Actually it's legacy
        parameter from the parrent class.
    :type name: str

    :param value: Required, defaults to ``None``, Can be used in file name
        by putting `{_value}` into :py:attr:`str_template`. Can be an empty string but not ``None``
    :type value: any serializable object

    :param job_dir: Required. home directory of given workflow. Can be an empty string but not ``None``
    :type job_dir: str

    :param work_dir: directory of the file,
    :type work_dir: str

    :param str_template: filename template without any paths, just the
        filename's basename (with extension). Parameters are processed according
        to python `.format` function. Cannot be empty or ``None``.
    :type str_template: str

    """

    def __init__(self, name, value=None, str_template=None,
                 job_dir=None, work_dir=None):
        """
        >>> filename('name', job_dir="", work_dir="", str_template="{value}") #doctest: +SKIP

        >>> filename()
        Traceback (most recent call last):
        TypeError: __init__() takes at least 2 arguments (1 given)

        >>> filename("test")()
        Traceback (most recent call last):
        AttributeError: 'NoneType' object has no attribute 'format'

        >>> filename("test", job_dir="/",work_dir=".")()
        Traceback (most recent call last):
        AttributeError: 'NoneType' object has no attribute 'format'

        >>> filename("test_name", "test_value", job_dir="", work_dir="", str_template="{_value}")()
        'test_value'

        >>> filename("test_name", "test_value", job_dir="", work_dir="",  str_template="{_name}")()
        'test_name'

        >>> filename("test_name", "test_value", job_dir="/a_dir/", work_dir="", str_template="{_name}")()
        '/a_dir/test_name'

        >>> filename("test_name", "test_value", job_dir="/a_dir/", work_dir="a_workdir", str_template="{_name}")()
        '/a_dir/a_workdir/test_name'

        >>> f=filename("test_name", "test_value", job_dir="/a_dir/",
        ... work_dir="a_workdir", str_template="{_name}_{_value}.txt")
        >>> f # doctest: +ELLIPSIS
        <__main__.filename object at 0x...>

        >>> f() == '/a_dir/a_workdir/test_name_test_value.txt'
        True

        >>> str(f) == '/a_dir/a_workdir/test_name_test_value.txt'
        True

        >>> f.base_dir == '/a_dir/a_workdir'
        True

        >>> f.job_dir == '/a_dir/'
        True

        >>> f.name == 'test_name'
        True

        >>> f.override_path == None
        True

        >>> f.override_fname == None
        True

        >>> f.override_dir == None
        True

        >>> f.updateParameters()
        Traceback (most recent call last):
        TypeError: updateParameters() takes exactly 2 arguments (1 given)

        >>> f.value == 'test_value'
        True

        override_dir property

        >>> f.override_dir == None
        True
        >>> f.job_dir == '/a_dir/'
        True
        >>> f.override_dir="overriding/default/workdir"
        >>> f() == 'overriding/default/workdir/test_name_test_value.txt'
        True

        >>> f.override_dir=None
        >>> f() == '/a_dir/a_workdir/test_name_test_value.txt'
        True

        override_path property

        >>> f.override_path == None
        True
        >>> f() == '/a_dir/a_workdir/test_name_test_value.txt'
        True
        >>> f.override_path = "this_overrides_whole_output"
        >>> f() == 'this_overrides_whole_output'
        True
        >>> f.override_path = None
        >>> f() == '/a_dir/a_workdir/test_name_test_value.txt'
        True

        override filename

        >>> f.override_fname == None
        True
        >>> f() == '/a_dir/a_workdir/test_name_test_value.txt'
        True
        >>> f.override_fname = "overrided_filename.txt"
        >>> f() == '/a_dir/a_workdir/overrided_filename.txt'
        True
        >>> f.override_fname = None
        >>> f() == '/a_dir/a_workdir/test_name_test_value.txt'
        True

        str_template and passing arguments:

        >>> f.template = '{_name}_{_value}.txt'
        >>> f() == '/a_dir/a_workdir/test_name_test_value.txt'
        True
        >>> f.template = '{_name}.txt'
        >>> f() == '/a_dir/a_workdir/test_name.txt'
        True
        >>> f.template = '{index:04d}.txt'
        >>> f()
        Traceback (most recent call last):
        KeyError: 'index'
        >>> f(index=3) == '/a_dir/a_workdir/0003.txt'
        True

        >>> f.template = '{iteration:02d}/{index:04d}.txt'
        >>> f(index=3)
        Traceback (most recent call last):
        KeyError: 'iteration'
        >>> f(index=3,iteration=1) == '/a_dir/a_workdir/01/0003.txt'
        True

        """

        generic_parameter.__init__(self, name, value=value,
                 str_template=str_template)

        self.job_dir = job_dir
        self.work_dir = work_dir

        # Possibility of complex behaviour, see docstrings

        self.override_dir = None
        """
        Directory that overrides both, `job_dir` and `work_dir`. This can be
        reverted by assigning none to this propoerty.
        """

        self.override_fname = None
        """
        Override filename leaving all directory prefixes unaffected. Revertible.
        """

        self.override_path = None
        """
        String that overrides the output by provided value. The function becomes
        then insensible to any argumnets. The output is the same regardless the
        arguments provided. This can be reverted by nulling this property.
        """

    def _get_job_dir(self):
        return self._job_dir

    def _set_job_dir(self, value):
        self._job_dir = value

    def _get_work_dir(self):
        return self._work_dir

    def _set_work_dir(self, value):
        self._work_dir = value

    def _get_base_dir(self):
        return os.path.join(self.job_dir, self.work_dir)

    def _set_base_dir(self, value):
        pass

    def updateParameters(self, parameters):
        for (name, value) in parameters.items():
            setattr(self, name, value)
        return self

    def _serialize(self):
        if self.override_fname:
            return self.override_fname
        else:
            return self._str_template.format(**self.__dict__)

    def __str__(self):
        if self.override_dir:
            return os.path.join(self.override_dir, self._serialize())
        if self.override_path:
            return self.override_path

        return os.path.join(self.job_dir, self.work_dir, self._serialize())

    def __call__(self, **parameters):
        self.updateParameters(parameters)
        return str(self)

    job_dir = property(_get_job_dir, _set_job_dir)
    """ Returns / sets job_dir """

    work_dir = property(_get_work_dir, _set_work_dir)
    """ Returns / sets work """

    base_dir = property(_get_base_dir, _set_base_dir)
    """ Returns / sets base_dir """

if __name__ == '__main__':
    import doctest
    doctest.testmod()
