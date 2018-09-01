# constants
# currently implemented as internals, but will be exposed as constants infrastructure later

task_states = {
        'begin'     : 1,
        'active'    : 2,
        'hold'      : 3,
        'success'   : 4,
        'fail'      : 5,
        'end'       : 6 }

black = [0, 0, 0]
green = [0, 255, 0]
red   = [255, 0, 0]
blue  = [0, 0, 255]
white = [255, 255, 255]
light_blue = [150, 200, 255]

# internals

task_state = 1
counter_hold = 0
counter_begin = 0
counter_fail = 0
counter_end = 0
counter_duration = 0

pos_cursor_i = [100, 100]
pos_target_i = [50, 50]
size_cursor_i = int(20)
size_target_i = int(50)
color_cursor_i = white
color_target_i = green

def is_cursor_on_target(cursor, target, window) :
    return ( (cursor[0] - target[0])**2 + (cursor[1] - target[1])**2 )**(0.5) <= window

def gen_new_target() :

    pos_max = 1000

    return [ int(np.random.rand() * pos_max), int(np.random.rand() * pos_max) ]


# PARAMS
# currently implemented as internals, but will be exposed as part of parameters framework

time_hold = 500
time_duration = 4000

time_fail = 1000
time_begin = 5
time_end = 10

acceptance_window = 100

cursor_vel_scale = 1
