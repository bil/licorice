#! /bin/bash

# This works for xenial-lts

# This is to be executed from the git repository directory, otherwise change REPO_DIR

# set some variables
REPO_DIR=`pwd`
KERNEL_DIR=~/rt
TMP_DIR=/tmp

# update to most recent version of packages, install essentials, do some cleanup
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install libncurses5-dev build-essential libssl-dev kernel-package
sudo apt-get -y autoremove

# download kernel and rt-patch if not exists
cd $TMP_DIR
wget -N http://www.kernel.org/pub/linux/kernel/v4.x/linux-4.4.12.tar.gz
wget -N http://www.kernel.org/pub/linux/kernel/projects/rt/4.4/older/patch-4.4.12-rt19.patch.gz

# reset kernel folder and extract linux source
rm -rf $KERNEL_DIR
mkdir -p $KERNEL_DIR
cd $KERNEL_DIR
tar -zxvf $TMP_DIR/linux-4.4.12.tar.gz

# copy kernel .config file from git
cp $REPO_DIR/.config $KERNEL_DIR/linux-4.4.12/.config

# patch kernel with realtime patch
cd $KERNEL_DIR/linux-4.4.12
zcat $TMP_DIR/patch-4.4.12-rt19.patch.gz | patch -p1

# build kernel
make-kpkg clean
CONCURRENCY_LEVEL=9 fakeroot make-kpkg --initrd --append-to-version=-licorice binary

# install kernel
sudo dpkg -i linux-image-4.4.12-custom-rt19_4.4.12-licorice-rt19-10.00.Custom_amd64.deb
sudo dpkg -i linux-headers-4.4.12-custom-rt19_4.4.12-licorice-rt19-10.00.Custom_amd64.deb

# reboot when done
#sudo reboot
