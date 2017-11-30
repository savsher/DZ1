#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import os.path
import fnmatch
import gzip
import re
from collections import defaultdict
import string
import time
<<<<<<< HEAD
import argparse
import configparser
=======
import sys
import argparse
>>>>>>> f3d3a243130a2611fef57d4e1209a2d997dd5bd7

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
    # save file-modification in str format
    file_time = ''

    def grep_cmdline():
        parser = argparse.ArgumentParser()
<<<<<<< HEAD
        parser.add_argument('--config', dest='config', action='store', help='Config File')
        args = parser.parse_args()
        # check file exists
        if args.config is not None:
            if os.path.isfile(args.config):
                return args.config
        return '/usr/local/etc/log_analyzer.conf'

    def read_config(file):
        read_conf = configparser.ConfigParser()
        read_conf.read(file)
        tmp = config.get('', 'REPORT_SIZE')
        #config['REPORT_DIR'] = config.get('GLOBAL', 'REPORT_DIR')
        #config['LOG_DIR'] = config.get('GLOBAL', 'LOG_DIR')
        print tmp
=======
        parser.add_argument('--config', action='test')
        for i in sys.argv[1:]:
            print i

>>>>>>> f3d3a243130a2611fef57d4e1209a2d997dd5bd7


    def grep_file(filed):
        # dict( url:[count, time_sum, time_min, time_max])
        grep_data = defaultdict(list)
        COUNT = 0
        TIME_SUM = 1
        TIME_MIN = 2
        TIME_MAX = 3
        # save file-modification in str format
        search_tmpl = re.compile('[GET|POST] .* HTTP')
        for line in filed:
            request = search_tmpl.search(line)
            if request is not None:
                rtime = float(line.split()[-1])
                request = request.group().split()[1]
                if request in grep_data.keys():
                    grep_data[request][COUNT] += 1
                    grep_data[request][TIME_SUM] += rtime
                    if grep_data[request][TIME_MIN] > rtime:
                        grep_data[request][TIME_MIN] = rtime
                    if grep_data[request][TIME_MAX] < rtime:
                        grep_data[request][TIME_MAX] = rtime
                else:
                    grep_data[request].append(1)
                    grep_data[request].append(rtime)
                    grep_data[request].append(rtime)
                    grep_data[request].append(rtime)
        return grep_data

    config_file = grep_cmdline()

    read_config(config_file)

    for path, dirlist, filelist in os.walk(config["LOG_DIR"]):
        for name in fnmatch.filter(filelist, "nginx-access-ui.log-*"):
            if mtime < os.stat(os.path.join(path, name)).st_mtime:
                xfile = os.path.join(path, name)
                mtime = os.stat(os.path.join(path, name )).st_mtime

    if xfile is None:
        raise 'File no found!!!'

    file_time = time.strftime('%Y.%m.%d', time.localtime(mtime))

    if xfile.endswith('.gz'):
        with gzip.open(xfile, 'rb') as f:
            grep_data = grep_file(f)
    else:
        with open(xfile, 'rt') as f:
            grep_data = grep_file(f)

    # Create templete for html file
    if grep_data:
        precise = 7
        result_data = list()
        total_req = sum([grep_data[x][0] for x in grep_data])
        #print(total_req)
        total_time = sum([grep_data[x][1] for x in grep_data])
        #print(total_time)
        result_data = list()
        for k,v in sorted(grep_data.items(), key=lambda x: x[1][1], reverse=True)[0:config["REPORT_SIZE"]]:
            tmpdir = {'url':k }
            tmpdir['count'] = v[0]
            tmpdir['count_perc'] = round(float(v[0])/total_req, precise)
            tmpdir['time_avg'] = round(float(v[1])/v[0], precise)
            tmpdir['time_max'] = round(v[3], precise)
            tmpdir['time_med'] = round(float(v[3]-v[2])/2, precise)
            tmpdir['time_perc'] = round(float(v[1])/total_time, precise)
            tmpdir['time_sum'] = round(v[1], precise)
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
    #print(result_data[0:2])

if __name__ == "__main__":
    main()