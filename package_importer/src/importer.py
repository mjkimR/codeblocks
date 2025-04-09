import glob
import importlib.util
import os


def import_all_py_files(package_directory: str, root_directory: str) -> None:
    """
    Dynamically imports all Python (*.py) files within a specified directory.

    This function calculates the Python import path relative to the provided
    `root_directory` and attempts to import each module. It's often used for
    plugin systems or dynamic module loading.

    Warning: Importing all files from a directory can execute arbitrary code.
             Only use this function with trusted directories.

    Args:
        package_directory (str): The path to the directory containing the Python
            files to import. This directory should logically represent a Python
            package or sub-package.
        root_directory (str): The path to the root of the package structure.
            This directory path acts as the base for determining the Python
            module path (e.g., if root is '/proj' and package is '/proj/plugins',
            imports will start like 'plugins.module'). For successful imports,
            this `root_directory` or one of its parent directories containing
            the full package structure should typically be part of Python's
            `sys.path`.

    Raises:
        ValueError:
            - If `root_directory` is not a valid directory path.
            - If `package_directory` is not a valid directory path.
            - If `package_directory` cannot be made relative to `root_directory`
              (e.g., it's not located within the `root_directory` structure,
              or resides on a different drive).
        ImportError: If a module cannot be found by Python's import system,
            or if an import statement *within* an imported module fails.
        Exception: If any other unexpected error occurs during the import
            process or during the execution of the imported module's top-level code.

    Returns:
        None
    """
    # Validate directories first
    if not os.path.isdir(root_directory):
        raise ValueError(f"Root directory '{root_directory}' not found or is not a directory.")
    if not os.path.isdir(package_directory):
        raise ValueError(f"Package directory '{package_directory}' not found or is not a directory.")

    try:
        rel_package_path = os.path.relpath(package_directory, root_directory)
        if rel_package_path.startswith('..'):
            raise ValueError(
                f"Package directory '{package_directory}' is not inside root directory '{root_directory}'."
            )
    except ValueError as e:
        raise ValueError(
            f"Could not determine relative path from '{root_directory}' to '{package_directory}'. "
            f"Ensure it's nested correctly and on the same filesystem structure."
        ) from e
    if rel_package_path == '.':
        base_package_path = ''
    else:
        base_package_path = rel_package_path.replace(os.sep, '.')

    for f_path in glob.glob(os.path.join(package_directory, "*.py")):
        if f_path.endswith("__init__.py"):
            continue

        module_name = os.path.basename(f_path)[:-3]
        if base_package_path:
            full_module_path = f"{base_package_path}.{module_name}"
        else:
            # If base_package_path is empty (package_directory == root_directory)
            full_module_path = module_name

        try:
            importlib.import_module(full_module_path)
        except ImportError as e:
            raise ImportError(f"Error importing module '{full_module_path}': {e}") from e
        except Exception as e:
            raise Exception(f"An unexpected error occurred related to module '{full_module_path}': {e}") from e
