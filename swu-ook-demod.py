#!/usr/bin/python

########################################
## imports
########################################
import signal
import sys
import argparse
import os
import collections
import struct

from time import time




########################################
## parameter stuff
########################################
__author__ = 'taxilof'
parser = argparse.ArgumentParser(description='This is a 2400Hz ook demodulator.')
parser.add_argument('-f', "--file", help='input file name(- is STDIN) [default: STDIN]',required=False, default="-")
parser.add_argument('-s',"--samplerate", help='samplerate[default: 48000]', required=False, type=int, default=48000)
parser.add_argument('-d',"--debug", help='debug mode: plot every found frame', required=False, action="store_true")
parser.add_argument('-aw', "--awindow",  help='length in ms of the sliding window for finding average threshold [default: 4ms]', required=False, type=int, default=4)
parser.add_argument('-r',"--reportingperiod", help='reports every n seconds [default: off]', required=False, type=int, default=0)
args = parser.parse_args()

# convert args to config-variables
config_samplerate = args.samplerate
config_infile = args.file
config_awin_len = int(args.awindow/1000.0*config_samplerate)		# convert to samples
config_reportingperiod = args.reportingperiod
if args.debug:
	debug = 1
	try:
		import matplotlib.pyplot as plt
	except ImportError:
		print "error: could not import pyplot, no debugging available"
		pass	
else:
	debug = 0

if config_infile=="-":
	inf = sys.stdin
	is_file = False
	filesize = "n/a"
	config_infile = "STDIN"
else:
	inf = open(config_infile)
	filesize = os.path.getsize(config_infile)
	is_file = True




########################################
## functions
########################################
# catch ctrl+c
def signal_handler(signal, frame):
	sys.stderr.write("\ndone, found " + str(found_count) + " sequences (this took " + str((time()-start_time)) +"s)\n")
	exit(0)


def sign(x): 
	return 1 if x >= 0 else -1

# find all peaks between zerocrossings and return the average height
def find_average_peak_height(l):
	min_peak = 1000
	max_peak = 10000
	peaks = list()
	zc_search_buff = list()
	old_val = 0
	for val in l:
		zc_search_buff.append(abs(val))
		if sign(val) != sign(old_val):
			# found new zc: look for peak in zc_search_buff and reset
			peak = max(zc_search_buff)
			if peak>min_peak and peak < max_peak:
				peaks.append(peak)
			zc_search_buff = list()
		old_val = val
	# return stuff
	if len(peaks) >= 2:
		avg = sum(peaks) / float(len(peaks))
		#print "avg: " + str(avg)
		return avg
	else:
		return 0

# find all peaks over threshold and between a zc-ing
def find_peaks(l, min_peak):
	peaks = list()
	zc_buff = list()
	zc_old_index = 0
	old_val = 0
	c = 0
	for val in l:
		c+=1
		zc_buff.append(abs(val))
		if sign(val) != sign(old_val):
			# found new zc: look for peak in buffer and reset
			peak = max(zc_buff)
			if peak>min_peak:
				if sign(val) == 1:
					peak = 0-peak
				peaks.append([zc_old_index+zc_buff.index(abs(peak)), peak])
			zc_buff = list()
			zc_old_index = c
		old_val = val
	return peaks

# inspect a frame and return bitstream. the distance between the peaks (zero-bits) is used to calculated the number of one-bits.
def inspect(frame):
	avg = find_average_peak_height(frame)
	peaks = find_peaks(frame, avg*0.5)
	
	old_peak_pos = 0
	bitstream = ""
	startbit = 1
	# examine peak distance
	for p in peaks:		# p[0] is peak pos, p[1] is peak height
		diff = p[0]-old_peak_pos		# distance between peaks in samples
		
		# check every position if the diff is found
		add = ""
		
		if startbit == 1:
			add += "0" 		# startbit
			startbit = 0	
		else:
			for i in [1,2,3,4,5,6,7,8]:
				mid =  i*det_0_mid	# e.g. 10 20 30 40 50 60 70 80 for 48k samplerate
				if mid - det_0_jit <= diff and diff <= mid + det_0_jit:
					for ii in range(i-1):
						add += "1"	# add as many 1's as needed
					add += "0" 		# each peak is a 0 
					
		bitstream += add
		# save old peak pos
		old_peak_pos = p[0]
		
	# end stuff:
	print bitstream
	
	#sys.stdout.write("test")
	sys.stdout.flush()
	
	if(debug):
		# visualize the frame:
		plt.plot(range(len(inspection_buffer)),inspection_buffer)
		old_peak_pos = 0
		plt.axhline(y=avg*0.5,color='g')
		plt.axhline(y=-avg*0.5,color='g')
		plt.axhline(0, color='red')
		for p in peaks:
			diff = p[0]-old_peak_pos
			#plt.axvline(x=p[0]*0.5, color='g')
			plt.annotate(str(diff), xy=(p[0], p[1]),  xycoords='data',
							xytext=(-2, 20*sign(p[1])), textcoords='offset points',
							arrowprops=dict(arrowstyle="->")
							)
			old_peak_pos = p[0]
		mng = plt.get_current_fig_manager()
		mng.resize(*mng.window.maxsize())
		plt.show()	



