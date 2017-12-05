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
        self.tmp_conf_file = '/var/tmp/test'+ str(random.randint(1,999))
        self.tmp_conf_file_str = "[GLOBAL]\nREPORT_SIZE: 333\nREPORT_DIR: ./reports\n" \
                                 "LOG_DIR: ./log\nTS_FILE: /var/tmp/log_analyzer.ts"
        with open(self.tmp_conf_file,'wt') as f:
            f.write(self.tmp_conf_file_str)

        # Prepare for test_check_run
        self.tmp_log_file = '/var/tmp/nginx-access-ui.log-'+time.strftime('%Y%m%d', time.localtime())
        self.tmp_report_file = 'var/tmp/report-' + time.strftime('%Y.%m.%d', time.localtime())+'.html'
        self.tmp_log_file_str = 'test'
        with open(self.tmp_log_file, 'wt') as f:
            f.write(self.tmp_log_file_str)
        if os.path.exists(self.tmp_report_file):
            os.remove(self.tmp_report_file)


    @unittest.skipIf(len(sys.argv)> 0, 'This function cant correct to parse this command line ')
    def test_grep_cmd_line(self):
        pass


    def test_read_config(self):
        log_analyzer.read_config(self.tmp_conf_file)
        self.assertEqual(333, log_analyzer.config["REPORT_SIZE"])
        self.assertEqual('./log', log_analyzer.config["LOG_DIR"])
        self.assertEqual('./reports', log_analyzer.config["REPORT_DIR"])


    def test_check_run(self):
        old_log = log_analyzer.config["LOG_DIR"]
        old_report = log_analyzer.config["REPORT_DIR"]
        log_analyzer.config["LOG_DIR"]= '/var/tmp'
        log_analyzer.config["REPORT_DIR"] = '/var/tmp'
        result = log_analyzer.check_run()
        self.assertIn( 'report', result)
        self.assertIn( 'log', result)
        log_analyzer.config["LOG_DIR"] = old_log
        log_analyzer.config["REPORT_DIR"] = old_report

    @unittest.skip('Always skipped')
    def test_grep_file(self):
        f = open(self.tmp_grep_file, 'rt')
        with self.assertRaises(IOError, log_analyzer.grep_file(), f):
            print 'asdfasdfasdf'


    def test_create_report(self):
        old_val = log_analyzer.config["REPORT_DIR"]
        log_analyzer.config["REPORT_DIR"] = '/var/tmp/tmp/tmp'
        x = defaultdict(list)
        with self.assertRaises(SystemExit):
            self.assertRaises(IOError, log_analyzer.create_report(x, '/var/tmp/tmp/tmp.txt'))
        log_analyzer.config["REPORT_DIR"] = old_val


    def tearDown(self):
        os.remove(self.tmp_conf_file)
        os.remove(self.tmp_log_file)
