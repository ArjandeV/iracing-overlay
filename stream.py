#!python3

import sys
import shutil
import re
from state import State
import time
import math
import logging, logging.handlers
import argparse
import json
import irsdk
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow)
from controls import ControlsWindow
import ctypes
import pprint

VERSION = '1.0.1'

LICENSE_CLASSES = ['R', 'D', 'C', 'B', 'A', 'P', 'WC']




def on_session_change():
    if ir['DriverInfo']:
        state.my_car_idx = ir['DriverInfo']['DriverCarIdx']
        state.rpm_min = ir['DriverInfo']['DriverCarSLFirstRPM'] * 2/3
        state.rpm_max = ir['DriverInfo']['DriverCarRedLine']
    else:
        state.my_car_idx = state.rpm_min = state.rpm_max = -1

    if ir['WeekendInfo']:
        state.track_length = float(ir['WeekendInfo']['TrackLength'].split()[0])
    else:
        state.track_length = -1

    if ir['SessionInfo']:
        state.session_laps = ir['SessionInfo']['Sessions'][state.last_session_num]['SessionLaps']
        session_time = ir['SessionInfo']['Sessions'][state.last_session_num]['SessionTime']
        state.session_time = -1 if session_time == 'unlimited' else float(session_time.split()[0])
        state.cur_session_type = ir['SessionInfo']['Sessions'][state.last_session_num]['SessionType']
    else:
        state.session_laps = state.session_time = -1
        state.cur_session_type = None

    if ir['WeekendInfo'] and ir['DriverInfo']:
        state.event_type = ir['WeekendInfo']['EventType']
    else:
        state.event_type = None

    if ir['SplitTimeInfo']:
        state.first_sector_pct = ir['SplitTimeInfo']['Sectors'][1]['SectorStartPct']
    else:
        state.first_sector_pct = -1

    state.drivers = {}
    state.last_time_update_drivers = -1
    on_cam_change()

def on_cam_change():
    print(ir['CamCameraNumber'])
    state.last_time_update_lap_ses_time = -1
    state.last_time_update_positions = -1
    state.last_time_update_standing = -1
    state.cur_dist_pct = 0
    state.last_dist_pct = 0
    state.speed_calc_data = []

def update_speed_rpm():
    #if ir['CarIdxTrackSurface'][state.cam_car_idx] == irsdk.TrkLoc.NOT_IN_WORLD \
    #    or (ir['IsReplayPlaying'] and ir['ReplayFrameNumEnd'] > 10):
    #    return

    if state.my_car_idx == state.cam_car_idx:
        speed = ir['Speed']
        rpm = ir['RPM']
        gear = ir['Gear']
        fuel = ir['FuelLevel']
    else:
        speed = None
        rpm = ir['CarIdxRPM'][state.cam_car_idx]
        gear = ir['CarIdxGear'][state.cam_car_idx]
        fuel = None

    if not rpm is None:
        low = .3
        high = 1 - low
        if rpm >= state.rpm_min:
            rpm = low + high * (rpm - state.rpm_min) / (state.rpm_max - state.rpm_min)
        else:
            rpm = low * rpm / state.rpm_min
        rpm = max(0, min(rpm, 1))
        vert_line = settings['rpm_speed']['vertical_line']
        blocks = settings['rpm_speed']['blocks']
        rpm = vert_line + (
                blocks[-1] * math.ceil(rpm * state.rpm_len - 1) +
                blocks[round(rpm % (1 / state.rpm_len) * state.rpm_len * (len(blocks) - 1))]
            ).ljust(state.rpm_len) + vert_line

    if not gear is None:
        gear = 'R' if gear == -1 else 'N' if gear == 0 else gear

    if speed is None:
        speed = 0
        if len(state.speed_calc_data) > 1:
            diff_pct = state.speed_calc_data[-1][0] - state.speed_calc_data[0][0]
            if diff_pct < 0: diff_pct += 1
            diff_time = max(0, state.speed_calc_data[-1][1] - state.speed_calc_data[0][1])
            if diff_pct > 0 and diff_time > 0:
                speed = max(0, state.track_length * diff_pct / diff_time * 1000)
                if speed > 110:
                    speed = 0
    speed = '{:3.0f}km/h'.format(speed * 3.6)

    fuel = '' if fuel is None else 'Fuel: {:.3f}l'.format(fuel)

    result ='{}{}{}  {}'.format(speed, rpm, gear, fuel)
    logging.debug(result)

