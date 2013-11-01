from pos_wrappers import generic_wrapper
from pos_parameters import list_parameter

class multiple_commands_wrapper_1(generic_wrapper):
    """
    """
    _template = """echo "1" ; echo "2" """

class multiple_commands_wrapper_2(generic_wrapper):
    """
    """
    _template = """echo "1" && echo "2" """

class multiple_commands_wrapper_3(generic_wrapper):
    """
    """
    _template = """echo "1" || echo "2" """

class multiple_commands_wrapper_4(generic_wrapper):
    """
    """
    _template = """echo {echoes}"""

    _parameters = {
        'echoes': list_parameter('echoes', [], str_template='{_list}'),
    }

if __name__ == '__main__':
    multiple_commands_wrapper_1()()
    multiple_commands_wrapper_2()()
    multiple_commands_wrapper_3()()
    cmd = multiple_commands_wrapper_4(echoes=['2','2'])
    cmd()
