import hashlib
import os
import socket  
import sys
import time
import select
# from thread import *

"""
a multi-client chat server using Python's select module
"""


class Server:
	#HOST = gethostname()	# HOST = socket.getfqdn() # get hostname of maching where it is currently executing

	# default number of seconds contained in the environment variable
	BLOCK_TIME = 60
	TIME_OUT = 30 * 60

	"""
	s (socket object)

	users (dictionary): {
		[username] (string): {
		 	[password] (string)
	 		[online] (boolean)
			[block] (boolean)
			[blocktime] (float): last block time
		 	[activetime] (float): last active time
		 	[logouttime] (float): last log out time
		}
	}

	socket_list should be a dictionary so that each socket connect to one username!!
	socket_list (dictionary): {[socket] (socket object): username (string)}
	"""

	def __init__(self):
		self.s = None 
		self.users = {} 
		self.socket_list = {}
		

		
	
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
			self.users[name]['block'] = False
			self.users[name]['blocktime'] = None # used for block clients with invalid password
			self.users[name]['activetime'] = None # used for logout inactive clients
			self.users[name]['logouttime'] = None # used for 'last' command
			self.users[name]['socket'] = None # used for broadcast and send


		
	# create socket and listen to connections
	def create_socket(self, port):
		try:
			# create an AF_INET (IPv4), STREAM socket (TCP).
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		except socket.error, msg:
			print 'Creating Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		try:
			# resolve OSError: [Errno 48] Address already in use may occur using socket.SO_REUSEADDR flag
			self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		except socket.error, msg:
			print 'Creating Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		try:
			
			self.s.bind(('', port))
		except socket.error, msg:
			print 'Binding Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		print 'Listening to port', port, '...'
		self.s.listen(10) # 10: number of max waiting connnections when busy
		# print 'Socket now listening'

	
	def server(self, port):
		select_list = []
		try:
			self.load()
			self.create_socket(port)
			
			while 1:

				# check time out for each online user
				for each_socket in self.socket_list:
					self.auto_logout(each_socket)

				select_list = self.socket_list.keys()
				select_list.append(self.s)
				try:
					# use select to get the list sockets which are ready to be read. 
					# Asynchronous I/O is provided in select module (non-block)
					read_list, write_list, error_list = select.select(select_list, [], [])
				except select.error, e:
					print 'Select Error. Exiting...'
					break
				except socket.error, e:
					print 'Socket Error. Exiting...'
					break

				for sock in read_list:
					if sock == self.s:  # a new connection received
						client_socket, client_addr = self.s.accept()
						print 'Connection request from', client_addr
						# call function login to authenticate username and password
						if self.login(client_socket, client_addr):
							print self.socket_list[client_socket], ': Logged In.'
						else:
							print 'Failed Logging In.'

					else:  # command from client
						self.command_processing(sock)
							
							#print 'receive command: ', client_message
							#msg = 'received the message from ' + client_message
							#self.send_message(client_socket, msg)
			
		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Server.'
			self.s.close()
			sys.exit()
		
		self.s.close()


	def command_processing(self, client_socket):
		client_name = self.socket_list[client_socket]
		client_message = self.receive_message(client_socket)
		if client_message:
			self.users[client_name]['activetime'] = time.time()
			if client_message == 'who':
				self.who(client_socket)
			elif client_message == 'logout':
				self.logout(client_socket)
			elif 'last' in client_message and client_message[:4] == 'last':
				c_msg = client_message.split()
				if len(c_msg) != 2 or (not c_msg[1].isdigit()):
					self.send_message(client_socket, 'Invalid Command')
				else:
					num = int(c_msg[1])
					self.last(client_socket, num)
			elif 'broadcast' in client_message and client_message[:9] == 'broadcast':
				if len(client_message) <= 10 or client_message[9] != ' ':
					self.send_message(client_socket, 'Invalid Command')
				else:
					b_msg = client_message[10:]
					self.broadcast(client_socket, b_msg)
			elif 'send' in client_message and client_message[:5] == 'send ':
				if client_message[5] == '(':
					left = client_message.find('(')
					right = client_message.find(')')
					if right == -1:
						self.send_message(client_socket, 'Invalid Command')
					else:
						send_list = client_message[left+1:right].split()
						s_msg = client_message[right+2:]
						if s_msg == '':
							self.send_message(client_socket, 'Invalid Command')
						else:
							self.send(client_socket, send_list, s_msg)
				else:
					c_msg = client_message.split()
					if len(c_msg) < 3:
						self.send_message(client_socket, 'Invalid Command')
					else:
						rcv_er = client_message.split()[1]
						s_msg = client_message[6+len(rcv_er):]
						self.send(client_socket, [rcv_er], s_msg)
			else:
				self.send_message(client_socket, 'Invalid Command')



	def auto_logout(self, socket):
		name = self.socket_list[socket]
		if time.time() - self.users[name]['activetime'] > Server.TIME_OUT:
			self.users[name]['online'] = False
			self.users[name]['logouttime'] = time.time()
			self.users[name]['socket'] = None
			respond = name + ': Auto Log Out'
			self.send_message(socket, respond)
			del self.socket_list[socket]
			socket.close()



	def send(self, socket, user_list, message):
		name = self.socket_list[socket]
		for user in user_list:
			if user not in self.users:
				back_msg = name + ': Failed send to '+ user +'. Invalid user object.'
				self.send_message(socket, back_msg)
			else:
				if self.users[user]['online']:
					self.send_message(self.users[user]['socket'], name+': '+message)


	def broadcast(self, socket, message):
		name = self.socket_list[socket]
		for user in self.users:
			if self.users[user]['online'] and user != name:
				self.send_message(self.users[user]['socket'], name+': '+message)
		print name, ': broadcast DONE.'

	def last(self, socket, number):
		name = self.socket_list[socket]
		name_list = ''
		curr_time = time.time()
		last_time = curr_time - number * 60
		for user in self.users:
			if self.users[user]['online']:
				name_list += user + ' '
			elif self.users[user]['logouttime']:
				if self.users[user]['logouttime'] > last_time:
					name_list += user + ' '
		self.send_message(socket, name_list)
		print name, ": last result:", name_list


	def who(self, socket):
		name = self.socket_list[socket]
		name_list = ''
		for user in self.users:
			if self.users[user]['online']:
				name_list += user + ' '
		self.send_message(socket, name_list)
		print name, ": who result:", name_list

	def logout(self, socket):
		name = self.socket_list[socket]
		self.users[name]['online'] = False
		self.users[name]['logouttime'] = time.time()
		respond = name + ' : Log Out. DONE'
		self.send_message(socket, respond)
		self.users[name]['socket'] = None
		del self.socket_list[socket]
		socket.close()
		print respond


	def send_message(self, socket, data):
		try:
			socket.sendall(data)
		#except socket.error, e:
		except Exception, (error, message):
			print 'Error sending data. Exiting...'
			sys.exit()

	def receive_message(self, socket):
		try:
			buf = socket.recv(1024)
		#except socket.error, e:
		except Exception, (error, message):
			print 'Error receiving data. Exiting...'
			sys.exit()
		return buf


	def login(self, client_socket, client_addr):
		try_count = 0
		flag = 1
		while try_count < 3:
			#print self.users
			client_message = self.receive_message(client_socket).split(' ') 
			if client_message:
				client_name = client_message[0]
				client_pw = client_message[1]
				print 'Client', client_name, 'try to login. ', try_count
				# check if the username is in the list
				if client_name not in self.users.keys():
					check_msg1 = 'Failed. Username Not Found.' 
					self.send_message(client_socket, check_msg1)
					#print check_msg1
					client_socket.close()
					break
				# check if the user is online
				if self.users[client_name]['online']:
					check_msg2 = 'Failed. Client ' + client_name + ': Already online.'
					self.send_message(client_socket, check_msg2) 
					#print check_msg2
					client_socket.close()
					break
				#check if the user is blocked
				if self.users[client_name]['block']:
					if time.time() - self.users[client_name]['blocktime'] > Server.BLOCK_TIME:
						self.users[client_name]['block'] = False
					else:
						check_msg3 = 'Failed. Client ' + client_name + ': is blocked. Cannot login.'
						self.send_message(client_socket, check_msg3)
						#print check_msg3  
						client_socket.close()
						break
				# valid password, welcome
				if self.users[client_name]['password'] == client_pw:
					flag = 0
					wel_msg = 'Welcome, ' + client_name
					self.send_message(client_socket, wel_msg)
					#print wel_msg
					self.users[client_name]['online'] = True
					self.users[client_name]['activetime'] = time.time()
					self.users[client_name]['socket'] = client_socket
					self.socket_list[client_socket] = client_name
					#break
					return 1
				# invalid password, try again or close socket
				if self.users[client_name]['password'] != client_pw:
					try_count += 1

					if try_count == 3:  # if tried for 3 times and failed, block the user
						check_msg4 = 'Failed. Client ' + client_name + ' tried more than 3 times.'
						self.users[client_name]['block'] = True
						self.users[client_name]['blocktime'] = time.time()
						self.send_message(client_socket, check_msg4)
						client_socket.close()
						#print check_msg4
					else:
						check_msg5 = 'Invalid password. Try again'
						self.send_message(client_socket, check_msg5)
					#print check_msg5

		return 0


						
			




def main():
	if len(sys.argv) > 1:
		port = int(sys.argv[1])
	else:
		port = 4119
	newS = Server()
	#newS.load()
	#newS.create_socket(port)
	newS.server(port) 

	
if __name__ == '__main__':
	main()
