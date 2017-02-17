# Python Import

# Core import
from add_component_directory import mkdir
from assgin_init_component import execute_assign


def start_component(name):

    try:
        # First step
        mkdir(name)

        # Second step
        execute_assign(name)

    except Exception as e:
        print e
