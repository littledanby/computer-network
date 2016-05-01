import os
import socket
import sys
import time
import select
import json


class Router:
	TIME_OUT = 5				# default time out value: 5 seconds
	INFINITY = float('inf')		# infinity value

	def __init__(self):
		self.s = None			# socket object
		self.id = None			# host:port identification
		self.table = {}			# table[destination][via]
		#self.routing = {}		# routing table which store the min weight to destination
		self.neighbors = []		# store neighbor id
		self.logfile = None		# log file name for this router
		self.timer = None		# last time sending table to neighbors


	# send updated routing table to neighbors every 5 seconds
	def send_update(self):
		send_table = [] # table: destination_id: weight
		for destination in self.table:
			min_dist = min(self.table[destination].values())
			send_table.append([destination, min_dist])

		wrap_table = jason.dumps(send_table)
		for id in self.neighbors:
			nb_info = id.split(':')
			nb_addr = (nb_info[0], int(nb_info[1]))
			self.s.sendto(json.dumps(send_table), addr)

	# update the routing table accoding to the received data
	def update_table(self, nb_data, nb_addr):
		table = json.loads(data)
		via_id = addr[0]+':'+addr[1]


	# when ctrl C is invoked, the 
	def send_kill_info(self):
		return 0

	# write log file
	def write_log(self):
		log = open(self.logfile, 'w')

		return 0

	# main part of Router class
	def router(self, listen_port, neighbor):
		try:
			self.create_socket(listen_port)
			self.load(neighbor)
			while 1:
				# if 5 seconds comes, send updates to neighbors
				if time.time()-self.timer > Router.TIME_OUT:
					self.send_update()
					self.timer = time.time()
				# wait for update info from neighbors
				r_list, w_list, e_list = select.select([self.s],[],[],0)
				if len(r_list) > 0:
					nb_data, nb_addr = self.s.recvfrom(4096)
					if len(nb_data) > 0:
						self.update_table(nb_data, nb_addr)

		except KeyboardInterrupt:
			print 'Ctrl+C detected. Close', self.id
			#### there is something has to be done!!!!####
			self.send_kill_info()
			self.s.close()
			sys.exit()

	# load the neighbor value from system input(sys.argv)
	def load(self, neighbor):
		for interface in neighbor:
			info = interface.split(':')
			neighbor_id = info[0]+':'+info[1]
			self.neighbors.append(neighbor_id)
			#neighbor_host = info[0]
			#neighbor_port = int(inf[1])
			#self.neighbors[neighbor_id] = (neighbor_host, neighbor_port)
			neighbor_wt = int(inf[2])
			self.table[neighbor_id] = {}
			self.table[neighbor_id][neighbor_id] = neighbor_wt
		# add infinity to other links
		for dest in self.table:
			for via in self.neighbors:
				if via not in self.table[dest]:
					self.table[dest][via] = Router.INFINITY
		# send text message to peers at start-up
		self.send_update()
		# start timer
		self.timer = time.time()


	# create socket and listen to connections
	def create_socket(self, port):
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.s.bind(('', port))
		except socket.error, msg:
			print 'Failed in socket. Exiting...'
			sys.exit()

		host = socket.gethostbyname(socket.gethostname())
		self.id = host+':'+str(port)
		self.logfile = str(port)
		



def main():
	if len(sys.argv) < 3:
		print 'Usage: python router.py listen_port interface1 interface2 [...]'
		sys.exit()
	else:
		print 'You can type (Ctrl+C) to kill it.'
		port = sys.argv[1]
		neighbor = []
		for i in range(2,len(sys.argv)):
			neighbor.append(sys.argv[i])
		newR = Router()
		newR.router(port, neighbor)



if __name__ == "__main__":
	main()


