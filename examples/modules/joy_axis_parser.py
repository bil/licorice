# this parser code brings data into the licorice system

if (read_source_input) : # this is a special variable that is set to true every time that the source is triggered and ready to read data

    read_source_input = False # it MUST be set to false at the end of the parser code

    pygame.event.pump()

    ax1 = usb_joystick.get_axis(0)
    ax2 = usb_joystick.get_axis(1)

    # this first dimension holds history (values of prior ticks), it shouldn't be exposed to the user at this stage, will be changed soon
    joystick_axis_out[0, 0] = ax1
    joystick_axis_out[0, 1] = ax2

else: # if the source is not triggered on this tick (in the case that the prior tick's reading of data is taking longer than a tick), do nothing

    pause()
    continue
