import sys
import os
import time
import socket
import struct
import select


class Receiver:
	HEADER_FORMAT = 'HHiibbHHH'

	# initial data for Receiver class
	def __init__(self):
		self.s_udp = None		# UDP socket object
		self.s_ack = None		# TCP socket object
		self.rcv_port = None	# listen port
		self.snd_port = None	# sender port
		self.snd_IP = None		# sender IP
		self.log = None			# receiver log file
		self.data = None		# receiver data file
		self.window = 1 		# window size. default 1
		self.seq_want  = 0 		# wanted sequence number
		#self.data_seq_num = 0 	# don't need this


	# initialization of sender info 
	# almost the same as init_sender
	def init_receiver(self, filename, listen_port, sender_IP, sender_port, log_filename):
		self.snd_IP = sender_IP
		self.snd_port = sender_port
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


	# create socket using sender IP and port number
	# almost the same as create_socket function in Sender class
	def create_socket(self):
		try:
			# running on top of UDP. DGREM socket (UDP). 
			#self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			addr_info = socket.getaddrinfo(self.snd_IP, self.snd_port)[0]

			self.s_udp = socket.socket(addr_info[0], socket.SOCK_DGRAM)
			#self.s_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			#self.s_udp.bind((socket.gethostbyname(socket.gethostname()), self.rcv_port))
			self.s_udp.bind(('', self.rcv_port))

			self.s_ack = socket.socket(addr_info[0], socket.SOCK_STREAM)
			#self.s_ack = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.s_ack.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.s_ack.connect((self.snd_IP, self.snd_port))

			
			#self.s_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		except socket.error, msg:
			print 'Creating Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
			sys.exit()

		#try:	
		#	self.s_udp.bind(('', self.rcv_port))
		#except socket.error, msg:
		#	print 'Binding Failed. Error code:', str(msg[0]), ' ; Error message:', msg[1]
		#	sys.exit()


	def receive_file(self):

		try:
			while 1:
				#read_list, write_list, error_list = select.select([0, self.s], [], [])
				#print 'wait file data'

				try:
					read_list, write_list, error_list = select.select([self.s_udp], [], [], 0)
				except select.error, e:
					print 'Select Error. Exiting...'
					break
				except socket.error, e:
					print 'Socket Error. Exiting...'
					break
				#print 'wait done'
				if len(read_list) > 0:
					rcv_data, sender_addr = self.s_udp.recvfrom(4096)
					if len(rcv_data) > 0:
						rcv_header = struct.unpack(Receiver.HEADER_FORMAT, rcv_data[:20])
						data = rcv_data[20:]
						ack_flag = rcv_header[4]
						fin_flag = rcv_header[5]
						checksum = rcv_header[7]
						#print 'rcv header =',rcv_header
						#print data
						check_header = struct.pack(Receiver.HEADER_FORMAT,rcv_header[0],rcv_header[1],rcv_header[2],rcv_header[3],rcv_header[4],rcv_header[5],rcv_header[6],0,rcv_header[8])
						check_checksum = self.cal_checksum(check_header+data)
						#print 'calculated checksum: ',check_checksum
						self.write_log(rcv_header[0],rcv_header[1],rcv_header[2],rcv_header[3],rcv_header[4],rcv_header[5])
						
						if checksum == check_checksum:
							# receive fin, to disconnect
							if fin_flag == 1:
								#print 'receive fin'
								self.send_fin()
								print 'Delivery completed successful.'
								self.data.close()
								self.log.close()
								self.s_udp.close()
								self.s_ack.close()
								sys.exit()
							# send ack
							else:
								seq_num = rcv_header[2]
								ack_num = rcv_header[3]
								if seq_num == self.seq_want:
									#print 'seq want. write data.'
									#self.data_seq_num += len(data)
									self.data.write(data)
									self.seq_want = seq_num+len(data)
								self.send_ack(self.seq_want)


				#rcv_data, sender_addr = self.s_udp.recvfrom(4096)
				#self.data.write(rcv_data)
				#self.log.write('receive data')

		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Receiver.'
			self.s_udp.close()
			self.s_ack.close()
			sys.exit()

		self.s_udp.close()
		self.s_ack.close()


	# build header and calculate checksum for header
	# reuse function in Sender class
	def build_packet(self, data, seq_num, ack_num, ack, fin):
		source_port = self.rcv_port
		dest_port = self.snd_port
		urg_ptr = 0
		rcv_window = self.window
		checksum = 0
		tcp_header = struct.pack(Receiver.HEADER_FORMAT, source_port, dest_port, seq_num, ack_num, ack, fin, rcv_window, checksum, urg_ptr)
		checksum = self.cal_checksum(tcp_header+data)
		tcp_header = struct.pack(Receiver.HEADER_FORMAT, source_port, dest_port, seq_num, ack_num, ack, fin, rcv_window, checksum, urg_ptr)
		return tcp_header+data


	# write the log file
	# reuse function in Sender class
	def write_log(self, s_port, r_port, seq_num, ack_num, ack, fin):
		log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		log_data = ''
		log_data += log_time+', Source: '+str(s_port)+', Destination: '+str(r_port)
		log_data += ', Seq#: '+str(seq_num)+', ACK#: '+str(ack_num)
		log_data += ', ACK: '+str(ack)+', FIN: '+str(fin)+'\n'
		self.log.write(log_data)


	# close connection by fin request
	# reuse function in Sender class
	def send_fin(self):
		data = ''
		fin_packet = self.build_packet(data,0,0,1,1)
		#self.s_udp.sendto(fin_packet,(self.snd_IP, self.snd_port))
		self.s_ack.send(fin_packet)
		self.write_log(self.rcv_port, self.snd_port, 0, 0, 1, 1)

	# send ack to sender
	def send_ack(self, ack_num):
		data = ''
		ack_packet = self.build_packet(data,0,ack_num,1,0)
		#self.s_udp.sendto(ack_packet,(self.snd_IP, self.snd_port))
		self.s_ack.send(ack_packet)
		self.write_log(self.rcv_port, self.snd_port, 0, ack_num, 1, 0)

	# calculate checksum for packet
	# iterate each two and sum byte value
	# reuse function in Sender class
	def cal_checksum(self, data):
		data_len = len(data)
		if (data_len & 1):
			data_len -= 1
			the_sum = ord(data[data_len])
		else:
			the_sum = 0
		while data_len > 0:
			data_len -= 2
			the_sum += (ord(data[data_len+1])<<8) + ord(data[data_len])
		the_sum = (the_sum >> 16) + (the_sum & 0xffff)
		the_sum = (~the_sum) & 0xffff
		return (the_sum>>8) | ((the_sum & 0xff)<<8)	


	def receiver(self, filename, listen_port, sender_IP, sender_port, log_file):
		try:
			self.init_receiver(filename, listen_port, sender_IP, sender_port, log_file)	
			self.create_socket()
			self.receive_file()
			self.log.close()
			self.data.close()

		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Receiver.'
			self.s_udp.close()
			self.s_ack.close()
			sys.exit()

		self.s_udp.close()
		self.s_ack.close()

	
def main():
	if len(sys.argv) == 6:
		filename = sys.argv[1]
		sender_IP = sys.argv[3]
		log_file = sys.argv[5]
		# port number should be integer
		try:
			listen_port = int(sys.argv[2])
			sender_port = int(sys.argv[4])
		except ValueError:
			print 'Invalid Command. Exiting...'
			sys.exit()
	else: # clarify the usage of Receiver.py.
		print 'Usage: python receiver.py <filename> <listening_port> <sender_IP> <sender_port> <log_filename>'

	newR = Receiver()
	newR.receiver(filename, listen_port, sender_IP, sender_port, log_file)


if __name__ == '__main__':
	main()


