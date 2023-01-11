if pygame.event.peek(eventtype=pygame.QUIT):
    pygame.quit()
    handle_exit(0)

# update cursor position every tick
# take mean of joystick_axis to support async input
ja = joystick_axis
if len(ja.shape) > 1:
    ja = np.mean(ja, axis=0)

vel = (ja[0] * vel_scale, ja[1] * vel_scale)
pos = [pos[0] + vel[0], pos[1] + vel[1]]

# push cursor position to screen every refresh_rate
if not pNumTicks[0] % refresh_rate:
    pos[0] = np.clip(pos[0], 0, screen_width - 2 * circle_size)
    pos[1] = np.clip(pos[1], 0, screen_height - 2 * circle_size)
    cir1.set_pos(pos)

screen.fill(black)
sprites.draw(screen)
pygame.display.flip()
