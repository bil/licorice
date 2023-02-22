*******************************************************************************
LiCoRICE Tutorial
*******************************************************************************

Welcome to LiCoRICE! This tutorial is intended for new users to LiCoRICE and provides guided examples in increasing difficulty to get you started with writing and running your own models.


0-5: Prerequisites (Quickstart)
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

    Any USB controller should work, but the one we used when making this tutorial is the `Logitech F310 Wired Gamepad Controller <https://www.amazon.com/dp/B003VAHYQY>`_. Make sure that the toggle is set to XInput mode (X) on the back or you will need to alter your model file to read 12 buttons instead of 11.

Install dependencies for running a GUI and install Pygame in your virtualenv where LiCoRICE is installed:

.. code-block:: bash

    sudo apt-get install -y xinit openbox lxterminal
    pip install pygame

Then, create a file ``~/.xinitrc`` with the following contents:

.. code-block::

    openbox &
    lxterminal --geometry=1000x1000

This will allow us to use a GUI from Ubuntu server by running the ``startx`` command.


Read and print joystick input
-------------------------------------------------------------------------------

We'll start out by simply reading in the input from our controller analog stick and printing it to the console.

Specify the model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
        # set this to the number of buttons to read from the joystick
        shape: 11  # 12 for DirectInput on the Logitech F310
        dtype: uint8

    modules:
      joystick_reader:
        language: python
        parser: True
        in:
          name: joystick_raw
          args:
            type: pygame_joystick
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

This specifies two LiCoRICE models, first ``joystick_reader`` which reads in the incoming data from the joystick and then ``joystick_print`` which outputs joystick positional data and button clicks.
It also specifies two signals, which track the joystick's current axis and the activity of any buttons on the joystick.

Be sure to specify ``joystick_buttons`` to match your joystick's specific inputs if you are using a non-Logitech F310 controller.


Generate joystick modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    licorice generate tutorial-6 -y

This should generate a couple files: ``$LICORICE_WORKING_PATH/joystick_print.py`` and ``$LICORICE_WORKING_PATH/joystick_reader_parser.py``.


Write joystick modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``pygame_joystick`` driver will initialize pygame's built-in `joystick <https://www.pygame.org/docs/ref/joystick.html>`_ and `display <https://www.pygame.org/docs/ref/display.html>`_ tooling and creates a ``Joystick`` object for connecting to and reading from our joystick, so there's no need to do this in a constructor.

Then open the parser (``$LICORICE_WORKING_PATH/joystick_reader_parser.py``) and add the following:

.. code-block:: python

    pygame.event.pump()

    ax0 = pygame_joystick.get_axis(0)
    ax1 = pygame_joystick.get_axis(1)

    buttons = [ pygame_joystick.get_button(i) for i in range(pygame_joystick.get_numbuttons()) ]

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now run the ``go`` command to :ref:`parse <api/cli:Parse>`, :ref:`compile <api/cli:Compile>`, and :ref:`run <api/cli:Run>` your model. We specify the ``SDL_VIDEODRIVER`` variables so that we don't need to initialize a GUI for pygame, but we'll use a GUI in the subsequent section.

.. code-block:: bash

    SDLVIDEO_DRIVER=dummy licorice go tutorial-6 -y

If everything worked, you should see the controller analog stick and button states among the output in your terminal in the following format:

.. code-block:: bash

    X: ...
    Y: ...
    Buttons: ...

    X: ...
    Y: ...
    Buttons: ...

    ...

Visualize the input
-------------------------------------------------------------------------------

Now we will be utilizing pygame to display the joystick data in a graphical window outside of the terminal.


Specify pygame module in the model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Here we are specifying a module that will generate a visual pygame output. You may also go ahead and remove the ``num_ticks`` line so that the model runs indefinitely.


Generate pygame modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    licorice generate tutorial-6 -y

This should generate a few new files: ``$LICORICE_WORKING_PATH/pygame_display_parser.py``, ``$LICORICE_WORKING_PATH/pygame_display_destructor.py`` and ``$LICORICE_WORKING_PATH/pygame_display_constructor.py``.


