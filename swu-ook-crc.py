#!/usr/bin/python

########################################
## imports
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


########################################
## config and variables
########################################

bitcount = 8
offset = 0
marker = "01111110" # marks start and stop of a frame



########################################
## mainloop
########################################


while(1):
	line = ''
	while not line.endswith('\n'):
		line += sys.stdin.read(1)
#		print line
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
	count = 1 - offset 
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
	
	# convert to ascii
	ascii_reversed = list()
	for i in bytes_reverse:
		ascii_reversed.append(chr(i))
	
	print "bitstream: " + str(bin_str_reverse) + " len_" + str(len(ascii_reversed)) + " crc_"+str(crc)
	print "chars: " + str(ascii_reversed) + " len_" + str(len(ascii_reversed)) + " crc_"+str(crc)
	#print "DR: " + str(bytes_reverse) + " len_" + str(len(bytes_reverse)) + " crc_"+str(crc)
	
	sys.stdout.flush()
