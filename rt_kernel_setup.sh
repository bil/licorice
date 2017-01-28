#! /bin/bash

# Before execeuting script, clone licorice repository into ~/shenoyREU

# install things
sudo apt-get update && 
sudo apt-get upgrade &&
sudo apt-get install ncurses-dev &&
sudo apt-get install build-essential &&

# download kernel and rt patch
wget ftp://ftp.kernel.org/pub/linux/kernel/v4.x/linux-4.4.12.tar.gz &&
wget http://www.kernel.org/pub/linux/kernel/projects/rt/4.4/patch-4.4.12-rt19.patch.gz &&
tar -zxvf linux-4.4.12.tar.gz &&

# move config file for kernel
cp ~/shenoyREU/.config ~/linux-4.4.12/.config

cd linux-4.4.12 &&
zcat ../patch-4.4.12-rt19.patch.gz | patch -p1 &&
sudo apt-get install kernel-package libssl-dev &&
make-kpkg clean &&
fakeroot make-kpkg –-initrd –-append-to-version=-custom kernel_image kernel_headers &&
sudo dpkg -i linux-image-4.4.12-custom-rt19_4.4.12-custom-rt19-10.00.Custom_amd64.deb &&
sudo dpkg -i linux-headers-4.4.12-custom-rt19_4.4.12-custom-rt19-10.00.Custom_amd64.deb &&
sudo reboot
