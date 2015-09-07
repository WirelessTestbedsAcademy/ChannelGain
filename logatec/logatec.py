# This example shows how to measure channel gain between two nodes in a
# LOG-a-TEC testbed.

# Import some classes from vesna-alh-tools. Follow the instructions at
# https://github.com/sensorlab/vesna-alh-tools if you don't have it installed
# yet.
from vesna import alh
from vesna.alh.signalgenerator import SignalGenerator, SignalGeneratorProgram
from vesna.alh.spectrumsensor import SpectrumSensor, SpectrumSensorProgram

# Some standard Python modules.
import logging
import time

# We use NumPy (http://www.numpy.org) for calculations. You can usually install
# NumPy using the package manager on your Linux system.
import numpy as np

# All channel measurement code is encapsulated in the NodePair class - it makes
# it easier to reuse it in other experiments.
class NodePair(object):

	# Object constructor takes two nodes: Node doing the signal
	# transmission and node doing power measurements.
	def __init__(self, txnode, rxnode):
		# We set up the SignalGenerator and SpectrumSensor objects here
		# for later use. We also query both nodes for their
		# corresponding lists of available hardware configurations.
		#
		# Since hardware will not change during the experiment, we only
		# do the query once in object constructor. This makes repeated
		# measurements faster.
		self.generator = SignalGenerator(txnode)
		self.generator_cl = self.generator.get_config_list()

		self.sensor = SpectrumSensor(rxnode)
		self.sensor_cl = self.sensor.get_config_list()

	# This method performs the power measurement. f_hz parameter is the
	# central frequency in hertz on which the channel measurement will be done.
	# ptx_dbm is the transmission power in dbm. If ptx_dbm is None, then
	# the transmitting node will remain silent.
	def measure(self, f_hz, ptx_dbm):
		now = time.time()

		if ptx_dbm is not None:
			# If transmission was requested, setup the transmitter.
			tx_config = self.generator_cl.get_tx_config(f_hz, ptx_dbm)
			if tx_config is None:
				raise Exception("Node can not scan specified frequency range.")

			generator_p = SignalGeneratorProgram(tx_config, now + 1, 14)
			self.generator.program(generator_p)

		# Setup the receiver for power measurement at the same
		# frequency as the transmitter. We will only sense a single
		# frequency, hence both start and stop parameters of the sweep
		# are set to f_hz.
		sweep_config = self.sensor_cl.get_sweep_config(f_hz, f_hz, 400e3)
		if sweep_config is None:
			raise Exception("Node can not scan specified frequency range.")

		sensor_p = SpectrumSensorProgram(sweep_config, now + 3, 10, 1)
		self.sensor.program(sensor_p)

		# Note that the transmit interval is longer than the receive
		# interval:
		#
		# now    + 1        + 3         /           + 13       + 15
		# |      tx start   rx start    \           rx stop    tx stop
		# |      |          |           /           |          |
		# |      |          |===========\===========|          |
		# |      |             receive  /           |          |
		# |      |                      \                      |
		# |      |======================/======================|
		#           transmit
		#
		# This is to make sure that signal transmission is happening
		# during the whole time the receiver is measuring signal power.
		# Start times may differ +/- 1 second due to unsynchronized
		# clocks and management network latency.

		while not self.sensor.is_complete(sensor_p):
			print "waiting..."
			time.sleep(2)

		# Retrieve the data and return a single vector with power
		# measurements (in dBm) from the sensing node.
		result = self.sensor.retrieve(sensor_p)

		return np.array(result.get_data())[:,0]

	# This method calculates the channel gain between the nodes.
	def get_channel_gain(self, f_hz, ptx_dbm):

		def db_to_mw(db):
			return 10.**(db/10.)

		def mw_to_db(mw):
			return 10.*np.log10(mw)

		# First, measure just the noise level on the receiving node.
		# Transmitter is turned off.
		pnoise_dbm = self.measure(f_hz, None)

		# Second, measure the received signal power level with the
		# transmitter turned on.
		prx_dbm = self.measure(f_hz, ptx_dbm)

		# Convert all power values to linear scale.
		ptx_mw = db_to_mw(ptx_dbm)
		pnoise_mw = db_to_mw(pnoise_dbm)
		prx_mw = db_to_mw(prx_dbm)

		# Take the mean of both noise and received signal power
		# measurements.
		pnoise_mw_mean = np.mean(pnoise_mw)
		prx_mw_mean = np.mean(prx_mw)

		print "p_noise = %.1f dBm (mean=%e mW std=%e mW)" % (
				mw_to_db(pnoise_mw_mean),
				pnoise_mw_mean,
				np.std(pnoise_mw))
		print "p_rx    = %.1f dBm (mean=%e mW std=%e mW)" % (
				mw_to_db(prx_mw_mean),
				prx_mw_mean,
				np.std(prx_mw))

		# Use the mean values to estimate the channel gain.
		h_mean = (prx_mw_mean - pnoise_mw_mean)/ptx_mw

		# Convert back to logarithmic scale.
		h_mean_db = mw_to_db(h_mean)

		print "h = %.1f dB" % (h_mean_db,)

		return h_mean_db

def main():
	# Turn on logging so that we can see requests and responses in the
	# terminal.
	logging.basicConfig(level=logging.INFO)

	# We must first create an object representing the coordinator node.
	coor = alh.ALHWeb("https://crn.log-a-tec.eu/communicator", 9501)

	# We will be using node 51 in the LOG-a-TEC Campus in-door
	# cluster as the transmitting node and node 53 in the same cluster as
	# the receiving node.
	#
	# These nodes are equipped with SNE-ISMTV-2400 radio boards that contain
	# CC2500 reconfigurable transceivers. This tranceiver operates in the
	# 2.4 GHz ISM band.
	#
	# Make sure you reserved the cluster in the calendar before running the
	# experiment!
	txnode = alh.ALHProxy(coor, 51)
	rxnode = alh.ALHProxy(coor, 53)

	pair = NodePair(txnode, rxnode)

	# We will perform the channel gain measurement at 2.425 GHz with the
	# transmitting node transmitting with 0 dBm of power.
	h = pair.get_channel_gain(2425e6, 0)

main()