Write pygame modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now, run LiCoRICE again, but this time from within an X server:

.. code-block:: bash

    startx
    # make sure to activate your virtualenv again and set any necessary environment variables
    licorice go tutorial-6 -y

And you should see the same output in the terminal as before, but now you should also see a window in which a circle cursor moves with your movement of the joystick


Add pinball logic
-------------------------------------------------------------------------------

Now we will begin using our cursor functionality to build a game commonly used in computational neuroscience experiements also known as the pinball task.


Modify module specifications in the model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open ``$LICORICE_WORKING_PATH/tutorial-6.yaml`` and change our pygame_display module definition to:

.. code-block:: yaml

    pygame_display:
      language: python
      constructor: true
      parser: true
      destructor: true
      in:
        - pos_cursor
        - pos_target
        - size_cursor
        - size_target
        - color_cursor
        - color_target
      out:
        name: viz
        args:
          type: vis_pygame    # sink type for pygame

Also change our joystick_reader module specification to:

.. code-block:: yaml

    language: python
    parser: True
    in:
      name: joystick_raw
      async: True
      args:
        type: pygame_joystick
      schema:
        max_packets_per_tick: 2
        data:
          dtype: float
          size: 8
    out:
      - joystick_axis
      - joystick_buttons

Now add a pinball_task module specification as such:

.. code-block:: yaml

    pinball_task:
      language: python
      constructor: true
      in:
        - joystick_axis
        - joystick_buttons
      out:
        - pos_cursor
        - pos_target
        - size_target
        - size_cursor
        - color_cursor
        - color_target
        - state_task

Finally make sure to add all our new signals:

.. code-block:: yaml

  pos_cursor:
    shape: 2
    dtype: double
    log: true
    log_storage:
      type: vector
      suffixes:
        - x
        - y

  pos_target:
    shape: 2
    dtype: double
    log: true
    log_storage:
      type: vector
      suffixes:
        - x
        - y

  size_cursor:
    shape: 1
    dtype: uint16

  size_target:
    shape: 1
    dtype: uint16

  color_cursor:
    shape: 3
    dtype: uint8

  color_target:
    shape: 3
    dtype: uint8

  state_task:
    shape: 1
    dtype: int8
    log: true


Regenerate our modified modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    licorice generate tutorial-6 -y

This should generate two new files: ``$LICORICE_WORKING_PATH/pinball_task.py`` and ``$LICORICE_WORKING_PATH/pinball_task_constructor.py``.
However, we will have to modify some of our old files as well.


Write pygame modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open the pygame display constructor (``$LICORICE_WORKING_PATH/pygame_display_constructor.py``) and change it to the following:

.. code-block:: python

    import math
    import pygame

    pygame.display.init()


    class Circle(pygame.sprite.Sprite):
        def __init__(self, color, radius, pos):
            pygame.sprite.Sprite.__init__(self)
            self.radius = radius
            self.color = color

            self.image = pygame.Surface((radius * 2, radius * 2)).convert_alpha()
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
                (self.radius * 2, self.radius * 2)
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

    refresh_rate = 2  # ticks (10 ms)

    sprite_cursor = Circle(color_cursor, size_cursor or 1, pos_cursor)
    sprite_target = Circle(color_target, size_target or 1, pos_target)

    sprites = pygame.sprite.Group([sprite_cursor, sprite_target])

Then open the pygame parser (``$LICORICE_WORKING_PATH/pygame_display_parser.py``) and change it to the following:

.. code-block:: python

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
        pygame.display.flip()


Now open the pygame display destructor (``$LICORICE_WORKING_PATH/pygame_display_destructor.py``) and make sure it has:

.. code-block:: python

    pygame.quit()

Next, open the pinball task constructor (``$LICORICE_WORKING_PATH/pinball_task_constructor.py``) and add the following:

