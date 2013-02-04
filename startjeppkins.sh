#!/bin/sh

echo "Starting skypekit"
nohup python startskypekit.py --skypekit=./linux-x86-skypekit-voicepcm-novideo 2>&1 &
sleep 5
echo "Starting jeppkins"
python jeppkins.py # >jeppkins.out 2>&1 &
#sleep 5

