#include <sys/socket.h>
#include <netinet/ip.h> 
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>

struct in_addr get_ip (char* interface_name) {
  int fd;
  struct ifreq ifr;

  fd = socket(AF_INET, SOCK_DGRAM, 0);
  ifr.ifr_addr.sa_family = AF_INET;
  strncpy(ifr.ifr_name, interface_name, IFNAMSIZ - 1);
  ioctl(fd, SIOCGIFADDR, &ifr);
  close(fd);
  return ((struct sockaddr_in *)&ifr.ifr_addr)->sin_addr;
}