.. code-block:: python

    # constants

    task_states = {
        "begin": 1,
        "active": 2,
        "hold": 3,
        "success": 4,
        "fail": 5,
        "end": 6,
    }

    black = [0, 0, 0]
    green = [0, 255, 0]
    red = [255, 0, 0]
    blue = [0, 0, 255]
    white = [255, 255, 255]
    light_blue = [150, 200, 255]

    # internals

    task_state = 1
    counter_hold = 0
    counter_begin = 0
    counter_success = 0
    counter_fail = 0
    counter_end = 0
    counter_duration = 0

    pos_cursor_i = [100, 100]
    pos_target_i = [50, 50]
    size_cursor_i = int(20)
    size_target_i = int(50)
    color_cursor_i = white
    color_target_i = green

    screen_width = 1280
    screen_height = 1024


    def is_cursor_on_target(cursor, target, window):
        return ((cursor[0] - target[0]) ** 2 + (cursor[1] - target[1]) ** 2) ** (
            0.5
        ) <= window


    def gen_new_target():

        width_max = screen_width - 2 * size_target_i
        height_max = screen_height - 2 * size_target_i

        return [
            int(np.random.rand() * width_max),
            int(np.random.rand() * height_max),
        ]


    # params

    time_hold = 50
    time_duration = 400

    time_success = 50
    time_fail = 100
    time_begin = 5
    time_end = 10

    acceptance_window = 100

    cursor_vel_scale = 10

This should initialize all the variables for our pinball tasks.

Finally, open the pinball task parser(``$LICORICE_WORKING_PATH/pinball_task.py``) and add the following:

.. code-block:: python

    # update cursor
    vel = (
        joystick_axis[0] * cursor_vel_scale,
        joystick_axis[1] * cursor_vel_scale,
    )
    pos_cursor_i = [pos_cursor_i[0] + vel[0], pos_cursor_i[1] + vel[1]]
    pos_cursor_i[0] = np.clip(pos_cursor_i[0], 0, screen_width - 2 * size_cursor_i)
    pos_cursor_i[1] = np.clip(
        pos_cursor_i[1], 0, screen_height - 2 * size_cursor_i
    )
    cursor_on_target = False

    # update task state
    if task_state == task_states["begin"]:

        counter_begin += 1

        if counter_begin >= time_begin:
            task_state = task_states["active"]
            counter_begin = 0
            pos_target_i = gen_new_target()
            color_target_i = green


    elif task_state == task_states["active"]:
        cursor_on_target = is_cursor_on_target(
            pos_cursor_i, pos_target_i, acceptance_window
        )

        if cursor_on_target:

            task_state = task_states["hold"]
            counter_hold += 1
            color_target_i = light_blue

        else:

            counter_duration += 1

            if counter_duration >= time_duration:
                task_state = task_states["fail"]
                counter_duration = 0
                color_target_i = red

    elif task_state == task_states["hold"]:

        cursor_on_target = is_cursor_on_target(
            pos_cursor_i, pos_target_i, acceptance_window
        )

        if not cursor_on_target:
            task_state = task_states["active"]
            counter_hold = 0
            color_target_i = green

        else:

            counter_hold += 1

            if counter_hold >= time_hold:
                task_state = task_states["success"]
                counter_hold = 0

    elif task_state == task_states["success"]:

        counter_success += 1

        if counter_success >= time_success:

            task_state = task_states["end"]
            counter_end += 1

    elif task_state == task_states["fail"]:

        counter_fail += 1

        if counter_fail >= time_fail:
            task_state = task_states["end"]
            counter_fail = 0

    elif task_state == task_states["end"]:

        counter_hold = 0
        counter_begin = 0
        counter_success = 0
        counter_fail = 0
        counter_duration = 0

        counter_end += 1

        if counter_end >= time_end:
            task_state = task_states["begin"]
            counter_end = 0


    # write output signals
    pos_cursor[:] = pos_cursor_i
    pos_target[:] = pos_target_i
    size_cursor[:] = size_cursor_i
    size_target[:] = size_target_i
    color_cursor[:] = color_cursor_i
    color_target[:] = color_target_i
    state_task[:] = task_state

This entails all the logic required for controlling the states of the game.


Run LiCoRICE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now, run LiCoRICE again from within your X server:

.. code-block:: bash

    licorice go tutorial-6 -y

And you should see the same output in the terminal as before, but now our pygame window should now be running the pinball game.

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
