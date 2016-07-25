#!/usr/bin/env python

import time
import socket
import re

class HVUnit():
	""" Send and receive commands from FSC HV Control Unit.
	Version 4.0 (a metal box, 64 channels).
	
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
		
		try:
			sock.connect(addr)
			
		except socket.timeout:
			raise IOError("connection is timed out")
			
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
		pattern = "HVPS{space}{digit} V,  I\(hv\){space}{digit} mA, I\(\+6\){space}{digit} mA, I\(-6\){space}{digit} mA"
		values = self._parse_resp(pattern, resp)
		
		return dict(zip(['V', 'Ihv', 'I6V_pos', 'I6V_neg'], values))
	
	def _parse_resp(self, pattern, string):
		""" Parse a responce string according to pattern.
			Return a list of field values 
			or raise an IOError if responce doesn't match pattern.
		"""
		fields = {
			'digit': '(\d+)',
			'fdigit': '(d+(?:\.\d+)?)', #floating point
			'space': '\s+',
			}
		
		pattern = pattern.format(**fields)
		pattern += "\s*" #any number of space in the end 
		
		mo = re.match(pattern, string)
		if not mo:
			raise IOError("wrong responce: %s (format: '%s')" % (repr(string), pattern))
			
		return mo.groups()
		
		
	def _readout(self):
		""" Get a responce from unit. """
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
		
		
	### Sort of API for on/off/set functions.
	
	def set(self, chan, code):
		""" Set HV channel DAC to value """
		resp = self.cmd('c %d %d' % (chan, code))
		
		#resp: chan 99, code 100 <- HV setup
		pattern = "chan{space}{digit}, code{space}{digit} <- HV setup"
		resp_chan, resp_code = self._parse_resp(pattern, resp)
		
		if int(resp_chan) != chan or int(resp_code) != code:
			raise IOError("Channel or code in responce not the same as in request (%d %d): '%s'" %
					(chan, code, resp) )
		return
	
	def off(self):
		""" Turn HV off """
		resp = self.cmd('o0')
		pattern = "Turn OFF HV Power supply"
		self._parse_resp(pattern, resp)
		return
	
	def on(self): 
		""" Turn HV on """
		resp = self.cmd('o1')
		pattern = "Turn ON HV Power supply"
		self._parse_resp(pattern, resp)
		return
		
	###
	
	
	
def main():
	import sys
	unit = HVUnit()
	cmdline = ' '.join(sys.argv[1:])
	print( unit.cmd(cmdline))

	
if __name__ == "__main__":
	main()
