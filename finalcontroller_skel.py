# finalcontroller_skel.py - POX controller for the CSE 150 final project
# Kyle Won, UCSC
# kwon, 1724327
# CSE 150 Final Project

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr
import pox.lib.packet as pkt

# Set debug mode to print information to console
DEBUG_MODE = False
log = core.getLogger()
timeout = 50

# For every switch in the network, map connected devices (hosts or switches) to ports
# Used for general IP traffic routing
CoreSwitchConnections = {
  "DataCenterSwitch": 1,
  "Floor1Switch1": 2,
  "Floor1Switch2": 3,
  "Floor2Switch1": 4,
  "AirGappedSwitch": 5,
  "104.24.32.100": 6,  # Trusted Host
  "108.44.83.103": 7,  # Untrusted Host 
}

DataCenterSwitchConnections = {
  "30.1.4.66": 2
}
Floor1Switch1Connections = {
  "20.2.1.10": 2,
  "20.2.1.20": 3
}
Floor1Switch2Connections = {
  "20.2.1.30": 2,
  "20.2.1.40": 3
}
Floor2Switch1Connections = {
  "10.2.7.10": 2,
  "10.2.7.20": 3
}

class Final (object):
  """
  A Firewall object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
 
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

  # Returns true if destination host is contained in the given list of hosts connected to a switch
  def deviceConnectedToSwitch(self, destination, switchConnections):
    return switchConnections.get(str(destination)) is not None

  # Returns the port on a switch that a host is connected to
  def getOutputPort(self, destination, switchConnections):
    return switchConnections.get(str(destination))

  # Accepts ARP traffic. Floods the network
  def acceptARP(self, packet, packet_in):
    if DEBUG_MODE:
      print "ARP packet - accept"
    msg = of.ofp_flow_mod()
    match = of.ofp_match()
    match.dl_type = pkt.ethernet.ARP_TYPE
    msg.match = match
    msg.idle_timeout = timeout
    msg.hard_timeout = timeout
    msg.buffer_id = packet_in.buffer_id
    msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
    self.connection.send(msg)

  # Accepts IP traffic between two specific hosts on two specific ports
  def acceptIP(self, packet, packet_in, ip_header, in_port, out_port):
    if DEBUG_MODE:
      print "IP packet from ",
      print ip_header.srcip,
      print " to ",
      print ip_header.dstip,
      print " - allow"
    msg = of.ofp_flow_mod()
    match = of.ofp_match()
    match.dl_type = pkt.ethernet.IP_TYPE
    match.nw_proto = pkt.ipv4.IPv4
    match.in_port = in_port
    match.nw_src = ip_header.srcip
    match.nw_dst = ip_header.dstip
    msg.match = match
    msg.idle_timeout = timeout
    msg.hard_timeout = timeout
    msg.buffer_id = packet_in.buffer_id
    msg.actions.append(of.ofp_action_output(port=out_port))
    self.connection.send(msg)

  # Accepts traffic using exact packet and in-port match. Floods the network
  def acceptFlood(self, packet, packet_in, in_port):
    if DEBUG_MODE:
      print "Non-IP packet - accept flood"
    msg = of.ofp_flow_mod()
    match = of.ofp_match.from_packet(packet, in_port)
    msg.match = match
    msg.idle_timeout = timeout
    msg.hard_timeout = timeout
    msg.buffer_id = packet_in.buffer_id
    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    self.connection.send(msg)

  # Unused in current implementation
  def dropUnconditional(self, packet, packet_in, duration = None):
    if duration is not None:
      if DEBUG_MODE:
        print "Packet match drop"
      msg = of.ofp_flow_mod()
      match = of.ofp_match.from_packet(packet)
      msg.match = match
      msg.idle_timeout = duration
      msg.hard_timeout = duration
      msg.buffer_id = packet_in.buffer_id
      # omit action to drop packet
      self.connection.send(msg)
    elif packet_in.buffer_id is not None:
      if DEBUG_MODE:
        print "Unconditional drop - single"
      msg = of.ofp_flow_mod()
      msg.buffer_id = packet_in.buffer_id
      self.connection.send(msg)
    else:
      if DEBUG_MODE:
        print "IGNORING PACKET on drop uncondition"

  # Drop packet of certain protocol between two specific hosts
  def dropProtocol(self, packet, packet_in, ip_header, protocol=None):
    if DEBUG_MODE:
      print "Want to drop packet of type",
      print protocol
    msg = of.ofp_flow_mod()
    match = of.ofp_match()
    match.dl_type = pkt.ethernet.IP_TYPE
    if protocol is "ICMP":
      match.nw_proto = pkt.ipv4.ICMP_PROTOCOL
    elif protocol is "TCP":
      match.nw_proto = pkt.ipv4.TCP_PROTOCOL
    elif protocol is "IP":
      match.nw_proto = pkt.ipv4.IPv4
    match.nw_src = ip_header.srcip
    match.nw_dst = ip_header.dstip
    msg.match = match
    msg.idle_timeout = timeout
    msg.hard_timeout = timeout
    msg.buffer_id = packet_in.buffer_id
    # omit action to drop
    self.connection.send(msg)

  # Secure client port id is same as subnet host id + 1 (port 1 connects to core switch)
  # Ex: secure client ip address = 40.2.5.3 --> switch port number 4
  def getSecureClientOutPort(self, secureClientIP):
    return int(str(secureClientIP).split('.')[3]) + 1

  # Determines if a given IP address is part of a subnet defined by the given subnet mask
  # Format of 24 bit subnetMask: x.x.x.0
  # Format of IP address: x.x.x.x
  def match24BitSubnetMask(self, subnetMask, ip):
    subnetNums = subnetMask.split('.')
    ipNums = str(ip).split('.')
    for i in range(0,3):
      if subnetNums[i] != ipNums[i]:
        if DEBUG_MODE:  
          print "IP",
          print str(ip),
          print " not part of subnet",
          print subnetMask
        return False
    return True
  
  # This is where you'll put your code. The following modifications have 
  # been made from Lab 3:
  #   - port_on_switch: represents the port that the packet was received on.
  #   - switch_id represents the id of the switch that received the packet.
  #      (for example, s1 would have switch_id == 1, s2 would have switch_id == 2, etc...)
  # You should use these to determine where a packet came from. To figure out where a packet 
  # is going, you can use the IP header information.
  def do_final (self, packet, packet_in, port_on_switch, switch_id):
    # Parse packet information
    ip_header = packet.find('ipv4')
    icmp_header = packet.find('icmp')
    tcp_header = packet.find('tcp')
    arp_header = packet.find('arp')  

    # Allow all ARP packets
    if arp_header is not None:
      self.acceptARP(packet, packet_in)
      return
    elif ip_header is not None:
      sourceIP = ip_header.srcip
      destinationIP = ip_header.dstip
    else: # Flood all other non-IP traffic
      self.acceptFlood(packet, packet_in, port_on_switch)
      return

    # Implied IP traffic from here on out
    if switch_id == 6:  # Air-gapped switch
      if DEBUG_MODE:
        print "Switch 6"
        print sourceIP,
        print " -> ",
        print destinationIP
      # Traffic only allowed between secure clients
      if self.match24BitSubnetMask("40.2.5.0", sourceIP) and self.match24BitSubnetMask("40.2.5.0", destinationIP):
        out_port = self.getSecureClientOutPort(destinationIP)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      else:
        # Drop all other traffic that doesn't originate from Air-Gapped floor 
        self.dropProtocol(packet, packet_in, ip_header, "IP")
        return
    # ENFORCE TCP RULES
    if tcp_header is not None:
      # Trusted Host cannot send TCP to Web Server
      if sourceIP == IPAddr("104.24.32.100") and destinationIP == IPAddr("30.1.4.66"):
        self.dropProtocol(packet, packet_in, ip_header, "TCP")
        return
    # ENFORCE ICMP RULES
    elif icmp_header is not None:
      protocol = "ICMP"
      # Untrusted Host cannot send ICMP to Floor 1, Floor 2, or Web Server
      if ip_header.srcip == IPAddr("108.44.83.103"):
        if self.match24BitSubnetMask("20.2.1.0", destinationIP) or self.match24BitSubnetMask("10.2.7.0", destinationIP) or destinationIP == IPAddr("30.1.4.66"):
          self.dropProtocol(packet, packet_in, ip_header, protocol)
          return 
      # Trusted Host cannot send ICMP traffic Floor 1 Department A, or Web Server
      if ip_header.srcip == IPAddr("104.24.32.100"):
        if self.match24BitSubnetMask("20.2.1.0", destinationIP) or destinationIP == IPAddr("30.1.4.66"):
          self.dropProtocol(packet, packet_in, ip_header, protocol)
          return
      # Hosts in Floor 1 Dept. A cannot send ICMP traffic to Floor 2 Dept. B, and vice versa
      if self.match24BitSubnetMask("20.2.1.0", sourceIP) and self.match24BitSubnetMask("10.2.7.0", destinationIP):
        self.dropProtocol(packet, packet_in, ip_header, protocol)
        return
      if self.match24BitSubnetMask("10.2.7.0", sourceIP) and self.match24BitSubnetMask("20.2.1.0", destinationIP):
        self.dropProtocol(packet, packet_in, ip_header, protocol)
        return
    
    # Examine fallthrough IP traffic
    # All IP traffic must have specified destination ports
    if switch_id == 1:  # Core switch
      if DEBUG_MODE:
        print "Switch 1"
      if self.deviceConnectedToSwitch(destinationIP, DataCenterSwitchConnections):
        # Send from Core to Data Center
        out_port = self.getOutputPort("DataCenterSwitch", CoreSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      elif self.deviceConnectedToSwitch(destinationIP, Floor1Switch1Connections):
        # Send from Core to Floor 1 Switch 1
        out_port = self.getOutputPort("Floor1Switch1", CoreSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      elif self.deviceConnectedToSwitch(destinationIP, Floor1Switch2Connections):
        # Send from Core to Floor 1 Switch 2
        out_port = self.getOutputPort("Floor1Switch2", CoreSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      elif self.deviceConnectedToSwitch(destinationIP, Floor2Switch1Connections):
        # Send from Core to Floor 2 Switch 1
        out_port = self.getOutputPort("Floor2Switch1", CoreSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      elif self.match24BitSubnetMask("40.2.5.0", destinationIP):
        # Send from Core to Air Gapped Switch
        out_port = self.getOutputPort("AirGappedSwitch", CoreSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      elif destinationIP == IPAddr("104.24.32.100"):
        # Send from Core to Trusted Host
        out_port = self.getOutputPort(destinationIP, CoreSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      elif destinationIP  == IPAddr("108.44.83.103"):
        # Send from Core to Untrusted Host
        out_port = self.getOutputPort(destinationIP, CoreSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      else:
        return  # Implicitly drop all other traffic
    elif switch_id == 2:  # Data center switch
      if DEBUG_MODE:
        print "Switch 2"
      if sourceIP == IPAddr("108.44.83.103") and destinationIP == IPAddr("30.1.4.66"):
        # Drop IP traffic going from Untrusted Host to Web Server
        self.dropProtocol(packet, packet_in, ip_header, "IP")
        return
      if self.deviceConnectedToSwitch(destinationIP, DataCenterSwitchConnections):
        # Send from Data Center to Web Server
        out_port = self.getOutputPort(destinationIP, DataCenterSwitchConnections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      else:
        # Send all IP traffic outgoing from Data Center to Core
        out_port = 1
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
    elif switch_id == 3:  # Floor 1 Switch 1
      if DEBUG_MODE:
        print "Switch 3"
      if self.deviceConnectedToSwitch(destinationIP, Floor1Switch1Connections):
        # Send from Floor 1 Switch 1 connected Host
        out_port = self.getOutputPort(destinationIP, Floor1Switch1Connections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      else:
        # Send all IP traffic outgoing from Floor 1 Switch 1 to Core
        out_port = 1
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
    elif switch_id == 4:  # Floor 1 Switch 2
      if DEBUG_MODE:
        print "Switch 4"
      if self.deviceConnectedToSwitch(destinationIP, Floor1Switch2Connections):
        # Send from Floor 1 Switch 2 to connected Host
        out_port = self.getOutputPort(destinationIP, Floor1Switch2Connections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      else:
        # Send all IP traffic outgoing from Floor 1 Switch 2 to Core
        out_port = 1
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
    elif switch_id == 5:  # Floor 2 Switch 1
      if DEBUG_MODE:
        print "Switch 5"
      if self.deviceConnectedToSwitch(destinationIP, Floor2Switch1Connections):
        # Send from Floor 2 Switch 1 to connected Host
        out_port = self.getOutputPort(destinationIP, Floor2Switch1Connections)
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      else:
        # Send all IP traffic outgoing from Floor 2 Switch 1 to Core
        out_port = 1
        self.acceptIP(packet, packet_in, ip_header, port_on_switch, out_port)
        return
      
    # All other fallthrough traffic implicitly dropped (nothing should reach here)
    return

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """
    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.
    self.do_final(packet, packet_in, event.port, event.dpid)

def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Final(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
