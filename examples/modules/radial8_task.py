# update cursor

vel = ( int(joystick_axis[0] * cursor_vel_scale) , int(joystick_axis[1] * cursor_vel_scale) )
pos_cursor[:] = [ pos_cursor[0] + vel[0] , pos_cursor[1] + vel[1] ]


# update task state
if task_state == task_states['begin'] :

    counter_begin += 1

    if counter_begin >= time_begin :
        task_state = task_states['active']
        counter_begin = 0
        pos_target[:] = new_target()
    
elif task_state == task_states['active'] :

    if cursor_on_target(pos_cursor, pos_target, acceptance_window) :
        task_state = task_states['hold']
        counter_hold += 1

elif task_state == task_states['hold'] :

    if not cursor_on_target(pos_cursor, pos_target, acceptance_window) :
        task_state = task_states['active']
        counter_hold = 0

    else:
        counter_hold += 1

        if counter_hold >= time_hold :
            task_state = task_states['success']
            counter_hold = 0

elif task_state == task_states['fail'] :

    counter_fail += 1

    if counter_fail >= time_fail :
        task_state = task_states['end']
        counter_fail = 0

elif task_state == task_states['end'] :

    counter_end += 1

    if counter_end >= time_end :
        task_state = task_states['begin']
        counter_end = 0
