# this parser code brings data into the licorice system

if (read_source_input) : # this is a special variable that is set to true every time that the source is triggered and ready to read data

    read_source_input = False # it MUST be set to false at the end of the parser code

    pygame.event.pump()

    ax0 = usb_joystick.get_axis(0)
    ax1 = usb_joystick.get_axis(1)

    buttons = [ usb_joystick.get_button(i) for i in range(joystick_buttons.shape[1]) ]

    joystick_axis[0, 0] = ax0
    joystick_axis[0, 1] = ax1

    joystick_buttons[0, :] = buttons

else: # if the source is not triggered on this tick (in the case that the prior tick's reading of data is taking longer than a tick), do nothing

    pause()
    continue
