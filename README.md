# CSE 150 Final Project: POX router
## Overview
This project was developed as the final project for CSE 150 - Intro to Computer Networks at UCSC.

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
