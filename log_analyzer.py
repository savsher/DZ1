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
import ConfigParser
import sys
import logging
import copy


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "TS_FILE": "/var/tmp/log_analyzer.ts",
    "TRIGGER": 0.9
}


def parse_cmdline():
    """
    Fun parce command line
    :return str(/path_to_config_file) or exit
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config', action='store', help='Config File',
                        default='/usr/local/etc/log_analyzer.conf')
    args = parser.parse_args()
    # check file exists
    if os.path.isfile(args.config):
            return args.config
    else:
        print 'Cant start without config file ...'
        sys.exit(1)


def read_config(file):
    """
    Fun parce config file
    file : str(/path_to_config)
    """
    read_conf = ConfigParser.ConfigParser()
    read_conf.optionxform = str
    try:
        read_conf.read(file)
    except ConfigParser.Error as err:
        print err
        print('Failed to read config file!!!')
        sys.exit(1)
    else:
        conf_local = copy.deepcopy(config)
        conf_local.update(dict(read_conf.items('GLOBAL')))
        return conf_local


def time_stamp(path):
    try:
        with open(path, 'wt') as f:
            f.write(str(time.time()))
    except EnvironmentError as err:
        logging.exception(err)
        sys.exit(1)

def check_report_file(conf, http_log_time):
    """
    Check the report file existence
    if not return file name
    """
    report_file = os.path.join(
        conf['REPORT_DIR'],
        'report-' + time.strftime('%Y.%m.%d',time.strptime(str(http_log_time),'%Y%m%d')) + '.html')
    if os.path.isfile(report_file):
        logging.info('Report already exists : %s ', report_file)
        time_stamp(conf['TS_FILE'])
        logging.info('Script stop %s', sys.argv[0])
        sys.exit(0)
    return report_file


def check_run(conf):
    """
    Fun test existence of report-YYYY.MM.DD.html and if True
    continue else exit
    """
    if not os.path.isdir(conf['LOG_DIR']):
        logging.error('Not exists : %s ', conf['LOG_DIR'])
        sys.exit(1)
    if not os.path.isfile('report.html'):
        logging.error('Not exists : report.html')
        sys.exit(1)
    if not os.path.isdir(conf['REPORT_DIR']):
        try:
            os.mkdir(conf['REPORT_DIR'])
        except OSError as err:
            logging.exception(err)
            sys.exit(1)

    http_log_time = 19700000
    http_log_file = None
    for path, dirlist, filelist in os.walk(conf['LOG_DIR']):
        for name in filelist:
            x = re.findall('nginx-access-ui.log-(\d{8})[.gz]?', name)
            if http_log_time < int(x[0]):
                http_log_time = int(x[0])
                http_log_file = name
        break # depth tree 1
    if http_log_file is not None:
        http_log_file = os.path.join(conf['LOG_DIR'], http_log_file)
        report_file = check_report_file(conf, http_log_time)
        return {'log': http_log_file, 'report': report_file}
    else:
        logging.info('No log file to grep ...')
        logging.info('Script stop %s', sys.argv[0])
        sys.exit(0)


def grep_file(filed, trigger):
    """
    Fun grep source log and create dic()
    filed : file descriptor
    :return dic()
    """
    # dict( url:[count, time_sum, time_min, time_max])
    request_data = defaultdict(list)
    URL_COUNT = 0
    URL_TIME_SUM = 1
    URL_TIME_MIN = 2
    URL_TIME_MAX = 3
    # save file-modification in str format
    search_tmpl = re.compile('[GET|POST] .* HTTP')
    pattern_lines = 0
    trigger = trigger
    try:
        for total_lines, line in enumerate(filed):
            request = search_tmpl.search(line)
            if request is not None:
                pattern_lines += 1
                rtime = float(line.split()[-1])
                request = request.group().split()[1]
                if request in request_data.keys():
                    request_data[request][URL_COUNT] += 1
                    request_data[request][URL_TIME_SUM] += rtime
                    if request_data[request][URL_TIME_MIN] > rtime:
                        request_data[request][URL_TIME_MIN] = rtime
                    if request_data[request][URL_TIME_MAX] < rtime:
                        request_data[request][URL_TIME_MAX] = rtime
                else:
                    request_data[request].append(1)
                    request_data[request].append(rtime)
                    request_data[request].append(rtime)
                    request_data[request].append(rtime)
            if float(total_lines + 1 - pattern_lines)/(total_lines + 1) > trigger:
                logging.exception('Exceeded trashhold "BAD LINKS" : %s', trigger)
                request_data.clear()
                break
    except IOError as err:
        logging.error(err)
        sys.exit(1)
    else:
        return request_data


def create_report(request_data, reportf, conf):
    """
    Fun generate report file : report-YYYY.MM.DD.html
    grep_data :  dir()
    reportf : str(report filename
    conf: config)
     """
    URL_COUNT = 0
    URL_TIME_SUM = 1
    URL_TIME_MIN = 2
    URL_TIME_MAX = 3
    precise = 7
    result_data = list()
    total_req = 0
    total_time = 0
    for x in request_data:
        total_req += request_data[x][URL_COUNT]
        total_time += request_data[x][URL_TIME_SUM]
    result_data = list()
    for k, v in sorted(request_data.items(), key=lambda x: x[1][URL_TIME_SUM], reverse=True)[0:int(conf['REPORT_SIZE'])]:
        tmpdir = {'url': k}
        tmpdir['count'] = v[URL_COUNT]
        tmpdir['count_perc'] = round(float(v[URL_COUNT]) / total_req, precise)
        tmpdir['time_avg'] = round(float(v[URL_TIME_SUM]) / v[URL_COUNT], precise)
        tmpdir['time_max'] = round(v[URL_TIME_MAX], precise)
        tmpdir['time_med'] = round(float(v[URL_TIME_MAX] - v[URL_TIME_MIN]) / 2, precise)
        tmpdir['time_perc'] = round(float(v[URL_TIME_SUM]) / total_time, precise)
        tmpdir['time_sum'] = round(v[URL_TIME_SUM], precise)
        result_data.append(tmpdir)
    # Rendering template
    try:
        with open('report.html', 'rt') as fread:
            with open(reportf, 'wt') as fwrite:
                text = fread.read()
                text = string.Template(text).safe_substitute(table_json=result_data)
                fwrite.write(text)
    except IOError as err:
        logging.exception('Cant create file: %s', reportf)
        logging.error(err)
        sys.exit(1)


def main(config_new):
    """"""

    files = check_run(config_new)
    logging.info('Grep http log %s', sys.argv[0])

    if files['log'].endswith('.gz'):
        f = gzip.open(files['log'], 'rb')
    else:
        f = open(files['log'], 'rt')
    grep_data = grep_file(f, config_new["TRIGGER"])
    f.close()
    if not grep_data:
        logging.error('Script are stopped : %s', sys.argv[0])
        sys.exit(0)

    logging.info('Create report file %s', files['report'])
    create_report(grep_data, files['report'], config_new)
    time_stamp(config_new['TS_FILE'])


if __name__ == "__main__":

    config_file = parse_cmdline()
    config_new = read_config(config_file)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
        filename=config_new.get('LOG_FILE'))

    logging.info('Start script: %s', sys.argv[0])
    try:
        main(config_new)
    except Exception as err:
        logging.error(err)
    else:
        logging.info('Stop script success ...: %s', sys.argv[0])
