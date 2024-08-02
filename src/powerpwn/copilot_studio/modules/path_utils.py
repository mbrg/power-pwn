import os

# Determine the directory containing the current script
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Move up one level to get to the project root (if the script is in a subdirectory)
project_root = os.path.dirname(current_script_dir)


def get_project_file_path(internal_path: str, filename: str) -> str:
    """
    Get the absolute path to a file within the project directory.

    :param internal_path: The relative path to the file from the project root
    :param filename: The file name
    :return: The absolute path to the file
    """
    return os.path.join(f"{project_root}/{internal_path}", filename)
