#!/bin/sh
set -e

mkdir -p lists
cd lists

wget https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts -O 01_steven_unified
wget https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/porn/hosts -O 02_steven_unified_porn
wget https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/social/hosts -O 03_steven_unified_social
wget https://block.energized.pro/extensions/social/formats/hosts -O 04_energized_extension_social
wget https://block.energized.pro/bluGo/formats/hosts -O 05_energized_blu_go
wget https://block.energized.pro/spark/formats/hosts -O 06_energized_spark
wget https://block.energized.pro/extensions/xtreme/formats/hosts -O 07_energized_extension_xtreme
wget https://raw.githubusercontent.com/jerryn70/GoodbyeAds/master/Hosts/GoodbyeAds.txt -O 08_goodbye_ads
wget https://winhelp2002.mvps.org/hosts.zip -O /tmp/mvps_hosts.zip && unzip -p /tmp/mvps_hosts.zip HOSTS > 09_mvps && rm -f /tmp/mvps_hosts.zip
wget https://adaway.org/hosts.txt -O 10_adaway
wget https://raw.githubusercontent.com/StevenBlack/hosts/master/data/someonewhocares.org/hosts -O 11_dan_pollocks
wget 'https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts;showintro=0' -O 12_peter_lowe
wget https://zerodot1.gitlab.io/CoinBlockerLists/hosts -O 13_coin_blocker
wget https://ewpratten.retrylife.ca/youtube_ad_blocklist/hosts.ipv4.txt -O 14_youtube_ads
