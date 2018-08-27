task_states = {
        'begin'     : 1,
        'active'    : 2,
        'hold'      : 3,
        'success'   : 4,
        'fail'      : 5,
        'end'       : 6 }

task_state = 1
counter_hold = 0
counter_begin = 0
counter_fail = 0
counter_end = 0

pos_cursor[:] = [0, 0]
pos_target[:] = [0, 0]
size_cursor[:] = int(20)
size_target[:] = int(50)
color_cursor[:] = [255, 255, 255]
color_target[:] = [0, 255, 0]

def cursor_on_target(cursor, target, window) :
    return ( (cursor[0] - target[0])**2 + (cursor[1] - target[1])**2 )**(1/2) <= window

def new_target() :

    pos_max = 1000

    return [ int(np.random.rand() * pos_max), int(np.random.rand() * pos_max) ]


# PARAMS

time_hold = 500
time_duration = 5000

time_fail = 1000
time_begin = 5
time_end = 10

acceptance_window = 100

cursor_vel_scale = 5
