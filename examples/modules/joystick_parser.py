# this parser code brings data into the licorice system

if (read_source_input) : # this is a special variable that is set to true every time that the source is triggered and ready to read data

    read_source_input = False # it MUST be set to false at the end of the parser code

    pygame.event.pump()

    joystick_axis_out[0] = usb_joystick.get_axis(0)

else: # if the source is not triggered on this tick (in the case that the prior tick's reading of data is taking longer than a tick), do nothing

    pause()
    continue
