*******************************************************************************
LiCoRICE Tutorial
*******************************************************************************

Welcome to LiCoRICE! This tutorial is intended for new users to LiCoRICE and provides guided examples in increasing difficulty to get you started with writing and running your own models.


0-5: Prerequisites
===============================================================================

If you're here, we assume that you've completed the :ref:`quickstart guide <guide/quickstart:LiCoRICE Quickstart>`.


6: User Input via Joystick
===============================================================================

Now we will create a simple game, known as the pinball task, that utilizes a joystick input.

First we will begin reading in the joystick input, then we will graphically display that input using Pygame and finally we will implement the game.


Setup
-------------------------------------------------------------------------------

As in the quickstart, we assume you are using the ``~/licorice`` directory as your workspace by setting the ``LICORICE_WORKING_PATH`` environment variable.

Ensure you have a controller or joystick:

    Any USB controller should work, but the one we used when making this tutorial is the `Logitech F310 Wired Gamepad Controller <https://www.amazon.com/dp/B003VAHYQY>`_ with the toggle set to XInput mode (X) on the back.

Install Pygame in your virtualenv where LiCoRICE is installed:

.. code-block:: bash

    pip install pygame


Specify the model
-------------------------------------------------------------------------------

Create the model file:

.. code-block:: bash

    touch $LICORICE_WORKING_PATH/tutorial-6.yaml

Open the created file add the following:

.. code-block:: yaml

   config:
      num_ticks: 200
      tick_len: 10000

    signals:
      joystick_axis:
        shape: 2
        dtype: double

      joystick_buttons:
        shape: 11 # set this to the number of buttons to extract from the joystick
        dtype: uint8

    modules:
      joystick_out:
        language: python
        constructor: True
        parser: True
        in:
          name: jdev
          args:
            type: usb_input
          schema:
            data:
              dtype: uint8
              size: 22
        out:
          - joystick_axis
          - joystick_buttons

      joystick_print:
        language: python
        in:
          - joystick_axis
          - joystick_buttons

This specifies two LiCoRICE models, first ``joystick_out`` which reads in the incoming data from the joystick and then ``joystick_print`` which outputs joystick positional data and button clicks.
It also specifies two signals, which track the joystick's current axis and the activity of any buttons on the joystick.

Be sure to specify ``joystick_buttons`` to match your joystick's specific inputs if you are using a non-Logitech F310 controller.


Generate joystick modules
-------------------------------------------------------------------------------

.. code-block:: bash

    licorice generate tutorial-6 -y

This should generate a few files: ``$LICORICE_WORKING_PATH/joystick_print.py``, ``$LICORICE_WORKING_PATH/joystick_out_parser.py`` and ``$LICORICE_WORKING_PATH/joystick_out_constructor.py``.


Write joystick modules
-------------------------------------------------------------------------------

Open the constructor (``$LICORICE_WORKING_PATH/joystick_out_constructor.py``) and add the following:

.. code-block:: python

    import pygame

    pygame.display.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() < 1:
        die('No joystick found!\n')

    usb_joystick = pygame.joystick.Joystick(0)
    usb_joystick.init()


The constructor will initialize pygame's built-in `joystick <https://www.pygame.org/docs/ref/joystick.html>`_ and `display <https://www.pygame.org/docs/ref/display.html>`_ tooling and creates a ``Joystick`` object for connecting to and reading from our joystick.

Then open the parser (``$LICORICE_WORKING_PATH/joystick_out_parser.py``) and add the following:

.. code-block:: python

    pygame.event.pump()

    ax0 = usb_joystick.get_axis(0)
    ax1 = usb_joystick.get_axis(1)

    buttons = [ usb_joystick.get_button(i) for i in range(usb_joystick.get_numbuttons()) ]

    joystick_axis[0] = ax0
    joystick_axis[1] = ax1

    joystick_buttons[:] = buttons[:]


The parser will continuously read in axis and button data from the joystick object and update the values in our signals accordingly.

Now open the print module (``$LICORICE_WORKING_PATH/joystick_print.py``) and add the following:

.. code-block:: python

    if not pNumTicks[0] % 10:  # pNumTicks[0] is the tick counter
        print("X: ", joystick_axis[0], "\nY: ", joystick_axis[1], "\nButtons: ", *joystick_buttons, "\n\n", flush=True)


Similar to the quickstart walkthrough, we print both our joystick position and any button presses.


Run LiCoRICE
-------------------------------------------------------------------------------

In general, only one command (``go``) needs to be issued to :ref:`parse <api/cli:Parse>`, :ref:`compile <api/cli:Compile>`, and :ref:`run <api/cli:Run>` a model, but these commands can also be issued individually if need be:

.. code-block:: bash

    licorice go tutorial-6 -y

