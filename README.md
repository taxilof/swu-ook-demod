# 2400Hz on-off-keying-demodulator

## what is on-off-keying?
[wikipedia quote](https://en.wikipedia.org/wiki/On-off_keying):
> On-off keying (OOK) denotes the simplest form of amplitude-shift keying (ASK) modulation that represents digital data as the presence or absence of a carrier wave. In its simplest form, the presence of a carrier for a specific duration represents a binary one, while its absence for the same duration represents a binary zero.
 
## stuff required
 * SDR-stick (or use sample-files)
 * rtl-sdr
 * python
 * gcc
 * python-matplotlib, python-tk (only for debug)

## files:
* swu-ook-demod.py: The demodulator for 2400Hz ook (help is available with -h). Output is written to stdout.
* swu-ook-crc.py: Used to caluclate the crc for each frame and for bit-visualisation (also displays characters).
* fir.c: 100-tap FIR filter (low-pass ~3khz).

## usage:
* compile fir filter with `gcc -o fir fir.c` and make it executable `chmod +x fir`
* run everything and show bitstream: `rtl_fm -s 48k -C -f 155461000 -g 40 | ./fir | ./swu-ook-demod.py | ./swu-ook-crc.py | grep bitstream`
* debug mode (shows plot for every frame): `rtl_fm -s 48k -C -f 155461000 -g 40 | ./fir | ./swu-ook-demod.py -d` 
 * the plot pauses the process, to continue just close the plot (ctrl+w)

## notes:
* each byte is sent in reverse (mirrored), so take care (swu-ook-crc does)
