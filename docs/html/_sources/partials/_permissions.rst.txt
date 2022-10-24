To ensure you have the correct permissions, create a new limits file with
``sudo vi /etc/security/limits.d/licorice.conf`` and add these lines to
ensure your user can run licorice. *Replace* ``user`` *with the user you are
using to run licorice*.

.. code-block:: bash

    user - rtprio 95
    user - memlock unlimited

Now log out and back in and you are set up for non-realtime licorice development and usage!
