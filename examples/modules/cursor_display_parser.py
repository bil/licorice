if not pNumTicks[0] % refresh_rate:


    pos_cur = cir1.get_pos()

    vel_scale = 10

    # this is broken indexing, slicing should be simpler than this, signal code is not slicing out the history dimension
    vel = ( int(joystick_axis_out[0,0] * vel_scale) , int(joystick_axis_out[0,1] * vel_scale) )

    pos_new = ( pos_cur[0] + vel[0], pos_cur[1] + vel[1] )
    
    cir1.set_pos(pos_new)

    screen.fill(black)
    sprites.draw(screen)
    pygame.display.flip()
