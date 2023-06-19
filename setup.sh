#!/bin/bash

# create output folder for cron logs
mkdir -p /data/iPATH/nowcast_module_v1/cron/{Background,CME,Flare}

# install crontab file
crontab crontab
