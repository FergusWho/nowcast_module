#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1

usage() {
   echo "$0 usage:" && grep "[[:space:]].)\ #" $0 \
   | sed 's/#//' \
   | sed -r 's/([a-z])\)/-\1/'
   exit 0
}

while getopts ':hf:t:' flag; do
   case $flag in
      f) # <from>: select only dates after <from>. Same format as date -d<from>. Default: 2023/01/01
         From=${OPTARG};;
      t) # <to>: select only dates till <to>. Same format as date -d<to>. Default: now
         To=${OPTARG};;
      h) # Show help
         usage;;
   esac
done

MinDate=$(date -ud"${From:-20230101}" +%s)
MaxDate=$(date -ud"${To:-now}" +%s)
Lines=$(tput lines)

echo "Network statistics between $(date -ud@$MinDate +'%F %T') and $(date -ud@$MaxDate +'%F %T')"
echo

find $DataDir/cron/NetworkCheck/ -type f \
| xargs awk -vMinDate=$MinDate -vMaxDate=$MaxDate '
   NF > 3 {
      uts = mktime(gensub(/[-:]/, " ", "g", $1" "$2))
      ute = mktime(gensub(/[-:]/, " ", "g", $4" "$5))
      if (ute >= MinDate && uts <= MaxDate) {
         printf "%s %s %s %d\n", $1, $2, $3, ute-uts
      }
   }' \
| cut -d' ' -f1,3 \
| sort -V \
| uniq -c \
| awk -vLines=$Lines '
   BEGIN {
      BLACK     = "\033[30m"
      RED       = "\033[31m"
      GREEN     = "\033[32m"
      YELLOW    = "\033[33m"
      BLUE      = "\033[34m"
      MAGENTA   = "\033[35m"
      CYAN      = "\033[36m"
      WHITE     = "\033[37m"
      B_BLACK   = "\033[1;30m"
      B_RED     = "\033[1;31m"
      B_GREEN   = "\033[1;32m"
      B_YELLOW  = "\033[1;33m"
      B_BLUE    = "\033[1;34m"
      B_MAGENTA = "\033[1;35m"
      B_CYAN    = "\033[1;36m"
      B_WHITE   = "\033[1;37m"
      RESET     = "\033[0m"
   }

   {
      n = $1
      day = $2
      status = $3
      statuses[status]
      hist[day,status] = n
      num[day] += n
   }

   END {
      PROCINFO["sorted_in"] = "@ind_str_asc"
      maxlen = 0
      for (st in statuses) {
         len = length(st)
         if (len > maxlen) maxlen = len
      }

      printf "%sDay       ", B_WHITE
      for (st in statuses) printf " %*s", maxlen, st
      printf "%s\n", RESET

      il = 0
      for (day in num) {
         if (++il % Lines == Lines-1) {
            printf "%sDay       ", B_WHITE
            for (st in statuses) printf " %*s", maxlen, st
            printf "%s\n", RESET
         }

         if (hist[day,"OK"] == num[day]) color = B_GREEN
         else if (hist[day,"OK"] < num[day]/2) color = B_RED
         else color = B_YELLOW
         printf "%s%s%s", color, day, RESET

         for (st in statuses) {
            n = hist[day,st]/num[day]*1e2
            color = RESET
            if (st != "OK") {
               if (n >= 10) color = B_RED
               else if (n >= 1) color = B_MAGENTA
               else if (n > 0) color = B_YELLOW
            } else if (st == "OK") {
               if (n < 100) color = RED
               else color = GREEN
            }
            printf " %s%*.1f%%%s", color, maxlen-1, n, RESET
         }
         printf "\n"
      }

      printf "%sDay       ", B_WHITE
      for (st in statuses) printf " %*s", maxlen, st
      printf "%s\n", RESET
   }'
