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
    "TS_FILE": "/var/tmp/log_analyzer.ts"
}


def parse_cmdline():
    """
    Fun parce command line
    :return str(/path_to_config_file) or exit
    """
    parser = argparse.ArgumentParser()
    """
    5.https: // github.com / savsher / DZ1 / blob / master / log_analyzer.py  
    # L35 - есть атрибут default
    """
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
        """
        6. https: // github.com / savsher / DZ1 / blob / master / log_analyzer.py  
        # L49 - вот это все можно циклом заменить. Или распарсить в словарь и сделать update
        """
        conf_local = copy.deepcopy(config)
        conf_local.update(dict(read_conf.items('GLOBAL')))
        return conf_local
"""
#11. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
#L94 - почему эта функция ищет лог, а потом еще ищет отчет для нее? 
а если я хочу у вас импортировать одно без другого, то что делать? 
а если протестировать нужно только определенный функционал?
"""
"""
Вопрос не совсем понятен, особенно последние 2 его части
Данная функция проверяет, нужно ли повторно запускать тест.
для этого она должна знать "последний лог файл" и  есть ли "репорт" с такой же датой
На основании этих данных она либо прерывет работу, либо возвращает название файлов(перечисленных выше)
 необходимых для работы
"""
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
    """
    8. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
    #L102 - ну и что? вы можете сами ее создать
    """
    if not os.path.isdir(conf['REPORT_DIR']):
        try:
            os.mkdir(conf['REPORT_DIR'])
        except OSError as err:
            logging.error('Cant create directory: $s', conf['REPORT_DIR'])
            logging.error(err)
            sys.exit(1)

    http_log_time = 19700000
    http_log_file = None
    for path, dirlist, filelist in os.walk(conf['LOG_DIR']):
        for name in fnmatch.filter(filelist, 'nginx-access-ui.log-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*'):
            """
            9. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
            #L110 - это упадет на имени "nginx-access-ui.log-" . Не тестировали.
            """
            x = int(name.split('.')[1].split('-')[1])
            if http_log_time < x:
                http_log_time = x
                http_log_file = name
    if http_log_file is not None:
        http_log_file = os.path.join(conf['LOG_DIR'], http_log_file)
        report_file = os.path.join(conf['REPORT_DIR'],
            'report-' + time.strftime('%Y.%m.%d', time.strptime(str(http_log_time), '%Y%m%d')) + '.html')
        # check
        """
        10. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
        #L121 - их надо сверять не по mtime. Есть однозначное соответствие лога и отчета, 
        если для лога есть отчета - значит все ок, работа сделана.
        16. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
        #L244 - если отчет уже был посчитан ранее все равно нужно тс-файл обновить.
        """
        if os.path.isfile(report_file):
            logging.info('Report already exists : %s ', report_file)
            try:
                with open(conf['TS_FILE'], 'wt') as f:
                    f.write(str(time.time()))
            except EnvironmentError as err:
                logging.exception(err)
                sys.exit(1)
            logging.info('Script stop %s', sys.argv[0])
            sys.exit(0)
        return {'log': http_log_file, 'report': report_file}
    else:
        logging.info('No log file to grep ...')
        logging.info('Script stop %s', sys.argv[0])
        sys.exit(0)


def grep_file(filed):
    """
    Fun grep source log and create dic()
    filed : file descriptor
    :return dic()
    """
    # dict( url:[count, time_sum, time_min, time_max])
    grep_data = defaultdict(list)
    # save file-modification in str format
    search_tmpl = re.compile('[GET|POST] .* HTTP')
    """
    # 13. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
    #L134 - (1) давайте эта функция будет возвращать генератор (2) если не получилось распарсить, например, 90% строк,
     то это беда. Надо задаться порогом (относительным) ошибок парсинга и если он превышен - писать в лог и выходить
    """
    """
    (1) пункт не понял зачем
    (2) реализована проверка корректности парсинга, но сделано это относительно текущей строки файла, а не всего файла
    проверка начинается после набра некоторой статистики ( begin_from )
    """
    pattern_lines = 0
    trigger = 0.90
    begin_from = 1000
    try:
        for total_lines, line in enumerate(filed):
            request = search_tmpl.search(line)
            if request is not None:
                pattern_lines += 1
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
            if total_lines > begin_from and float(total_lines - pattern_lines)/total_lines > trigger:
                logging.exception('Exceeded trashhold "BAD LINKS" : %s', trigger)
                grep_data.clear()
                break
    except IOError as err:
        logging.error(err)
        sys.exit(1)
    else:
        return grep_data


def create_report(grep_data, reportf, conf):
    """
    Fun generate report file : report-YYYY.MM.DD.html
    grep_data :  dir()
    reportf : str(report filename
    conf: config)
     """
    precise = 7
    result_data = list()
    """
    14. https: // github.com / savsher / DZ1 / blob / master / log_analyzer.py  
    # L177 - давайте сократим количество проходов по grep_data до минимума, 
    щас многовато как-то
    """
    total_req = 0
    total_time = 0
    for x in grep_data:
        total_req += grep_data[x][0]
        total_time += grep_data[x][1]
    result_data = list()
    for k, v in sorted(grep_data.items(), key=lambda x: x[1][1], reverse=True)[0:int(conf['REPORT_SIZE'])]:
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
    """
    15. https: // github.com / savsher / DZ1 / blob / master / log_analyzer.py  
    # L196 - сделайте read(),   safe_substitute и все, не надо усложнять так.
    """
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


def main(myvar):
    """"""

    files = check_run(myvar)
    logging.info('Grep http log %s', sys.argv[0])

    """
    12. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
    #L233 - это можно без дупликации кода написать
    """
    if files['log'].endswith('.gz'):
        f = gzip.open(files['log'], 'rb')
    else:
        f = open(files['log'], 'rt')
    grep_data = grep_file(f)
    f.close()
    if not grep_data:
        logging.error('Script are stopped : %s', sys.argv[0])
        sys.exit(0)

    logging.info('Create report file %s', files['report'])
    create_report(grep_data, files['report'], myvar)
    try:
        with open(config['TS_FILE'], 'wt') as f:
            f.write(str(time.time()))
    except EnvironmentError as err:
        logging.exception(err)
        sys.exit(1)

if __name__ == "__main__":

    config_file = parse_cmdline()
    config_new = read_config(config_file)
    """
    #3. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
    #L215 - filename принимает None
    """
    """
     Не понял смысл, данного коментария
     если переменная оказалась в словаре , то она уже не может быть None, иначе она не распарсится
     или имелось ввиду что-то другое
    """
    if 'LOG_FILE' in config_new:
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname).1s %(message)s',
            datefmt='%Y.%m.%d %H:%M:%S',
            filename=config_new['LOG_FILE']
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname).1s %(message)s',
            datefmt='%Y.%m.%d %H:%M:%S'
        )

    logging.info('Start script: %s', sys.argv[0])
    """
    2. https://github.com/savsher/DZ1/blob/master/log_analyzer.py
    #L255 - в случае неожиданной ошибки все упадет, а вы и не узнаете, если в консоль не смотреть постоянно. Добавьте логирование таких ошибок.
    """
    try:
        main(config_new)
    except RuntimeError as err:
        logging.error(err)
    else:
        logging.info('Stop script success ...: %s', sys.argv[0])
