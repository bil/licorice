#! /bin/bash

set -ev

# Kernel patch script
SRC_FILE=${BASH_SOURCE[0]:-$0}

# Set high-level versions
# UBUNTU_VERSION=18.04
# KERNEL_RT_VERSION=4.16.18-rt12
UBUNTU_VERSION=${LICO_UBUNTU_VERSION:-20.04}
KERNEL_RT_VERSION=${LICO_KERNEL_RT_VERSION:-5.4.230-rt80}
ENABLE_USB=${LICO_ENABLE_USB:-1}
MANUAL_CONFIG=${LICO_MANUAL_CONFIG:-0}
KERNEL_VERSION_TEXT=$( cd "$( dirname "${SRC_FILE}" )" && git describe --tags )
if [ $ENABLE_USB -eq 1 ]; then
    CONFIG_FILENAME=.config_usb
else
    CONFIG_FILENAME=.config
    KERNEL_VERSION_TEXT="${KERNEL_VERSION_TEXT}-no-usb"
fi

# set some variables
INSTALL_DIR=$( cd "$( dirname "${SRC_FILE}" )" && pwd )
KERNEL_DIR=~/.licorice/rt_kernel
TMP_DIR=/tmp

NUM_CPUS=`grep processor /proc/cpuinfo|wc -l`

KERNEL_VERSION=$( echo ${KERNEL_RT_VERSION} | cut -d- -f1 )
RT_PATCH=$( echo ${KERNEL_RT_VERSION} | cut -d- -f2 )

KERNEL_VERSION_0=$( echo ${KERNEL_VERSION} | cut -d. -f1 )
KERNEL_VERSION_1=$( echo ${KERNEL_VERSION} | cut -d. -f2 )
KERNEL_VERSION_2=$( echo ${KERNEL_VERSION} | cut -d. -f3 )

# update to most recent version of packages, install essentials, do some cleanup
export DEBIAN_FRONTEND=noninteractive
export DEBIAN_PRIORITY=critical
sudo -E apt-get -y update
sudo -E apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" upgrade
sudo -E apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" install libncurses5-dev build-essential libssl-dev dwarves libelf-dev flex bison openssl dkms libelf-dev libudev-dev libpci-dev libiberty-dev autoconf bc
sudo apt-get -y autoremove

# download kernel and rt-patch if not exists
cd $TMP_DIR
#wget https://git.kernel.org/pub/scm/linux/kernel/git/rt/linux-stable-rt.git/snapshot/linux-stable-rt-5.4.209-rt77.tar.gz
wget https://www.kernel.org/pub/linux/kernel/v${KERNEL_VERSION_0}.x/linux-${KERNEL_VERSION}.tar.gz
wget https://www.kernel.org/pub/linux/kernel/projects/rt/${KERNEL_VERSION_0}.${KERNEL_VERSION_1}/older/patch-${KERNEL_VERSION}-${RT_PATCH}.patch.gz

# to check signature
#
# sudo apt-get install gnupg2
# gpg2 --locate-keys torvalds@kernel.org gregkh@kernel.org
# gpg2 --generate-key # Enter name and email; create password
# wget -N https://kernel.org/pub/linux/kernel/v5.x/linux-5.4.209.tar.sign
# gunzip linux-5.4.209.tar.gz
# gpg2 --verify linux-5.4.209.tar.sign linux-5.4.209.tar


# reset kernel folder and extract linux source
rm -rf $KERNEL_DIR
mkdir -p $KERNEL_DIR
cd $KERNEL_DIR
tar -zxvf ${TMP_DIR}/linux-${KERNEL_VERSION}.tar.gz
cd linux-${KERNEL_VERSION}
zcat ${TMP_DIR}/patch-${KERNEL_VERSION}-${RT_PATCH}.patch.gz | patch -p1


# manually edit config
# make menuconfig
if [ $MANUAL_CONFIG -eq 1 ]; then
    exit
else
# copy kernel .config file from git
# TODO download this from appropriate bucket given Ubuntu version
cp ${INSTALL_DIR}/${CONFIG_FILENAME} ${KERNEL_DIR}/linux-${KERNEL_VERSION}/.config
fi

# build kernel
cd ${KERNEL_DIR}/linux-${KERNEL_VERSION}
# TODO revisit
# https://askubuntu.com/questions/1329538/compiling-the-kernel-5-11-11
scripts/config --set-str SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str SYSTEM_REVOCATION_KEYS ""
make clean
make -j $NUM_CPUS
sudo make INSTALL_MOD_STRIP=1 modules_install
sudo make install
sudo update-initramfs -c -k ${KERNEL_VERSION}-${RT_PATCH}-licorice-${KERNEL_VERSION_TEXT}
sudo update-grub

# notify reboot when done
printf "\n\n%s\n" "Kernel installation complete. Please reboot the system."
#sudo reboot
