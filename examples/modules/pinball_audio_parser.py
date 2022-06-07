if (state_task[0, 0] == task_states["success"]) and (
    state_prev != task_states["success"]
):
    sound_success.play()

elif (state_task[0, 0] == task_states["fail"]) and (
    state_prev != task_states["fail"]
):
    sound_fail.play()

state_prev = state_task[0, 0]
