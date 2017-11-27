#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import fnmatch
import gzip
import re
import json
from collections import defaultdict, OrderedDict

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
    # dict( url:[count, time_sum, time_min, time_max])
    grep_data = defaultdict(list)
    # summary_requests
    total_req = 0
    # summary_time
    total_time = 0

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

    result_data = list()
    for k,v in sorted(grep_data.items(), key=lambda x: x[1][1], reverse=True)[0:config["REPORT_SIZE"]]:
        tmpdir = {'url':k }
        tmpdir['count'] = v[0]
        tmpdir['count_perc'] = v[0]/total_req
        tmpdir['time_avg'] = v[1]/v[0]
        tmpdir['time_max'] = v[3]
        tmpdir['time_med'] = (v[3]-v[2])/2
        tmpdir['time_perc'] = v[1]/total_time
        tmpdir['time_sum'] = v[1]
        result_data.append(tmpdir)
    print result_data[0:1]
    #http://jinja.pocoo.org/docs/dev/templates/#


if __name__ == "__main__":
    main()