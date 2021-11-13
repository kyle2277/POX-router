#!/usr/bin/python

# final_skel.py - Mininet network topology for the CSE 150 final project
# Kyle Won, UCSC
# kwon, 1724327
# CSE 150 Final Project

import math
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import RemoteController

class final_topo(Topo):

  # Adds secure client hosts to the network depending on given subnet address and mask
  # Example subnetIPAddress input: 40.2.5.0/29
  def defineSecureClients(self, subnetIPAddress):
    subnetInfo = subnetIPAddress.split('/')
    subnetAddress = subnetInfo[0]
    subnetMask = subnetInfo[1]
    numberClients = (2 ** (32 - int(subnetMask))) - 2
    for i in range(1, numberClients + 1):
      clientName = "client" + str(i)
      clientMAC = "00.00.00.00.00." + str(i * 10)
      clientIP = subnetAddress[0: len(subnetAddress) - 1] + str(i)
      clientRoute = clientName + "-eth0"
      #print "client name: " + clientName
      #print "client MAC address: " + clientMAC
      #print "client IP address: " + clientIP
      #print "client default route: " + clientRoute
      self.addHost(clientName, mac=clientMAC, ip=clientIP, defaultRoute=clientRoute)
    return numberClients

  # Links given number of secure clients (named "client<i>") to given switch
  def linkSecureClients(self, numClients, switch):
    # switch port 1 connected to core switch
    switchPort = 2
    for i in range(1, numClients + 1):
      client = "client" + str(i)
      self.addLink(switch, client, port1=switchPort, port2=0)
      switchPort += 1

  def build(self):
    # Examples!
    # Create a host with a default route of the ethernet interface. You'll need to set the
    # default gateway like this for every host you make on this assignment to make sure all 
    # packets are sent out that port. Make sure to change the h# in the defaultRoute area
    # and the MAC address when you add more hosts!
    # h1 = self.addHost('h1',mac='00:00:00:00:00:01',ip='1.1.1.1/24', defaultRoute="h1-eth0")
    # h2 = self.addHost('h2',mac='00:00:00:00:00:02',ip='2.2.2.2/24', defaultRoute="h2-eth0")
    
    # Data center
    web_server = self.addHost('h_server', mac='00.00.00.00.00.66', ip='30.1.4.66/24', defaultRoute="h_server-eth0")
    # Floor 1
    laptop = self.addHost('laptop', mac='00:00:00:00:00:01', ip='20.2.1.10/24', defaultRoute="laptop-eth0")
    lab_machine = self.addHost('lab_mac', mac='00:00:00:00:00:02', ip='20.2.1.20/24', defaultRoute="lab_mac-eth0")
    device1 = self.addHost('device1', mac='00.00.00.00.00.03', ip='20.2.1.30/24', defaultRoute="device1-eth0")
    device2 = self.addHost('device2', mac='00.00.00.00.00.04', ip='20.2.1.40/24', defaultRoute="device2-eth0")
    # Floor 2
    host1 = self.addHost('host1', mac='00.00.00.00.00.05', ip='10.2.7.10/24', defaultRoute="host1-eth0")
    host2 = self.addHost('host2', mac='00.00.00.00.00.06', ip='10.2.7.20/24', defaultRoute="host2-eth0")
    # Other hosts
    trusted_host = self.addHost('h_trust', mac='00.00.00.00.00.07', ip='104.24.32.100/24', defaultRoute="h_trust-eth0")
    untrusted_host = self.addHost('h_untrust', mac='00.00.00.00.00.08', ip='108.44.83.103/24', defaultRoute="h_untrust-eth0")
    # Air-gapped floor secure clients
    numSecureClients = self.defineSecureClients('40.2.5.0/29')

    # Create a switch. No changes here from Lab 1.
    # s1 = self.addSwitch('s1')    

    # Network core
    core_s1 = self.addSwitch('s1') # switch_id 1
    # Data center    
    data_center_s2 = self.addSwitch('s2') # switch_id 2
    # Floor 1
    floor1_s3 = self.addSwitch('s3') # switch_id 3
    floor1_s4 = self.addSwitch('s4') # switch_id 4
    # Floor 2
    floor2_s5 = self.addSwitch('s5') # switch_id 5
    # Air-gapped floor
    AG_floor_s6 = self.addSwitch('s6') # switch_id 6
    
    # Connect Port 8 on the Switch to Port 0 on Host 1 and Port 9 on the Switch to Port 0 on 
    # Host 2. This is representing the physical port on the switch or host that you are 
    # connecting to.
    #
    # IMPORTANT NOTES: 
    # - On a single device, you can only use each port once! So, on s1, only 1 device can be
    #   plugged in to port 1, only one device can be plugged in to port 2, etc.
    # - On the "host" side of connections, you must make sure to always match the port you 
    #   set as the default route when you created the device above. Usually, this means you 
    #   should plug in to port 0 (since you set the default route to h#-eth0).
    #
    # self.addLink(s1,h1, port1=8, port2=0)
    # self.addLink(s1,h2, port1=9, port2=0)

    # Network core
    # core (1) <--> data center (1)
    self.addLink(core_s1, data_center_s2, port1=1, port2=1)
    # core (2) <--> floor1_s1 (1)
    self.addLink(core_s1, floor1_s3, port1=2, port2=1)
    # core (3) <--> floor1_s2 (1)
    self.addLink(core_s1, floor1_s4, port1=3, port2=1)
    # core (4) <--> floor2_s1 (1)
    self.addLink(core_s1, floor2_s5, port1=4, port2=1)
    # core (5) <--> AG_floor_s1 (1)
    self.addLink(core_s1, AG_floor_s6, port1=5, port2=1)
    # core (6) <--> trusted_host (0)
    self.addLink(core_s1, trusted_host, port1=6, port2=0)
    # core (7) <--> untrusted_host (0)
    self.addLink(core_s1, untrusted_host, port1=7, port2=0), 
    # Data center
    # data_center_s1 (2) <--> web_server (0)
    self.addLink(data_center_s2, web_server, port1=2, port2=0)
    # Floor 1
    # floor1_s1 (2) <--> laptop (0)
    self.addLink(floor1_s3, laptop, port1=2, port2=0)
    # floor1_s1 (3) <--> lab_machine (0)
    self.addLink(floor1_s3, lab_machine, port1=3, port2=0)
    # floor1_s2 (2) <--> device1 (0)
    self.addLink(floor1_s4, device1, port1=2, port2=0)
    # floor1_s2 (3) <--> device2 (0)
    self.addLink(floor1_s4, device2, port1=3, port2=0)
    # Floor 2
    # floor2_s1 (2) <--> host1 (0)
    self.addLink(floor2_s5, host1, port1=2, port2=0)
    # floor2_s1 (3) <--> host2 (0)
    self.addLink(floor2_s5, host2, port1=3, port2=0)
    # Air-gapped floor
    # AG_floor_s1 (2) <--> secure_clients (0)
    self.linkSecureClients(numSecureClients, AG_floor_s6) 

    print "Hello network"

def configure():
  topo = final_topo()
  #net = Mininet(topo=topo)
  net = Mininet(topo=topo, controller=RemoteController)
  net.start()

  CLI(net)
  
  net.stop()


if __name__ == '__main__':
  configure()
