#!/usr/bin/env python
# -*- coding: utf-8 -*-

import log_analyzer

import unittest

class TestLogAnalyzer(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test(self):
        a= 'a'
        b= 'a'
        self.assertEqual(a,b)