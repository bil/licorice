# UDP

Install pyenv and LiCoRICE according to README.

Open up two terminals:

1. Send UDP packets

Run:

```bash
cd examples/udp
./send_udp.sh
```

2. Running licorice to receive and print packets

Set LiCoRICE working directory:

```bash
export LICORICE_WORKING_DIR=/<path>/<to>/<licorice>/examples
```

Run:

```bash
cd examples/udp
./run.sh
```
