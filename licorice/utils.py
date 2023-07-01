import os
from collections.abc import Iterable


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


class BitMask:
    def __init__(self, mask):
        if type(mask) is int:
            self.int = mask
        elif type(mask) is str:
            if mask[0:2] == "0x":  # hex format
                self.int = int(mask, base=16)
            elif mask[0:2] == "0b":  # binary format
                self.int = int(mask, base=2)
            elif mask[0:2] == "0o":  # octal format
                self.int = int(mask, base=8)
            else:  # decimal format
                self.int = int(mask)
        elif isinstance(mask, Iterable):
            self.int = sum(list(map(lambda x: 2**x, mask)))
        else:
            raise ValueError()
        self.hex_str = hex(self.int)
        self.binary_str = bin(self.int)
        self.bit_list = []
        for i, b in enumerate(self.binary_str[:1:-1]):
            if b == "1":
                self.bit_list.append(i)

    def __repr__(self):
        return f"licorice.utils.BitMask({self.hex_str})"

    def __str__(self):
        return self.hex_str

    def __eq__(self, other):
        return self.int == other.int

    def __ne__(self, other):
        return not self.__eq__(other)

    def inverse(self, num_cores):
        return BitMask(self.int ^ int("1" * num_cores, base=2))
