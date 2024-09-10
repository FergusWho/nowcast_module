#!/bin/bash

check_ip() {
   ping -q -c1 -w1 $1 &>/dev/null && return 0 || return 1
}

printf "%s " $(date -u +'%F %T')

# commonly used DNS IPs:
#    Google (primary, secondary)
#    OpenDNS (primary, secondary)
#    Cloudflare (primary, secondary)
#    Level3 (1 to 6)
ips=(
   8.8.8.8 8.8.4.4
   208.67.222.222 208.67.220.220
   1.1.1.1 1.0.0.1
   4.2.2.1 4.2.2.2 4.2.2.3 4.2.2.4 4.2.2.5 4.2.2.6
)
(( nbads = 0 ))
for ip in ${ips[@]}; do
   check_ip $ip && break || (( ++nbads ))
done
if (( nbads == ${#ips[@]} )); then
   echo NETWORK_DOWN
   exit
fi

if ! check_ip iswa.gsfc.nasa.gov; then
   echo ISWA_DOWN
   exit
fi

hapi_status=$(curl --connect-timeout 2 -s https://iswa.gsfc.nasa.gov/IswaSystemWebApp/hapi/capabilities |
   jq -r '.status.message' 2>/dev/null)
if [[ $hapi_status != OK ]]; then
   echo ISWA_HAPI_DOWN
   exit
fi

if ! check_ip kauai.ccmc.gsfc.nasa.gov; then
   echo KAUAI_DOWN
   exit
fi

donki_status=$(curl --connect-timeout 2 -s -o /dev/null -w "%{http_code}" https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis?startDate=$(date -u +%F))
if [[ $donki_status != 200 ]]; then
   echo DONKI_DOWN
   exit
fi

echo OK
