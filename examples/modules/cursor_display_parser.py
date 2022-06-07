# update cursor position every tick
vel = (joystick_axis[0, 0] * vel_scale, joystick_axis[0, 1] * vel_scale)
pos = [pos[0] + vel[0], pos[1] + vel[1]]

# push cursor position to screen every refresh_rate
if not pNumTicks[0] % refresh_rate:

    cir1.set_pos(pos)

    screen.fill(black)
    sprites.draw(screen)
    pygame.display.flip()
