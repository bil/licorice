# update cursor

vel = ( joystick_axis[0] * cursor_vel_scale , joystick_axis[1] * cursor_vel_scale )
pos_cursor_i = [ pos_cursor_i[0] + vel[0] , pos_cursor_i[1] + vel[1] ]

cursor_on_target = False


# update task state
if task_state == task_states['begin'] :

    counter_begin += 1

    if counter_begin >= time_begin :
        task_state = task_states['active']
        counter_begin = 0
        pos_target_i = gen_new_target()
        color_target_i = green

    
elif task_state == task_states['active'] :

    cursor_on_target = is_cursor_on_target(pos_cursor, pos_target, acceptance_window)

    if cursor_on_target :

        task_state = task_states['hold']
        counter_hold += 1
        color_target_i = light_blue

    else:

        counter_duration += 1

        if counter_duration >= time_duration :
            task_state = task_states['fail']
            counter_duration = 0
            color_target_i = red

elif task_state == task_states['hold'] :

    cursor_on_target = is_cursor_on_target(pos_cursor, pos_target, acceptance_window)

    if not cursor_on_target :
        task_state = task_states['active']
        counter_hold = 0
        color_target_i = green

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

    counter_hold = 0
    counter_begin = 0
    counter_fail = 0
    counter_duration = 0

    counter_end += 1

    if counter_end >= time_end :
        task_state = task_states['begin']
        counter_end = 0


# write output signals
pos_cursor[:] = pos_cursor_i
pos_target[:] = pos_target_i
size_cursor[:] = size_cursor_i
size_target[:] = size_target_i
color_cursor[:] = color_cursor_i
color_target[:] = color_target_i