def update_lap_ses_time():
    if state.last_time_update_lap_ses_time > 0 and state.cur_session_time - state.last_time_update_lap_ses_time < .5:
        return
    state.last_time_update_lap_ses_time = state.cur_session_time

    lap_num =  ir['CarIdxLap'][state.cam_car_idx]
    session_time = 0
    
    if lap_num is 0:
        state.pre_session_time = state.cur_session_time or 0
    else:
        session_time = state.cur_session_time - state.pre_session_time

#     session_type = state.cur_session_type or 'Session Time'
#     session_time = state.cur_session_time or 0

#     if state.my_car_idx == state.cam_car_idx:
#         lap_num =  ir['Lap']
#     else:
#         lap_num =  ir['CarIdxLap'][state.cam_car_idx]
        
    lap_num =  ir['CarIdxLap'][state.cam_car_idx]

    if not session_time is None:
        m, s = divmod(int(session_time), 60)
        h, m = divmod(m, 60)
        session_time = '{}:{:02}:{:02}'.format(h, m, s) if h else '{}:{:02}'.format(m, s)
        if state.session_time != -1:
            h, m = divmod(int(state.session_time / 60), 60)
            session_time += '/{}h{:02}m'.format(h, m) if h else '/{}m'.format(m)

#     if not lap_num is None and not state.session_laps is None:
#         if lap_num < 1 or (ir['IsReplayPlaying'] and ir['ReplayFrameNumEnd'] > 10):
# #             lap = ''
#             lap = 'Lap: {}/{}'.format(lap, state.session_laps)
#         elif type(state.session_laps) is int and state.session_laps > 0:
#             lap = 'Lap: {}/{}'.format(lap, state.session_laps)
#         else:
#             lap = 'Lap: %d' % lap

    lap = '{}/{}'.format(lap_num, state.session_laps)

    result = 'T{} - L{}'.format(session_time, lap)
    logging.debug(result)

def update_drivers():
    if state.last_time_update_drivers > 0 and state.cur_session_time - state.last_time_update_drivers < 1:
        return
    state.last_time_update_drivers = state.cur_session_time

    if ir['DriverInfo']:
        for d in ir['DriverInfo']['Drivers']:
            if d['IsSpectator'] or d['UserID'] == -1: continue
            car_idx = d['CarIdx']
            if not car_idx in state.drivers:
                state.drivers[car_idx] = dict(
                    license_class = LICENSE_CLASSES[int(d['LicLevel'] / 5)],
                    safety_rating = '{:.2f}'.format(d['LicSubLevel'] / 100),
                    class_position = 0,
                    completed_race = False,
                    lap = 1)
            state.drivers[car_idx]['driver_info'] = d

    if ir['SessionInfo']:
        state.results_positions = ir['SessionInfo']['Sessions'][state.last_session_num]['ResultsPositions']
        if state.results_positions:
            if state.event_type == 'Race':
                state.race_time = ir['SessionInfo']['Sessions'][state.last_session_num]['ResultsAverageLapTime'] * state.session_laps
                state.drivers_on_lead_lap = len([p for p in state.results_positions if p['Lap'] == 0])
            for pos in state.results_positions:
                car_idx = pos['CarIdx']
                if car_idx in state.drivers:
                    state.drivers[car_idx]['position_info'] = pos
                    state.drivers[car_idx]['class_position'] = pos['ClassPosition'] + 1

    if ir['QualifyResultsInfo']:
        qual_positions = ir['QualifyResultsInfo']['Results']
        if qual_positions:
            for pos in qual_positions:
                car_idx = pos['CarIdx']
                if car_idx in state.drivers:
                    state.drivers[car_idx]['qual_info'] = pos


def sort_by_lap_distance(diff):
    if diff < -.5:
        return diff + 1
    elif diff > .5:
        return diff - 1
    return diff

def update_position():
    if state.last_time_update_positions > 0 and state.cur_session_time - state.last_time_update_positions < 1:
        return
    state.last_time_update_positions = state.cur_session_time

#     if state.cam_car_idx in state.drivers and ir['CarIdxTrackSurface'][state.cam_car_idx] != -1:
    for car_idx, (lap, pct, trk_loc) in enumerate(zip(ir['CarIdxLap'], ir['CarIdxLapDistPct'], ir['CarIdxTrackSurface'])):
        if not car_idx in state.drivers: continue
        d = state.drivers[car_idx]
        if lap == 1 and not 'has_crossed_start_line' in d:
            if pct < 0.5:
                d['has_crossed_start_line'] = True
            else:
                lap = 0
                
        #pprint(vars(irsdk))
        #if trk_loc == irsdk.TrkLoc.ON_TRACK or trk_loc == irsdk.TrkLoc.OFF_TRACK: # only update overall distance if not pitting
        #    d['overall_distance'] = lap + pct
        #d['lap_distance'] = pct
        #d['track_location'] = trk_loc
        
        # driver has crossed finish line
        if state.event_type == 'Race' and d['lap'] != lap: 
            # first driver finishes race
            if not state.has_race_been_won and lap > state.session_laps:
                d['completed_race'] = True
                state.has_race_been_won = True
            elif state.has_race_been_won:
                if not d['completed_race']:
                    d['completed_race'] = True
            else:
                d['lap'] = lap



