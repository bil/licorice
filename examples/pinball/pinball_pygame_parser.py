joystick_strs = [f"{x:.2f}" for x in joystick_axis]
text_surface = screen_font.render(",".join(joystick_strs), False, (255, 255, 255))

if pygame.event.peek(eventtype=pygame.QUIT):
    pygame.quit()
    handle_exit(0)

if pNumTicks[0] == 0:
    # need to set size & color again on first tick because they were empty when the constructor ran

    sprite_cursor.set_size(size_cursor[0])
    sprite_target.set_size(size_target[0])

    sprite_cursor.set_color(color_cursor)
    sprite_target.set_color(color_target)

if not pNumTicks[0] % refresh_rate:
    sprite_cursor.set_pos(pos_cursor)
    sprite_target.set_pos(pos_target)

    sprite_cursor.set_color(color_cursor)
    sprite_target.set_color(color_target)

    screen.fill(black)
    sprites.draw(screen)
    screen.blit(text_surface, (0, 0))
    pygame.display.flip()
