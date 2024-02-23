#!/bin/bash

CodeDir=/shared/iPATH/nowcast_module_v1
DataDir=/data/iPATH/nowcast_module_v1

# create output folders for cron logs
mkdir -p $DataDir/cron/{Background,CME,Flare,DailyReport,DailyStagingCleanup}

# create output folders for simulations
mkdir -p $DataDir/{Background,CME,Flare}

# create staging and archive areas
mkdir -p $DataDir/{staging,archive}/{iswa,sep_scoreboard}

# copy spacecraft and planet positions
cp -r $CodeDir/helioweb $DataDir/

# create processed CME and Flare lists
echo "[]" >$DataDir/CME/past.json
echo "[]" >$DataDir/Flare/past.json

# install crontab file
crontab crontab
