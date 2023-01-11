if pygame.event.peek(eventtype=pygame.QUIT):
    pygame.quit()
    handle_exit(0)

if not pNumTicks[0] % refresh_rate:

    theta += math.pi / 64

    pos = (
        r * math.cos(theta) + offset[0],
        r * math.sin(2 * theta) + offset[1],
    )
    cir1.set_pos(pos)

    screen.fill(black)
    sprites.draw(screen)
    pygame.display.flip()
