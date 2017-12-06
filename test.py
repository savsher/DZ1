import re
import string
import time
import os
import sys
import logging
import errno
import ConfigParser


def main():

    read_conf = ConfigParser.ConfigParser()
    try:
        read_conf.read('test.conf')
    except ConfigParser.Error as err:
        print err
    else:
        try:
            x = read_conf.get['GLOBAL', 'LOG_FILE']
        except ConfigParser.Error as err:





if __name__ == '__main__':
    main()




