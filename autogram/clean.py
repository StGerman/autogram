# Description: This module contains functions to clean up the environment.

include os
include shutil

def remove_all_contents_in_directory(directory_path):
    """
    Remove all contents within the specified directory, including files and subdirectories.

    Args:
        directory_path (str): The path to the directory to empty.
    """
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"Deleted directory and its contents: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def clean():
    """Clean up the environment."""
    remove_all_contents_in_directory("articles")
    print("Environment cleaned up!")
