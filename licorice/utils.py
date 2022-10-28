import os


def __handle_completed_process(result, print_stdout=False):
    if print_stdout:
        print(result.stdout.decode())

    if result.returncode != 0:
        print(f"Completed process output: {result.stdout.decode()}")
        raise RuntimeError(result.stderr.decode())


# return valid filepath if file exists in given path_list
def __find_in_path(path_list, file, raise_error=True):
    for path in path_list:
        filepath = os.path.join(path, file)
        if os.path.exists(filepath):
            return filepath

    if raise_error:
        raise FileNotFoundError(
            f"Could not locate {file} in path: {os.pathsep.join(path_list)}."
        )
    else:
        return None
