#!/usr/bin/env python

import time
import socket
import re

class hvctl:
	""" Send and receive commands from FSC HV Control Unit.
	Version 1.0 (a metal box, 64 channels).
	
	Send a command to HV Control Unit.
	Get a raw text responce with .cmd().
	Get a decoded responce with .v() and other functions.
	"""
	DEFAULT_HOST = '172.22.60.202'
	DEFAULT_PORT = 2217
	
	def __init__(self, host = DEFAULT_HOST, port = DEFAULT_PORT, timeout = 1.0):
		addr = (host, int(port))
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(timeout)
		sock.connect(addr)
			
		#TODO: except
		self.sock = sock
	
	def cmd(self, command):
		""" Send a text command.
		Return a text response with stripped binary litter. """
		UNIT_TIMEOUT = 1.0 #
		
		content = command + "\r\n" # LF CF
		self.sock.sendall(content.encode())
		time.sleep(UNIT_TIMEOUT)
		return self._readout()
	
	def v(self):
		junk = self._readout() #a trash from the socket
		resp = self.cmd('v')
		
		# HVPS    0 V,  I(hv)    0 mA, I(+6)   65 mA, I(-6)   41 mA
		fields = {
			'digit': '(\d+)',
			'fdigit': '(d+(?:\.\d+)?)', #floating point
			'space': '\s+',
			}
		pattern = "HVPS{space}{digit} V,  I\(hv\){space}{digit} mA, I\(\+6\){space}{digit} mA, I\(-6\){space}{digit} mA\s*"
		pattern = pattern.format(**fields)
		
		mo = re.match(pattern, resp)
		if not mo:
			raise IOError("misformatted responce: %s (format: '%s')" % (repr(resp), pattern))
		
		return dict(zip(['V', 'Ihv', 'I6_pos', 'I6_neg'], mo.groups()))
		
	def _readout(self):
		""" Get a responce. """
		resp = ""
		LITTER = '\xff\xfb\x01\xff\xfb\x03\xff\xfd\x00\xff\xfb,'
		while True:
			try:
				data = self.sock.recv(4096)
			except socket.timeout:
				break
			
			if not data:
			    break
			resp += data 
		
		if resp.startswith(LITTER):
			resp = resp[len(LITTER):]
			
		resp = resp.translate(None, '\x00') #replace non-ASCII 
		resp = resp.replace("\n\r", "\n") #replace misused \n\r
		return resp


def main():
	import sys
	unit = hvctl()
	cmdline = ' '.join(sys.argv[1:])
	print( unit.cmd(cmdline))

	
if __name__ == "__main__":
	main()
