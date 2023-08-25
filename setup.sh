#!/bin/bash

CodeDir=/shared/iPATH/nowcast_module_v1
DataDir=/data/iPATH/nowcast_module_v1

# create output folders for cron logs
mkdir -p $DataDir/cron/{Background,CME,Flare}

# create output folders for simulations
mkdir -p $DataDir/{Background,CME,Flare}

# create staging area
mkdir -p $DataDir/staging/{iswa,sep_scoreboard}

# copy spacecraft and planet positions
cp -r $CodeDir/helioweb $DataDir/

# create processed CME and Flare lists
echo "[]" >$DataDir/CME/past.json
echo "[]" >$DataDir/Flare/past.json

# install crontab file
crontab crontab
