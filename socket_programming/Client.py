import hashlib
import os
import socket
import sys


class Client:

	TIME_OUT = 30 * 60  # Inactive time for a client


	def __init__(self):
		self.s = None

	# create socket and connect to server
	def create_socket(self, host, port):
		# 
		try:
			# create an AF_INET, STREAM socket (TCP)
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		except socket.error, msg:
			print 'Failed to create socket. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit();

		print 'Socket Created'

		try:
			remote_ip = socket.gethostbyname(host) # get server ip address (IPv4)
		except socket.gaierror:
			print 'Hostname could not be resolved. Exiting...'
			sys.exit() 

		# connect to server
		self.s.connect((remote_ip, port))
		print 'Socket connected to', host, 'on IP :', remote_ip

	# send data to server
	def send_data(self, message):
		try:
			self.s.sendall(message)
		except socket.error:
			print 'Send failed. Exiting...'
			sys.exit()
		print 'haha sent!'

	

	# close socket
	def close_socket(self):
		self.s.close()

	def talk_with_server(self, host, port):
		self.create_socket(host, port)
		self.authentication()
		
		self.close_socket()


	def authentication(self):
		while 1:
			name = raw_input('Username: ')
			self.send_data(name)
			valid_name = self.s.recv(4096)

			password = raw_input('Password: ')
			send_pw = hashlib.sha1(password).hexdigest()
			self.send_data(send_pw)

			valid_pw = self.s.recv(4096)
			if not valid_name:
				print 'User dose not exist. Please Input again.'
				continue
			if not valid_pw:
				print 'Invalid login. Please Input again'
				continue
			if valid_name and valid_pw:
				print 'Login successfully!'
				break

	


def main():
	if len(sys.argv) == 3:
		host = sys.argv[1]
		port = int(sys.argv[2])
		newC = Client()
		newC.talk_with_server(host, port)
	else:
		print 'Usage: python Client.py <server_IP_address> <server_port_number>'

if __name__ == '__main__':
	main()
