if not pNumTicks[0] % refresh_rate:

#    sprite_cursor.set_pos( np.round(pos_cursor[:]).astype('int16') )
#    sprite_target.set_pos( np.round(pos_target[:]).astype('int16') ) # would be better to check if pos_target has changed

    sprite_cursor.set_pos( pos_cursor[0])
    sprite_target.set_pos( pos_target[0])

    screen.fill(black)
    sprites.draw(screen)
    pygame.display.flip()
