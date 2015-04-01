Channel gain experiment
=======================


LOG-a-TEC
---------

The `logatec.py` script uses a pair of sensor nodes in the City Center cluster
of the LOG-a-TEC testbed and measures channel gain between them. Two
measurements are done: first noise power is measured at the receiving node
while the transmitter is silent. After that, receiving node measures received
signal power while the transmitter is transmitting a signal with a constant
power. From these two measurements, channel gain value is estimated.

Experiments running on LOG-a-TEC testbed are controlled over the Internet from
a Python script running on the user's computer. To run an experiment, you need
the following installed on your system:

 * Python 2.x. (usually already installed on Linux systems),
 * [numpy](http://www.numpy.org/) (usually can be installed through the package manager on Linux systems),
 * [vesna-alh-tools](https://github.com/sensorlab/vesna-alh-tools) and
 * a valid username and password for the LOG-a-TEC testbed (see vesna-alh-tools
   README on how to set it up).

To run the experiment, use:

    $ python logatec.py

See comments in the script for more details.
