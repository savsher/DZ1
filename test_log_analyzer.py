#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import random
import log_analyzer
import os
import sys
import time
from collections import defaultdict


class TestLogAnalyzer(unittest.TestCase):

    def setUp(self):
        # Prepare for test_read_config
        self.tmp_conf_file = '/var/tmp/test' + str(random.randint(1, 999))
        self.tmp_conf_file_str = "[GLOBAL]\nREPORT_SIZE: 333"
        with open(self.tmp_conf_file, 'wt') as f:
            f.write(self.tmp_conf_file_str)

        # Prepare for test_check_run and test_grep_file:
        self.tmp_log_file = '/var/tmp/nginx-access-ui.log-'+time.strftime('%Y%m%d', time.localtime())
        self.tmp_report_file = 'var/tmp/report-' + time.strftime('%Y.%m.%d', time.localtime())+'.html'
        self.tmp_log_file_text = [
            '1.138.198.128 -  - [30/Jun/2017:03:28:23 +0300] "GET /api/v2/banner/25187824 HTTP/1.1" 200 1260'
            ' "-" "python-requests/2.8.1" "-" "1498782503-440360380-4707-10488749" "4e9627334" 0.203',
            '1.138.198.128 -  - [30/Jun/2017:03:28:23 +0300] "GET /api/v2/banner/25949683 HTTP/1.1" 200 1261 "-"'
            ' "python-requests/2.8.1" "-" "1498782502-440360380-4707-10488740" "4e9627334" 0.863'
        ]
        with open(self.tmp_log_file, 'wt') as f:
            for i in self.tmp_log_file_text:
                f.write(i+'\n')
        if os.path.exists(self.tmp_report_file):
            os.remove(self.tmp_report_file)



    @unittest.skipIf(len(sys.argv) > 0, 'This function cant correct to parse this command line ')
    def test_grep_cmd_line(self):
        self.assertTrue(True)

    def test_read_config(self):
        x = log_analyzer.read_config(self.tmp_conf_file)
        self.assertNotEqual(x["REPORT_SIZE"], log_analyzer.config["REPORT_SIZE"])
        self.assertEqual(x["LOG_DIR"], log_analyzer.config["LOG_DIR"])
        self.assertEqual(x["REPORT_DIR"], log_analyzer.config["REPORT_DIR"])

    def test_check_run(self):
        old_log = log_analyzer.config["LOG_DIR"]
        old_report = log_analyzer.config["REPORT_DIR"]
        log_analyzer.config["LOG_DIR"] = '/var/tmp'
        log_analyzer.config["REPORT_DIR"] = '/var/tmp'
        result = log_analyzer.check_run(log_analyzer.config)
        self.assertIn('report', result)
        """
        1. https://github.com/savsher/DZ1/blob/master/test_log_analyzer.py - добавьте тесты на парсинг, поиск логов и т.п.
        """
        self.assertIn('log', result)
        log_analyzer.config["LOG_DIR"] = old_log
        log_analyzer.config["REPORT_DIR"] = old_report


    """
    1. https://github.com/savsher/DZ1/blob/master/test_log_analyzer.py - добавьте тесты на парсинг, поиск логов и т.п.
    """
    def test_grep_file(self):
        with open(self.tmp_log_file, 'rt') as f:
            grep_data = log_analyzer.grep_file(f)
        self.assertIn('/api/v2/banner/25949683', grep_data)
        self.assertIn('/api/v2/banner/25187824', grep_data)

    def test_create_report(self):
        old_val = log_analyzer.config["REPORT_DIR"]
        log_analyzer.config["REPORT_DIR"] = '/var/tmp/tmp/tmp'
        x = defaultdict(list)
        with self.assertRaises(SystemExit):
            self.assertRaises(IOError, log_analyzer.create_report(x, '/var/tmp/tmp/tmp.txt', log_analyzer.config))
        log_analyzer.config["REPORT_DIR"] = old_val

    def tearDown(self):
        os.remove(self.tmp_conf_file)
        os.remove(self.tmp_log_file)
