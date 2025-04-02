import importlib.util
import os
import sys


def import_all_py_files(target_directory, root_directory):
    sys.path.append(root_directory)

    # Walk through the target directory to find all .py files
    for dirpath, _, filenames in os.walk(target_directory):
        for file in filenames:
            if file.endswith('.py'):
                module_name = os.path.splitext(file)[0]
                file_path = os.path.join(dirpath, file)

                # Dynamically import the Python file as a module
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
