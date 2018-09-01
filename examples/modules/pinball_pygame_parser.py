if pNumTicks[0] == 0 :
# need to set size & color again on first tick because they were empty when the constructor ran

    sprite_cursor.set_size(size_cursor[0])
    sprite_target.set_size(size_target[0])

    sprite_cursor.set_color(color_cursor[0, :])
    sprite_target.set_color(color_target[0, :])

if not pNumTicks[0] % refresh_rate:

    sprite_cursor.set_pos( pos_cursor[0, :])
    sprite_target.set_pos( pos_target[0, :])

    sprite_cursor.set_color( color_cursor[0, :])
    sprite_target.set_color( color_target[0, :])

    screen.fill(black)
    sprites.draw(screen)
    pygame.display.flip()
