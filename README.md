# CSE 150 Final Project: POX router
## Overview
This project was developed as a final project for CSE 150 - Intro to Computer Networks at UCSC. The goal of this project is to implement forwarding rules in the control plane of a software-defined enterprise network. The network is simulated in Mininet and the controller uses the POX framework to communicate with 6 simulated OpenFlow switches.  

Please read the [project writeup](https://github.com/kyle2277/POX-router/blob/2c642c553e1e4c6778bdafee9bf06c803fdd6108/final_project_writeup.pdf) for detailed information regarding the network topology, forwarding rules, and testing methodology.

## Requirements
* Mininet
* POX

## How to Run
1. Start mininet network  
  `$ sudo python final_topology.py`
2. Put `final_controller.py` in `<pox directory>/pox/misc`  
3. In a second terminal tab, start the POX remote controller  
  `$ <pox directory>/pox.py misc.final_controller`  
4. Type commands into mininet console  
  Ex: `laptop ping -c 5 h_server`  
