import hashlib
import os
import socket  
import sys
from thread import *



class Server:
	#HOST = gethostname()
	HOST = socket.getfqdn() # get hostname of maching where it is currently executing

	# default number of seconds contained in the environment variable
	BLOCK_TIME = 60

	"""
	initiation 
	
	s (socket object)
	 users:
	  	username (string):
	 		password (string)
	 		online (boolean)
	 		socket (socket object) 
	 socket_list:
	 	socket (socket object):
	 		username (string)
	"""

	def __init__(self):
		self.s = None  
		self.users = {} 
		# self.socket_list = {}
		
		
	# create socket and listen to connections
	def create_socket(self, port):
		try:
			# create an AF_INET, STREAM socket (TCP)
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		except socket.error, msg:
			print 'Create Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		try:
			#self.s.bind((Server.HOST, port))
			self.s.bind(('', port))

		except socket.error, msg:
			print 'Bind Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		self.s.listen(10) # 10: number of max waiting connnections when busy
		# print 'Socket now listening'


	# use threads to handle connections
	def client_thread(self, conn):
		# send message to connected client
		# conn.send('Welcome to the Server. Type username and hit ENTER \n')

		while 1:
			data = conn.recv(1024)
			reply = "Receive name from client: " + data
			if not data:
				break

			conn.sendall(reply)
			print 'User:', data

		conn.close()

	
	def talk_with_client(self):
		while 1:
			# wait to accept a connection
			conn, addr = self.s.accept()
			print 'Connected with', addr[0], ':', str(addr[1])

			start_new_thread(self.client_thread,(conn,))
		
		self.s.close()

	
	def load(self):
		fileRead = open("user_pass.txt", 'r')
		lines = fileRead.readlines()
		fileRead.close()

		for line in lines:
			person = line.split()
			name = person[0]
			password = person[1]
			self.users[name] = {}
			self.users[name]['password'] = password
			self.users[name]['online'] = False

	def authentication(self, username, password):
		if username not in self.users:
			print 'Username Not Found'
		else:
			if self.users[username] != password:
				print "Wrong password, try again."
		pw_sha1 = self.sha1(password)
		return self.users[username] == pw_sha1


def main():
	if len(sys.argv) > 1:
		port = int(sys.argv[1])
	else:
		port = 4119
	newS = Server()
	newS.load()
	newS.create_socket(port)
	newS.talk_with_client() 
	
if __name__ == '__main__':
	main()
