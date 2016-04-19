import hashlib
import os
import socket  
import sys
import time
import select
#from threading import Thread
import struct

class Sender:
	TIME_OUT = 5 
	MSS = 576 # value for the maximum segment size

	# define some info for sender to be initialized
	def __init__(self):
		self.s = None			# socket object
		self.log = None			# log file for sender
		self.rcv_port = None	# receiver port number
		self.rcv_IP = None		# receiver IP address
		self.ack_port = None	# ack port number
		self.window = 1			# window size, default value is 1
		self.data = None		# data to transmit
		self.est_rtt = 0		# sender should have one more output field - estimated RTT
		self.dev_rtt = 0		# default as 0
		


	# initialization of sender info 
	def init_sender(self, data_file, remote_IP, remote_port, ack_port, log_filename, window_size):
		self.rcv_IP = remote_IP	
		self.rcv_port = remote_port
		self.ack_port = ack_port
		self.window = window_size
		# if the log filename is 'stdoue' - display to the standard output
		if log_filename == 'stdout':
			self.log = sys.stdout 
		else:
			try:
				self.log = open(log_filename, 'w')
			except IOError:
				print 'Uable to open log file.'
		try:
			self.data = open(data_file, 'r')
		except IOError:
			print 'Uable to open data file.'

	# create socket and listen 
	# reuse function from HW3
	def create_socket(self):
		try:
			# running on top of UDP. DGREM socket (UDP). 
			#self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			addr_info = socket.getaddrinfo(self.rcv_IP, self.rcv_port)[0]  
			self.s = socket.socket(addr_info[0], socket.SOCK_DGRAM)
			# for both IPv4 and IPv6. return 5-tuple: (family, socktype, proto, canonname, sockaddr)
			
			# resolve OSError: [Errno 48] Address already in use may occur using socket.SO_REUSEADDR flag
			self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		except socket.error, msg:
			print 'Creating Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		try:	
			self.s.bind(('', self.ack_port))
		except socket.error, msg:
			print 'Binding Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

	def send_file(self):
		#for each in self.data:
		self.s.sendto('hi I send a hello to you. Hope you got A for all courses! And Hope you find a good intern!', (self.rcv_IP, self.rcv_port))
		self.log.write('transmitted')

	# the main part for sender class
	# send packets to receiver
	def sender(self, data_file, remote_IP, remote_port, ack_port, log_file, window_size):
		try:
			self.init_sender(data_file, remote_IP, remote_port, ack_port, log_file, window_size)
		
			self.create_socket()
			self.send_file()
			self.data.close()
			self.log.close()
		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Server.'
			self.s.close()
			sys.exit()

		self.s.close()
	



	def log_time(self):
		now = time.localtime()
		return "{0}-{1}-{2} {3}:{4}:{5}".format(now[0], now[1], now[2], now[3], now[4], now[5])



	
def main():
	if len(sys.argv)!=7 and len(sys.argv)!=6:
		print 'Usage: python Sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename> <window_size>'
	else:
		filename = sys.argv[1]
		remote_IP = sys.argv[2]
		log_file = sys.argv[5]
		# port number should be integer
		try:
			remote_port = int(sys.argv[3])
			ack_port = int(sys.argv[4])
			#window_size = int(sys.argv[6])
		except ValueError:
			print 'Invalid Input Command. Exiting...'
			sys.exit()
		# If no parameter is specified, the default window size value should be 1
		if len(sys.argv)==6:
			window_size = 1
		else:
			# window size should be integer
			try:
				window_size = int(sys.argv[6])
			except ValueError:
				print 'Invalid Input Command. Exiting...'
				sys.exit()

		newS = Sender()
		newS.sender(filename, remote_IP, remote_port, ack_port, log_file, window_size)
		
	
if __name__ == '__main__':
	main()















