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
import argparse
import configparser
import sys
import logging

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "TS_FILE": "/var/tmp/log_analyzer.ts"
    #"LOG_FILE": "/usr/loca/etc/log_analyzer.conf"
}

def grep_cmdline():
    """ """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config', action='store', help='Config File')
    args = parser.parse_args()
    # check file exists
    default_config_file = '/usr/local/etc/log_analyzer.conf'
    if args.config is not None:
        if os.path.isfile(args.config):
            return args.config
    else:
        if os.path.isfile(default_config_file):
            return default_config_file
    return None

def read_config(file):
    """ """
    if file is not None:
        read_conf = configparser.ConfigParser()
        try:
            read_conf.read(file)
            report_size = read_conf.getint('GLOBAL', 'REPORT_SIZE')
            report_dir = read_conf.get('GLOBAL', 'REPORT_DIR')
            log_dir = read_conf.get('GLOBAL', 'LOG_DIR')
            ts_file = read_conf.get('GLOBAL', 'TS_FILE')
        except Exception as err:
            print err
        else:
            config["REPORT_SIZE"] = report_size
            config['REPORT_DIR'] = report_dir
            config['LOG_DIR'] = log_dir
            config['TS_FILE']  = ts_file
            try:
                log_file = read_conf.get('GLOBAL', 'LOG_FILE')
            except Exception as err:
                print err
            else:
                config['LOG_FILE'] = log_file

def check_run():
    """ """
    if not os.path.isdir(config['LOG_DIR']):
        logging.error('Not exists : %s ', config['LOG_DIR'])
        sys.exit(1)
    if not os.path.isdir(config['REPORT_DIR']):
        logging.error('Not exist : %s ', config['REPORT_DIR'])
        sys.exit(1)

    http_log_time = 19700101
    http_log_file = None
    for path, dirlist, filelist in os.walk(config['LOG_DIR']):
        for name in fnmatch.filter(filelist, "nginx-access-ui.log-*"):
            x = int(name.split('.')[1].split('-')[1])
            if http_log_time < x:
                http_log_time = x
                http_log_file = name
    if http_log_file is not None:
        http_log_file = os.path.join(config['LOG_DIR'], http_log_file)
        report_file = os.path.join(
            config['REPORT_DIR'],
            'report-' + time.strftime('%Y.%m.%d', time.strptime(str(http_log_time), '%Y%m%d')) + '.html')
        #check
        if os.path.isfile(report_file):
            report_file_time = os.stat(report_file).st_mtime
            http_log_time = os.stat(http_log_file).st_mtime
            if report_file_time > http_log_time:
                logging.info('Report already exists : %s ', report_file)
                sys.exit(0)
        return {'log':http_log_file, 'report':report_file}
    else:
        logging.info('No log file to grep ...')
        sys.exit(0)

def grep_file(filed):
    """ """
    # dict( url:[count, time_sum, time_min, time_max])
    grep_data = defaultdict(list)
    # save file-modification in str format
    search_tmpl = re.compile('[GET|POST] .* HTTP')
    try:
        for line in filed:
            request = search_tmpl.search(line)
            if request is not None:
                rtime = float(line.split()[-1])
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
    except IOError as err:
        logging.error(err)
        sys.exit(1)
    else:
        return grep_data

def create_report(grep_data, file):
    precise = 7
    result_data = list()
    total_req = sum([grep_data[x][0] for x in grep_data])
    # print(total_req)
    total_time = sum([grep_data[x][1] for x in grep_data])
    # print(total_time)
    result_data = list()
    for k, v in sorted(grep_data.items(), key=lambda x: x[1][1], reverse=True)[0:config["REPORT_SIZE"]]:
        tmpdir = {'url': k}
        tmpdir['count'] = v[0]
        tmpdir['count_perc'] = round(float(v[0]) / total_req, precise)
        tmpdir['time_avg'] = round(float(v[1]) / v[0], precise)
        tmpdir['time_max'] = round(v[3], precise)
        tmpdir['time_med'] = round(float(v[3] - v[2]) / 2, precise)
        tmpdir['time_perc'] = round(float(v[1]) / total_time, precise)
        tmpdir['time_sum'] = round(v[1], precise)
        result_data.append(tmpdir)
    # Rendering template
    report_tmpl = os.path.join(config['REPORT_DIR'], 'report.html')
    if not os.path.isfile(report_tmpl):
        logging.error('No template file: %', report_tmpl)
        sys.exit(1)
    with open(os.path.join(config['REPORT_DIR'], 'report.html'), 'rt') as fread:
        with open(os.path.join(file), 'wt') as fwrite:
            try:
                for line in fread:
                    test = re.search('var table = \$table_json', line)
                    if test is not None:
                        fwrite.write(string.Template(line).substitute(table_json=result_data))
                    else:
                        fwrite.write(line)
            except IOError as err:
                logging.error(err)
                sys.exit(1)

def main():
    """"""
    config_file = grep_cmdline()
    read_config(config_file)

    if 'LOG_FILE' in config:
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname).1s %(message)s',
            datefmt='%Y.%m.%d %H:%M:%S',
            filename=config['LOG_FILE']
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname).1s %(message)s',
            datefmt='%Y.%m.%d %H:%M:%S'
        )

    logging.info('Start script: %s', sys.argv[0])
    files = check_run()
    logging.info('Grep http log %s', sys.argv[0])

    if files['log'].endswith('.gz'):
        with gzip.open(files['log'],'rb') as f:
            grep_data = grep_file(f)
    else:
        with open(files['log'], 'rt') as f:
            grep_data = grep_file(f)

    logging.info('Create report file %s', files['report'])
    if grep_data:
        create_report(grep_data, files['report'])
        try:
            with open(config['TS_FILE'], 'wt') as f:
                f.write(str(time.time()))
        except EnvironmentError as err:
            logging.exception(err)
            sys.exit(1)
        else:
            logging.info('Stop script success ...: %s', sys.argv[0])
    else:
        logging.info('Stop script ...: %s', sys.argv[0])

if __name__ == "__main__":
    main()