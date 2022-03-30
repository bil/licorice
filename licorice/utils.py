def __handle_completed_process(result, print_stdout=False):
    if print_stdout:
        print(result.stdout.decode())

    if result.returncode != 0:
        print(f"Completed process output: {result.stdout.decode()}")
        raise RuntimeError(result.stderr.decode())
