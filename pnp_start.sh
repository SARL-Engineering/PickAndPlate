#!/bin/bash

# This sleep needed to make sure openbox has started first
sleep 5

# Export the display variable so the following applications have a valid display
export DISPLAY=:0

# Sets the background
feh --bg-scale /home/debian/PickAndPlate_Extras/pnp-background.png

# Short sleep so you can see the background
sleep 1.5

# Start the main pick and plate application (move to directory)
if [ ! -f /home/debian/PickAndPlate/noautostart ]
then
    cd /home/debian/PickAndPlate/
    /usr/bin/python /home/debian/PickAndPlate/PickAndPlate.py &
fi
