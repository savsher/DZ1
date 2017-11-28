#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import fnmatch
import gzip
import re
import json
from collections import defaultdict
import string
import time

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

def grep_line():
    pass

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
    # save file-modification in str format
    file_time = ''

    def grep_line(line):
        SEARCH_TMPL =  'GET .* HTTP'
        request = re.search(SEARCH_TMPL, line)
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


    for path, dirlist, filelist in os.walk(config["LOG_DIR"]):
        for name in fnmatch.filter(filelist, "nginx-access-ui.log-*"):
            if mtime < os.stat(os.path.join(path, name)).st_mtime:
                xfile = os.path.join(path, name)
                mtime = os.stat(os.path.join(path, name )).st_mtime

    if xfile is None:
        raise 'File no found!!!'

    file_time = time.strftime('%Y.%m.%d', time.localtime(mtime))

    if xfile.endswith('.gz'):
        with gzip.open(xfile, 'rt') as f:
            for line in f:
                grep_line(line)
    else:
        with open(xfile, 'rt') as f:
            for line in f:
                grep_line(line)

    result_data = list()
    for k,v in sorted(grep_data.items(), key=lambda x: x[1][1], reverse=True)[0:config["REPORT_SIZE"]]:
        tmpdir = {'url':k }
        tmpdir['count'] = v[0]
        tmpdir['count_perc'] = round(float(v[0]/total_req), 9)
        tmpdir['time_avg'] = round(float(v[1]/v[0]), 7)
        tmpdir['time_max'] = v[3]
        tmpdir['time_med'] = round(float((v[3]-v[2])/2), 7)
        tmpdir['time_perc'] = round(float(v[1]/total_time), 7)
        tmpdir['time_sum'] = round(v[1], 7)
        result_data.append(tmpdir)

    #  Rendering template
    with open(os.path.join(config['REPORT_DIR'], 'report.html'), 'rt') as fread:
        with open(os.path.join(config['REPORT_DIR'], 'report-' + file_time + '.html'), 'wt') as fwrite:

            for line in fread:
                test = re.search('var table = \$table_json', line)
                if test is not None:
                    fwrite.write(string.Template(line).substitute(table_json=result_data))
                else:
                    fwrite.write(line)

if __name__ == "__main__":
    main()