########################################
## settings
########################################
#config
baud = 4800
#symbol decoder settings
det_0_mid = config_samplerate/baud
det_0_jit = 4
#det_0_jit = diff_mid / 2 - 1
sys.stderr.write("working with file \"%(config_infile)s\" with %(length)s bytes at %(config_samplerate)s samples/s\n" % {'config_infile':config_infile, 'length':filesize, 'config_samplerate':config_samplerate})
sys.stderr.write("working with samplerate " + str(config_samplerate) + " samples/s and " + str(baud) + "baud.\n")
sys.stderr.write("sliding window size for average threshold detection is " + str(args.awindow) + "ms or " + str(config_awin_len) + " samples.\n")
sys.stderr.write("zerocrossdetection: zero-bit equals " + str(det_0_mid) + "+-" + str(det_0_jit) + " samples.\n")



########################################
## variables
########################################
# timers
old_time = time()
start_time = time()

# counter stuff
sample_counter = 0
iterations = 0
found_count = 0 

# sliding window for average threshold detection
a_win = collections.deque(maxlen=config_awin_len)

# reduce cpu time: just process after n samples
samples_passed = 0
samples_passed_max = int(config_awin_len/2)

# copy samples to inspection buffer, which gets inspected after the end of a frame has been detectet
inspection_buffer = list()
inspection_state = 0		# 0: nothing found
							# 1: frame started
							# 2: frame ended, doing inspection

########################################
## main Loop
########################################
signal.signal(signal.SIGINT, signal_handler) # register ctrl+c handler

while(1):
	# calc sample/s processing rate
	if config_reportingperiod:
		if time() - old_time > config_reportingperiod:
			# 1 second passed
			if is_file:
				sys.stderr.write(str(int(iterations/float(filesize)*200)) + "% at "+   str((iterations-sample_counter)/config_reportingperiod) +  " samples/s\n")
			else:
				sys.stderr.write("Read " + str(iterations)+ " samples at "+   str((iterations-sample_counter)/config_reportingperiod) +  " samples/s\n")
			sample_counter = iterations
			old_time = time()
		

	# count iterations
	iterations+=1	
	
	# read samples
	try:
		s = struct.unpack('h',inf.read(2))[0]
	except Exception, ex:
		sys.stderr.write("Error: " + str(ex) + "\n")
		sys.stderr.write( "Done, found " + str(found_count) + " Sequences (this took " + str((time()-start_time)) +"s)\n")
		exit()

	a_win.append(s)	# append to average threshold finder ringbuffer 


	# if the start of a frame is found, start to copy samples to inspection buffer 
	# this code-block has to be before the code that sets state=1 and copys old values from a_win to inspection_buffer
	if inspection_state == 1:			# frame started
		inspection_buffer.append(s)		# copy samples to inspection buffer
	if inspection_state == 2:			# frame ended
		inspect(inspection_buffer)		# examine inspection buffer (prints the bitstream to STDOUT)
		found_count += 1
		inspection_state = 0			# reset state when done
		
		
	# only check stuff in a_win window every n samples
	samples_passed += 1
	if samples_passed > samples_passed_max:
		samples_passed = 0
		
		# look if a frame is about to start in average threshold window a_win
		avg_peak = find_average_peak_height(a_win)
		if avg_peak > 0:
			if inspection_state == 0:				# frame started
				inspection_state = 1				# set state
				inspection_buffer = list()			# clean old list
				inspection_buffer.extend(a_win)		# copy over all prev values from window buffer
		else: # no signal found
			if inspection_state == 1:	# only if the start of a frame is already detected
				inspection_state = 2	# set state to frame-has-ended, so tell main loop to inspect

	
	