If everything worked, you should see the controller analog stick and button states among the output in your terminal in the following format:

.. code-block:: bash

    X: ...
    Y: ...
    Buttons: ...

    X: ...
    Y: ...
    Buttons: ...

    ...

Now we will be utilizing pygame to display the joystick data in a graphical window outside of the terminal.


Specify pygame module in the model
-------------------------------------------------------------------------------

Open ``$LICORICE_WORKING_PATH/tutorial-6.yaml`` and add this under modules:

.. code-block:: yaml

  pygame_display:
    language: python
    constructor: true
    parser: true            # most "user code" will live here for a sink
    destructor: true
    in:
      - joystick_axis
    out:
      name: viz
      args:
        type: vis_pygame    # sink type for pygame


Here we are specifying a module that will generate a visual pygame output.


Generate pygame modules
-------------------------------------------------------------------------------

.. code-block:: bash

    licorice generate tutorial-6 -y

This should generate a few new files: ``$LICORICE_WORKING_PATH/pygame_display_parser.py``, ``$LICORICE_WORKING_PATH/pygame_display_destructor.py`` and ``$LICORICE_WORKING_PATH/pygame_display_constructor.py``.


Write pygame modules
-------------------------------------------------------------------------------
Open the constructor (``$LICORICE_WORKING_PATH/pygame_display_constructor.py``) and add the following:

.. code-block:: python

    import math
    import pygame

    pygame.display.init()


    class Circle(pygame.sprite.Sprite):
        def __init__(self, color, radius, pos):
            pygame.sprite.Sprite.__init__(self)
            self.radius = radius
            self.color = color

            self.image = pygame.Surface([radius * 2, radius * 2]).convert_alpha()
            self.draw()

            self.rect = self.image.get_rect()
            self.rect.x, self.rect.y = pos

        def set_color(self, color):
            self.color = color
            self.draw()

        def get_pos(self):
            return (self.rect.x, self.rect.y)

        def set_pos(self, pos):
            self.rect.x, self.rect.y = pos

        def set_size(self, radius):
            cur_pos = self.rect.x, self.rect.y
            self.radius = radius
            self.image = pygame.Surface(
                [self.radius * 2, self.radius * 2]
            ).convert_alpha()
            self.rect = self.image.get_rect()
            self.rect.x, self.rect.y = cur_pos
            self.draw()

        def draw(self):
            self.image.fill((0, 0, 0, 0))
            pygame.draw.circle(
                self.image, self.color, (self.radius, self.radius), self.radius
            )


    black = (0, 0, 0)
    screen_width = 1280
    screen_height = 1024
    screen = pygame.display.set_mode((screen_width, screen_height))
    screen.fill(black)

    # used in both pygame_demo and cursor_track
    color = [200, 200, 0]
    pos = [0, 0]
    circle_size = 30

    # these variables only used for pygame demo
    r = 200
    theta = 0
    offset = [500, 500]

    vel_scale = 10

    cir1 = Circle(color, circle_size, pos)

    sprites = pygame.sprite.Group(cir1)

    refresh_rate = 2  # ticks (10 ms)

The constructor defines the circle we will be using as the cursor and initializes it in the pygame display.

Then open the parser (``$LICORICE_WORKING_PATH/pygame_display_parser.py``) and add the following:

.. code-block:: python

    if pygame.event.peek(eventtype=pygame.QUIT):
        pygame.quit()
        handle_exit(0)

    # update cursor position every tick
    vel = (joystick_axis[0] * vel_scale, joystick_axis[1] * vel_scale)
    pos = [pos[0] + vel[0], pos[1] + vel[1]]

    # push cursor position to screen every refresh_rate
    if not pNumTicks[0] % refresh_rate:
        pos[0] = np.clip(pos[0], 0, screen_width - 2 * circle_size)
        pos[1] = np.clip(pos[1], 0, screen_height - 2 * circle_size)
        cir1.set_pos(pos)

    screen.fill(black)
    sprites.draw(screen)
    pygame.display.flip()

Finally, open the destructor (``$LICORICE_WORKING_PATH/pygame_display_destructor.py``) and add the single line:

.. code-block:: python

    pygame.quit()

Run LiCoRICE
-------------------------------------------------------------------------------

Now, run LiCoRICE again:

.. code-block:: bash

    licorice go tutorial-6 -y

And you should see the same output in the terminal as before, but now you should also see a window in which a circle cursor moves with your movement of the joystick

7: Jitter demo
===============================================================================

Coming soon.

8: Audio line in/out
===============================================================================

Coming soon.

9: Serial port
===============================================================================

Coming soon.

10: Ethernet
===============================================================================

Coming soon.

11 Asynchronous modules
===============================================================================

Coming soon.

12: GPU
===============================================================================

Coming soon.
