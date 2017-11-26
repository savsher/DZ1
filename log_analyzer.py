#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import fnmatch
import gzip
import re
import json
from collections import defaultdict

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

def main():
    # initial variables
    mtime = 0
    xfile = None
    log_data = list()
    log_data.append({'url': 'test1', 'count': 100, 'time_sum': 99})
    log_data.append({'url': 'test2', 'count': 700, 'time_sum': 39})
    grep_data = defaultdict(list)
    total_req = 0
    total_time = 0
    COUNT = slice(0,0)
    TIME = slice(1,1)
    MIN = slice(2,2)
    MAX = slice(3,3)

    for path, dirlist, filelist in os.walk(config["LOG_DIR"]):
        for name in fnmatch.filter(filelist, "nginx-access-ui.log-*"):
            if mtime < os.stat(os.path.join(path, name)).st_mtime:
                xfile = os.path.join(path, name)
                mtime = os.stat(os.path.join(path, name )).st_mtime
    if xfile is None:
        raise 'File no found!!!'
    print xfile

    if xfile.endswith('.gz'):
        with gzip.open(xfile, 'rt') as f:
            for line in f:
                pass
    else:
        with open(xfile, 'rt') as f:
            for line in f:
                request = re.search('GET .* HTTP', line)
                if request is not None:
                    rtime = float(line.split()[-1])
                    total_req += 1
                    total_time += rtime
                    request = request.group().split()[1]
                    if request in grep_data.keys():
                        grep_data[request][0] += 1
                        grep_data[request][1] += rtime
                        if grep_data[request][2] > rtime:
                            grep_data[request][2] = rtime
                        if grep_data[request][3] < rtime:
                            grep_data[request][3] = rtime
                    else:
                        grep_data[request].append(1)
                        grep_data[request].append(rtime)
                        grep_data[request].append(rtime)
                        grep_data[request].append(rtime)
                        
        for i in log_data:
            print(json.dumps(i))





if __name__ == "__main__":
    main()