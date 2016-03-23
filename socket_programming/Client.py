import hashlib
import os
import socket
import sys
import select

"""
a client using Python's select module to detect message from sys.stdin and socket
"""

class Client:

	TIME_OUT = 30 * 60  # Inactive time for a client


	def __init__(self):
		self.s = None

	# create socket and connect to server
	def create_socket(self, host, port): 
		try:
			# create an AF_INET, STREAM socket (TCP)
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		except socket.error, msg:
			print 'Failed to create socket. Exiting...'
			sys.exit();

		#print 'Socket Created'

		try:
			remote_ip = socket.gethostbyname(host) # get server ip address (IPv4)
		except socket.gaierror:
			print 'Hostname could not be resolved. Exiting...'
			sys.exit() 

		# connect to server
		try:
			self.s.connect((remote_ip, port))
			print 'Socket connected to', host, 'on IP :', remote_ip
		except socket.error, e:
			print 'Failed connecting to server. Exiting...'
			sys.exit()



	# main part for Client class
	# wait for 2 kinds of messages
	# one is message from sys.stdin. client command
	# another is message received from server. 
	def client(self, host, port):
		try:
			self.create_socket(host, port)
			if self.login() == 0:
				self.s.close()
			else:
				while 1:
					try:
						# wait for message from stdin(0) and socket(self.s)
						read_list, write_list, error_list = select.select([0, self.s], [], [])
					except Exception, (error, message):
						self.s.close()
						sys.exit()
						break
					

					for sock in read_list:
						if sock == 0: # message from stdin
							# data = sys.stdin.readline()[:-1]
							data = raw_input()
							if data:
								self.send_message(data)
						if sock == self.s:
							data = self.receive_message()
							if data:
								if 'Log Out' in data:
									self.s.close()
								#print 'received the message from server'
								print data

		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Client.'
			self.s.close
			sys.exit()

		
		self.s.close()


	# login part.
	# translate password using SHA1 function for security
	# When the received message contains 'Failed', it means the login is failed (in many reasons). Then print reasons
	# When the received message contains 'Welcome', it means user has logged in successfully.
	def login(self):
		print 'Login Please'
		while 1:
			name = raw_input('Username: ')
			password = raw_input('Password: ')
			encode_pw = hashlib.sha1(password).hexdigest() # use SHA1 function for security
			if ' ' in name:
				print 'Name cannot contain space. Please input again.'
				continue
			comb = name + ' ' + encode_pw
			self.send_message(comb)
			while 1:
				rcv_message = self.receive_message()
				if 'Failed' in rcv_message:
					print rcv_message
					return 0
				elif 'Welcome' in rcv_message:
					print rcv_message
					return 1
				else:
					print rcv_message
					break


	# error handling for socket sending
	def send_message(self, message):
		try:
			self.s.sendall(message)
		except socket.error, e:
			print 'Error sending data. Exiting...'
			sys.exit()
		#print 'haha sent!'

	# error handling for socket receiving
	def receive_message(self):
		try:
			buff = self.s.recv(1024)
		except socket.error, e:
			print 'Error receiving data. Exiting...'
			sys.exit()
		return buff

			
def main():
	if len(sys.argv) == 3:
		host = sys.argv[1]
		port = int(sys.argv[2])
		newC = Client()
		newC.client(host, port)
	else: # clarify the usage of Client.py.
		print 'Usage: python Client.py <server_IP_address> <server_port_number>'

if __name__ == '__main__':
	main()
