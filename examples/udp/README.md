# UDP

Install pyenv and LiCoRICE according to README.

Open up three terminals:

1. Sending UDP packets

Run:

```bash
cd examples/modules
bash send_udp.sh
```

2. Running licorice to receive and place udp packet in a SharedArray

Set LiCoRICE working directory:

```bash
export LICORICE_WORKING_DIR=/<path>/<to>/<licorice>/examples
```

Run:

```bash
sudo rm /dev/shm/*
licorice go udp_demo
```

3. Running server to retrieve information

Fix /dev/shm permissions if necessary:

```bash
sudo chmod 777 /dev/shm/*
```

Run:

```bash
cd examples/modules
python udp_poll.py
```
