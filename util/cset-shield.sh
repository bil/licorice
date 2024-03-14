NUM_SYS_CPUS=1
sudo cset shield -r
sudo cset shield --cpu=$NUM_SYS_CPUS-$((`nproc --all`-1)) --kthread on
sudo chown -R $USER:lico /sys/fs/cgroup/cpuset/user
