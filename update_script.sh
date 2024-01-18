#!/bin/bash

# RUN THIS SCRIPT ON ANOTHER MACHINE
# ./update_script.sh

# the time interval in seconds
x=4

# loops forever
while :
do
    python distributed.py
    
    # sleep for x seconds
    sleep $x
done