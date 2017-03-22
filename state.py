'''
Created on 8 Mar 2014

@author: Daniel
'''

class State:
    is_connected = False

    last_session_num = -1
    last_session_state = -1
    my_car_idx = -1
    cam_car_idx = -1

    cur_session_time = -1
    cur_session_state_time = -1
    pre_session_time = 0
    cur_session_type = None
    
    has_race_been_won = False
    drivers_on_lead_lap = 0
    
    event_type = None
    track_length = -1
    first_sector_pct = -1
    session_laps = -1
    session_time = -1

    rpm_min = -1
    rpm_max = -1
    rpm_len = 10

    drivers = {}
    results_positions = []

    speed_calc_data = []

    last_time_update_lap_ses_time = -1

    last_time_update_drivers = -1

    last_time_update_positions = -1
    cur_dist_pct = 0
    last_dist_pct = 0

    last_time_update_standing = -1
    
    def raceTime(self):
        return self.cur_session_time - self.cur_session_state_time