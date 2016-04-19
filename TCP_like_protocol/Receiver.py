import sys
import os
import time
import socket
import select


class Receiver:
	def __init__(self):
		self.s = None		# socket object
		self.rcv_port = None
		self.srv_port = None
		self.srv_IP = None
		self.log = None
		self.data = None
		self.sender_socket = None

	# initialization of sender info 
	# almost the same as init_sender
	def init_receiver(self, filename, listen_port, server_IP, server_port, log_filename):
		self.srv_IP = server_IP
		self.srv_port = server_port
		self.rcv_port = listen_port
		if log_filename == 'stdout':
			self.log = sys.stdout 
		else:
			try:
				self.log = open(log_filename, 'w')
			except IOError:
				print 'Uable to open log file.'
		try:
			self.data = open(filename, 'w')
		except IOError:
			print 'Uable to open data file.'

	# create socket using server IP and port number
	# almost the same as create_socket in Sender class
	def create_socket(self):
		try:
			# running on top of UDP. DGREM socket (UDP). 
			#self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			addr_info = socket.getaddrinfo(self.srv_IP, self.srv_port)[0]  
			self.s = socket.socket(addr_info[0], socket.SOCK_DGRAM)
			# for both IPv4 and IPv6. return 5-tuple: (family, socktype, proto, canonname, sockaddr)
			
			# resolve OSError: [Errno 48] Address already in use may occur using socket.SO_REUSEADDR flag
			self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		except socket.error, msg:
			print 'Creating Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		try:	
			self.s.bind(('', self.rcv_port))
		except socket.error, msg:
			print 'Binding Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

	def receive_file(self):
		try:
			while 1:
				#read_list, write_list, error_list = select.select([0, self.s], [], [])
				try:
					read_list, write_list, error_list = select.select([self.s], [], [])
				except select.error, e:
					print 'Select Error. Exiting...'
					break
				except socket.error, e:
					print 'Socket Error. Exiting...'
					break
				rcv_data, sender = self.s.recvfrom(4096)
				self.data.write(rcv_data)
				self.log.write('receive data')


		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Receiver.'
			self.s.close()
			sys.exit()


		self.s.close()



	def receiver(self, filename, listen_port, server_IP, server_port, log_file):
		try:
			self.init_receiver(filename, listen_port, server_IP, server_port, log_file)
		
			self.create_socket()
			self.receive_file()
		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Receiver.'
			self.s.close()
			sys.exit()

		self.s.close()






	
def main():
	if len(sys.argv) == 6:
		filename = sys.argv[1]
		server_IP = sys.argv[3]
		log_file = sys.argv[5]
		# port number should be integer
		try:
			listen_port = int(sys.argv[2])
			server_port = int(sys.argv[4])
		except ValueError:
			print 'Invalid Command. Exiting...'
			sys.exit()
	else: # clarify the usage of Receiver.py.
		print 'Usage: python receiver.py <filename> <listening_port> <server_IP> <server_port> <log_filename>'

	newR = Receiver()
	newR.receiver(filename, listen_port, server_IP, server_port, log_file)

if __name__ == '__main__':
	main()