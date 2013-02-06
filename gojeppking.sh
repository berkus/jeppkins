#!/bin/sh

#while true
#do
    echo "Starting skypekit"
    #nohup python startskypekit.py --skypekit=./linux-x86-skypekit-voicepcm-novideo --debuglogname=debuglog --kitlog=kitlog 2>&1 &
    nohup python startskypekit.py --skypekit=./linux-x86-skypekit-voicepcm-novideo 2>&1 &
    sleep 5
    echo "Starting jeppkins"
    python jeppkins.py # >jeppkins.out 2>&1 &
    #sleep 10
#done

