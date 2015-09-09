#!/usr/bin/python

########################################
## importss
########################################
import fileinput
import sys



########################################
## functions
########################################
def gen_crc16_2(buffe, polynom  = 0x1021): # 0xe03e or 0x1021
	bitrange = xrange(8) # 8 Bits
	crcsum   = 0xffff

	for byte in buffe:
		crcsum ^= byte << 8
		for bit in bitrange: # Schleife fuer 8 Bits
			crcsum <<= 1
			if crcsum & 0x7FFF0000:
				crcsum = (crcsum & 0x0000FFFF) ^ polynom
	return crcsum

def bcd_to_int(x):
	"""
	This translates binary coded decimal into an integer
	TODO - more efficient algorithm

	>>> bcd_to_int(4)
	4

	>>> bcd_to_int(159)
	345
	"""

	if x < 0:
		raise ValueError("Cannot be a negative integer")


		
	binstring = ''
	while True:
		q, r = divmod(x, 10)
		nibble = bin(r).replace('0b', "")
		while len(nibble) < 4:
			nibble = '0' + nibble
		binstring = nibble + binstring
		if q == 0:
			break
		else:
			x = q

	return int(binstring, 2)

########################################
## config and variables
########################################

bitcount = 8
marker = "01111110" # marks start and stop of a frame



########################################
## mainloop
########################################


while(1):
	# this quirk is needed so it works with pipes from python-executables
	line = ''
	while not line.endswith('\n'):
		b = sys.stdin.read(1)
		if (b == ''):	# EOF
			sys.stderr.write("EOF")
			exit(0)
		line += b
		
	line = line.replace("\n","")
	if line[0:7] == "0000000":
		line = line[1:]				# cut down to 6x 0
		
		
	# search for markers for start and stop of the frame
	start_pos = line.find(marker) + 8
	stop_pos = line.find(marker, start_pos) 
	# cut out the real frame
	line = line[start_pos:stop_pos]
	
	if len(line)<30:
		continue

	line = line.replace("111110", "11111")	# after 5x one-bit, a zero-bit is inserted => fix this 
	count = 1  
	bin_str = ""
	buff = ""
	bin_str_reverse = ""
	
	for x in line:
		bin_str += x
		buff += x
		if (count == bitcount):
			
			bin_str_reverse += buff[::-1] +"|"
			bin_str += "|"
			buff = ""
			count = 0
		count = count +1
	
	bin_str_reverse +=  buff[::-1] 


	# make nice list of bytes
	bytes_normal = list()
	for i in bin_str.split("|"):
		if i:
			bytes_normal.append(int(i,2))
	# reversed format
	bytes_reverse = list()
	for i in bin_str_reverse.split("|"):
		if i:
			bytes_reverse.append(int(i,2))
			
	# crc
	bytes_normal[-1] = 255-bytes_normal[-1]	# last two byts are inverted for crc calc
	bytes_normal[-2] = 255-bytes_normal[-2]
	crc = gen_crc16_2(bytes_normal)
	
	# convert to ascii, BCD and decimal
	ascii_reversed = ""
	bcd_reversed = ""
	decimal_reversed = ""
	for i in bytes_reverse:
		ascii_reversed += "  %5s |" % (repr(chr(i)).replace('\\x','0x').replace("'",""))
		bcd_reversed += " %2d" % ((i & 0xf0) >> 4)
		bcd_reversed += "  %2d |" % (i & 0x0f)
		decimal_reversed += "    %3d |" % i


	decimal_normal = ""			
	for i in bytes_normal:
		decimal_normal += "    %3d |" % i

	len_info = " len_" + str(len(bytes_reverse)) + " crc_"+str(crc)
	
	print "bits    r: " + str(bin_str_reverse) + len_info
	print "decimal r: " + decimal_reversed + len_info
	#print "decimal n: " + decimal_normal + len_info
	print "BCD     r: " + bcd_reversed + len_info
	print "ASCII   r: " + ascii_reversed + len_info
	print "|" + len_info

	sys.stdout.flush()
