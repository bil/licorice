# TODO convert python dicts to C structs

from collections.abc import Iterable

from jinja2 import Template

data = {
    "custom": {
        "float32_signal": {
            "shape": 1,
            "dtype": "float32",
            "log": {
                "enable": True,
                "table": "custom",
                "type": "scalar",
                "num_cols": 1,
            },
            "max_packets_per_tick": 11,
            "sig_shape": "(5000,1)",
            "history": 5000,
            "buf_tot_numel": 5000,
            "packet_size": 1,
            "ctype": "float",
            "dtype_msgpack": "float",
            "bytes": 4,
            "buf_size_bytes": 44,
            "latency": 0,
            "dtype_short": "f4",
        },
        "int8_signal": {
            "shape": 1,
            "dtype": "int8",
            "log": {
                "enable": True,
                "table": "custom",
                "type": "scalar",
                "num_cols": 1,
            },
            "max_packets_per_tick": 11,
            "sig_shape": "(5000,1)",
            "history": 5000,
            "buf_tot_numel": 5000,
            "packet_size": 1,
            "ctype": "int8_t",
            "dtype_msgpack": "int8",
            "bytes": 1,
            "buf_size_bytes": 11,
            "latency": 0,
            "dtype_short": "i1",
        },
    },
    "int64_signal": {
        "int64_signal": {
            "shape": (1, 1),
            "dtype": "int64",
            "log": {
                "enable": True,
                "table": "signal",
                "type": "msgpack",
                "num_cols": 1,
            },
            "max_packets_per_tick": 11,
            "sig_shape": "(5000,1, 1)",
            "history": 5000,
            "buf_tot_numel": 5000,
            "packet_size": 1,
            "ctype": "int64_t",
            "dtype_msgpack": "int64",
            "bytes": 8,
            "buf_size_bytes": 88,
            "latency": 0,
            "schema": {
                "max_packets_per_tick": 11,
                "data": {"dtype": "int64", "size": 1},
            },
            "dtype_short": "i8",
        }
    },
}

struct_template = """
typedef struct {
    {%- for key, value in members.items() %}
    {{ value }} {{ key }};
    {%- endfor %}
} {{ struct_name }};
"""


# Function to render nested structs
def render_struct(data, struct_name="TestStruct"):
    members = {}
    template = Template(struct_template)
    rendered_output = ""

    # if isinstance(data, dict):
    # elif isinstance(data, Iterable):
    for key, value in data.items():
        if isinstance(value, str):
            members[key] = "char *"
        elif isinstance(value, int):
            members[key] = "int"
        elif isinstance(value, bool):
            members[key] = "bool"
        elif isinstance(value, dict):
            sub_struct_name = key.capitalize()
            members[key] = sub_struct_name
            rendered_output += (
                render_struct(value, struct_name=sub_struct_name) + "\n"
            )
        elif isinstance(value, Iterable):
            members[key] = "array"
        else:
            raise NotImplementedError(
                f"{type(value)} type can't be converted."
            )

    template = Template(struct_template)
    rendered_output += template.render(
        members=members, struct_name=struct_name
    )
    return rendered_output


c_code = render_struct(data)
print(c_code)
