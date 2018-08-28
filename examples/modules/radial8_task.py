# update cursor

vel = ( int(joystick_axis[0] * cursor_vel_scale) , int(joystick_axis[1] * cursor_vel_scale) )
pos_cursor[:] = [ pos_cursor[0] + vel[0] , pos_cursor[1] + vel[1] ]

cursor_on_target = False


# update task state
if task_state == task_states['begin'] :

    counter_begin += 1

    if counter_begin >= time_begin :
        task_state = task_states['active']
        counter_begin = 0
        pos_target[:] = gen_new_target()
    
elif task_state == task_states['active'] :

    cursor_on_target = is_cursor_on_target(pos_cursor, pos_target, acceptance_window)

    if cursor_on_target :

        task_state = task_states['hold']
        counter_hold += 1

    else:

        counter_duration += 1

        if counter_duration >= time_duration :
            task_state = task_states['fail']
            counter_duration = 0

elif task_state == task_states['hold'] :

    cursor_on_target = is_cursor_on_target(pos_cursor, pos_target, acceptance_window)

    if not cursor_on_target :
        task_state = task_states['active']
        counter_hold = 0

    else:

        counter_hold += 1

        if counter_hold >= time_hold :
            task_state = task_states['success']
            counter_hold = 0

elif task_state == task_states['success'] :

    task_state = task_states['end']
    counter_end += 1

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


if not pNumTicks[0] % 15 :
    print(task_state, counter_duration, cursor_on_target, pos_target[:], counter_hold)