def main():
    global state

    if state.is_connected and (not ir.is_initialized or not ir.is_connected):
        state.is_connected = False
        ir.shutdown()
        logging.info('IRSDK disconnected')
        state = State()
    elif not state.is_connected and (ir.is_initialized or ir.is_connected or ir.startup()):
        state.is_connected = True
        logging.info('IRSDK connected')

    if not state.is_connected:
#         time.sleep(2)
        controlsWindow.overlayWindow.update()
        return

    state.cur_session_time = ir['SessionTime']
    if state.cur_session_state_time == -1 and ir['CarIdxLap'][1] == 1:
        state.cur_session_state_time = state.cur_session_time

    # session changed
    if state.last_session_num != ir['SessionNum'] or \
        state.last_session_state != ir['SessionState'] or \
        state.rpm_min == -1 or state.rpm_max == -1 or \
        state.track_length == -1 or \
        state.first_sector_pct == -1 or \
        not state.cur_session_type:

        state.last_session_num = ir['SessionNum']
        state.last_session_state = ir['SessionState']
        try:
            on_session_change()
        except:
            state.last_session_num = -1
            logging.exception('error in on session change')

    # cam changed
    if state.cam_car_idx != ir['CamCarIdx']:
        state.cam_car_idx = ir['CamCarIdx']
        try:
            on_cam_change()
        except:
            state.cam_car_idx = -1
            logging.exception('error in on cam change')

    state.last_dist_pct = state.cur_dist_pct
    state.cur_dist_pct = ir['CarIdxLapDistPct'][state.cam_car_idx]
    state.speed_calc_data.append((state.cur_dist_pct, state.cur_session_time))
    state.speed_calc_data = state.speed_calc_data[-10:]

    update_speed_rpm()
    update_lap_ses_time()
    update_drivers()
    update_position()
    
    controlsWindow.overlayWindow.update()

def patch_irsdk():
    def get_hwnd(self):
        if not self.__hwnd:
            EnumWindows = ctypes.windll.user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
            GetWindowText = ctypes.windll.user32.GetWindowTextW
            GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
            IsWindowVisible = ctypes.windll.user32.IsWindowVisible
            handles = []
            def foreach_window(hwnd, lParam):
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLength(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buff, length + 1)
                    if buff.value == 'iRacing.com Simulator':
                        handles.append(hwnd)
                return True
            EnumWindows(EnumWindowsProc(foreach_window), 0)
            if len(handles) > 0:
                self.__hwnd = handles[0]
        return self.__hwnd
    
    def _broadcast_msg(self, broadcast_type=0, var1=0, var2=0, var3=0):
        return ctypes.windll.user32.SendNotifyMessageW(self.get_hwnd(), self._broadcast_msg_id,
            broadcast_type | var1 << 16, var2 | var3 << 16)
    
    irsdk.IRSDK.__hwnd = None
    irsdk.IRSDK.get_hwnd = get_hwnd
    irsdk.IRSDK._broadcast_msg = _broadcast_msg

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

    settings = None
    try:
        settings = json.loads(re.sub(r'^\s*\/\/.*', '', open('settings.json', 'r', encoding='utf-8').read(), flags=re.M))
    except FileNotFoundError:
        shutil.copy('settings.tmpl', 'settings.json')
        logging.info('Settings file created')
        sys.exit(0)

    if settings:
        logging.info('Settings file loaded')
    else:
        logging.fatal('No settings file')
        sys.exit(0)

    patch_irsdk()
    ir = irsdk.IRSDK()
    ir.startup(test_file=args.test, dump_to=args.dump)
#     if not ir.is_connected:
#         sys.exit(0)

    if args.dump:
        sys.exit(0)

    state = State()

    try:
        if args.test or args.dump:
            main()
        else:
            app = QApplication([])
            controlsWindow = ControlsWindow(ir, state)
            timer = QtCore.QTimer();
            timer.timeout.connect(main)
            timer.start(1/60);
            sys.exit(app.exec_())
    

    except KeyboardInterrupt:
        pass
    except:
        logging.exception('')
