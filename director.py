'''
Created on 21 Feb 2014

@author: Daniel
'''
import argparse
import logging, logging.handlers
import irsdk
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow)
from controls import ControlsWindow
import sys
import ctypes

VERSION = ''

def main():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='output verbosity', action='count', default=2)
    parser.add_argument('-s', '--silent', help='turn off display log', action='store_true', default=False)
    parser.add_argument('-V', '--version', action='version', version='iRacing Text Overlay %s' % VERSION, help='show version and exit')
    parser.add_argument('--test', help='use test file as irsdk mmap')
    parser.add_argument('--dump', help='dump irsdk mmap to file')
    args = parser.parse_args()

    logging_handlers = [logging.handlers.RotatingFileHandler('log', maxBytes=1 * 1024 * 1024, encoding='utf-8')]
    if not args.silent:
        logging_handlers.append(logging.StreamHandler())

    logging.basicConfig(format='{asctime} {levelname:>8}: {message}', datefmt='%Y-%m-%d %H:%M:%S', style='{',
        handlers=logging_handlers, level=[logging.WARN, logging.INFO, logging.DEBUG][min(args.verbose - 1, 2)])

    logging.info('iRacing Text Overlay %s' % VERSION)

    ir = irsdk.IRSDK()
    ir.startup(test_file=args.test, dump_to=args.dump)

    try:
        if args.test:
            main()
        else:
            while not ir.is_connected:
                pass
            
            app = QApplication([])
            controlsWindow = ControlsWindow(ir)
            timer = QtCore.QTimer();
            timer.timeout.connect(main)
            timer.start(1/30);
            sys.exit(app.exec_())
    

    except KeyboardInterrupt:
        pass
    except:
        logging.exception('')