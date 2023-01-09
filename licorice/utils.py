import os


def __handle_completed_process(result, print_stdout=False):
    if print_stdout:
        print(result.stdout.decode())

    if result.returncode != 0:
        print(f"Completed process output: {result.stdout.decode()}")
        raise RuntimeError(result.stderr.decode())


# return valid filepath if any of files exists in given path_list
def __find_in_path(path_list, files, raise_error=True):
    if type(files) != list:
        files = [files]
    for path in path_list:
        for file in files:
            filepath = os.path.join(path, file)
            if os.path.exists(filepath):
                return filepath

    if raise_error:
        raise FileNotFoundError(
            f"Could not locate {file} in path: {os.pathsep.join(path_list)}."
        )
    else:
        return None

# recursively update dict, overwriting conflicts with update
def __dict_deep_update(orig_dict, update_dict):
    for k, v in orig_dict.items():
        if k not in update_dict:
            update_dict[k] = v
        elif isinstance(v, dict):
            __dict_deep_update(v, update_dict[k])
    return update_dict
