import os
import socket  
import sys
import time
import select
#from threading import Thread
import struct

class Sender:
	MSS = 576 					# value for the maximum segment size
	HEADER_FORMAT = 'HHiibbHHH'	# header format
	alpha = 0.125				# parameter for RTT calculation
	beta = 0.25					# parameter for RTT calculation

	# define some info for sender to be initialized
	def __init__(self):
		self.s_udp = None		# UDP socket object for sending data
		self.s_ack = None		# TCP socket object for receiving ACK
		self.log = None			# log file for sender
		self.rcv_port = None	# receiver port number
		self.rcv_IP = None		# receiver IP address
		self.snd_port = None	# ack port number
		self.window = 1			# window size, default value is 1
		self.data = None		# data file to transmit
		self.send_data = '' 	# data to transmit
		self.est_rtt = 0		# sender should have one more output field - estimated RTT
		self.dev_rtt = 0		# default as 0
		self.sam_rtt = 0 		# sample RTT, to calculate RTT
		self.time_out = 5 		# default time out 5 seconds
		self.timer = [] 		# set timer for every packet sent
		self.total_byte = 0 	# total byte sent
		self.sent = 0 			# number for packet sent
		self.retransmitted = 0 	# number for packet retransmitted
		self.win_first = 0 		# first byte of window
		self.win_last = 0 		# last byte of window
		self.byte_first = 0 	# first byte of sending
		self.byte_last = 0 		# last byte of sending
		self.ack_prev = 0 		# previous ack number received
		self.ack_prev_count = 0 # count times of receiving of same previous ack number <for receiving 3 duplicate ACKs and retransmit>
		self.rcv_count = 0 		# used to calculate RTT
		

	# initialization of sender info 
	def init_sender(self, data_file, remote_IP, remote_port, ack_port, log_filename, window_size):
		self.rcv_IP = remote_IP	
		self.rcv_port = remote_port
		self.snd_port = ack_port
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

		if not self.data:
			print 'No avaliable data file. Exiting...'
			sys.exit()

		for line in self.data:
			self.send_data += line

		# count number of segments
		seg_num = len(self.send_data)/Sender.MSS
		if len(self.send_data)%Sender.MSS > 0:
			seg_num += 1
		# set timer for every segment
		for i in range(seg_num):
			self.timer.append(-1)

	# create socket 
	# One for sending packet(UDP), another receiving ACK(TCP) 
	def create_socket(self):
		try:
			# running on top of UDP. DGREM socket (UDP). 
			#self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			addr_info = socket.getaddrinfo(self.rcv_IP, self.rcv_port)[0]  
			self.s_udp = socket.socket(addr_info[0], socket.SOCK_DGRAM)
			#self.s_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

			s_tcp = socket.socket(addr_info[0], socket.SOCK_STREAM)
			#s_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)		
			
			# resolve OSError: [Errno 48] Address already in use may occur using socket.SO_REUSEADDR flag
			#self.s_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		except socket.error, msg:
			print 'Creating Failed. Error code:', str(msg[0]), '; Error message:', msg[1]
			sys.exit()

		try:	
			#self.s_udp.bind(('', self.snd_port))
			#s_tcp.bind((socket.gethostbyname(socket.gethostname()), self.snd_port))
			s_tcp.bind(('', self.snd_port))
		except socket.error, msg:
			print 'Binding Failed. Error code:', str(msg[0]), '; Error message:', msg[1]
			sys.exit()
		try:
			s_tcp.listen(1)
		except socket.error, msg:
			print 'Listening Failed. Error code:', str(msg[0]), '; Error message:',msg[1]
			sys.exit()

		(self.s_ack, addr) = s_tcp.accept()


	def send_and_log(self, resend_flag):
		packet = self.build_packet(self.send_data[self.byte_first:self.byte_last+1], self.byte_first, 0, 0, 0)
		self.s_udp.sendto(packet, (self.rcv_IP, self.rcv_port))
		self.timer[self.byte_first/Sender.MSS] = time.time()
		self.write_log(self.snd_port, self.rcv_port, self.byte_first, 0, 0, 0, self.est_rtt)
		self.total_byte += len(packet)
		self.sent += 1
		self.byte_first = self.byte_last + 1

		if resend_flag == 1:
			self.retransmitted += 1

		if resend_flag == 0:
			self.win_last = self.byte_last

	def send_and_resend(self):
		if self.timer[self.win_first/Sender.MSS]!=-1 and time.time()-self.timer[self.win_first/Sender.MSS]>self.time_out:
			self.win_last = self.win_first + Sender.MSS - 1
			self.byte_first = self.win_first
			self.byte_last = min(self.win_last, len(self.send_data)-1)
			self.send_and_log(1)
			print 'resend -- time out'
		
		else:
			if self.win_last - self.win_first + 1 < self.window * Sender.MSS:
				self.byte_last = min(self.byte_first+Sender.MSS-1, len(self.send_data)-1)
				if self.byte_last > self.byte_first:
					self.send_and_log(0)						
					print 'send - normal'



	# cut file to segments
	# send file data to receiver
	def send_file(self):
		seq_num = 0
		ack_num = 0 
		ack_flag = 0
		fin_flag = 0
		#print 'loop begin'
		while self.win_first < len(self.send_data):
			# time out, resend packet
			self.send_and_resend()

			#print 'wait info from receiver'
			try:
				r_list, w_list, e_list = select.select([self.s_ack],[],[])
			except select.error, e:
				print 'Select Error. Exiting...'
				break
			except socket.error, e:
				print 'Socket Error. Exiting...'
				break

			if len(r_list) > 0:

				#rcv_ack, receiver_addr = self.s_udp.recvfrom(4096)
				rcv_ack = self.s_ack.recv(4096)
				if len(rcv_ack) > 0:
					ack_header = struct.unpack(Sender.HEADER_FORMAT, rcv_ack[:20]) 
					seq_num = ack_header[2]
					ack_num = ack_header[3]
					ack_flag = ack_header[4]
					fin_flag = ack_header[5]
					self.write_log(ack_header[0],ack_header[1],ack_header[2],ack_header[3],ack_header[4],ack_header[5],self.est_rtt)
					# ACK
					if ack_flag == 1:
						print 'receive ACK'
						
						if ack_num > self.win_first:
							if ack_num!=self.ack_prev:
								self.ack_prev = ack_num
								self.ack_prev_count = 0								
							####
							self.win_first = ack_num
							# calculate RTT
							self.cal_RTT()


						elif ack_num == self.win_first:
							if ack_num == self.ack_prev: # duplicate ACK
								print 'duplicate ACK'
								self.ack_prev_count += 1
								if self.ack_prev_count >= 3: # retransmit ACKs appearing more than 3 times
									self.win_last = self.win_first + Sender.MSS - 1
									self.byte_first = self.win_first
									self.byte_last = min(self.win_last, len(self.send_data)-1)
									self.send_and_log(0)
									self.ack_prev_count = 0


	# write sender info to log file
	def write_log(self, s_port, r_port, seq_num, ack_num, ack, fin, est_rtt):
		log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		log_data = ''
		log_data += log_time+', Source: '+str(s_port)+', Destination: '+str(r_port)
		log_data += ', Seq#: '+str(seq_num)+', ACK#: '+str(ack_num)
		log_data += ', ACK: '+str(ack)+', FIN: '+str(fin)+', RTT: '+str(est_rtt)+'\n'
		self.log.write(log_data)


	# build header and calculate checksum for header
	# header includes: 
	# source port | dest port
	# sequence number
	# acknowledgment number
	# ACK | FIN | window size
	# checksum | urgent data pointer
	def build_packet(self, data, seq_num, ack_num, ack, fin):
		source_port = self.snd_port
		dest_port = self.rcv_port
		urg_ptr = 0
		rcv_window = self.window
		checksum = 0
		tcp_header = struct.pack(Sender.HEADER_FORMAT, source_port, dest_port, seq_num, ack_num, ack, fin, rcv_window, checksum, urg_ptr)
		checksum = self.cal_checksum(tcp_header+data)
		tcp_header = struct.pack(Sender.HEADER_FORMAT, source_port, dest_port, seq_num, ack_num, ack, fin, rcv_window, checksum, urg_ptr)
		return tcp_header+data

		#self.s_udp.sendto(tcp_header+data, (self.rcv_IP, self.rcv_port)) 

	# calculate RTT 
	# set alpha to 0.125, set beta to 0.25
	def cal_RTT(self):
		if self.rcv_count==0:
			self.est_rtt = time.time() - self.timer[(self.win_first-Sender.MSS)/Sender.MSS]
		if self.rcv_count==1:
			self.sam_rtt = time.time() - self.timer[(self.win_first-Sender.MSS)/Sender.MSS]
			self.dev_rtt = abs(self.sam_rtt-self.est_rtt)
			self.est_rtt = (self.est_rtt+self.sam_rtt)/2
		if self.rcv_count>1:
			self.sam_rtt = time.time() - self.timer[(self.win_first-Sender.MSS)/Sender.MSS]
			self.est_rtt = (1 - Sender.alpha) * self.est_rtt + Sender.alpha * self.sam_rtt
			self.dev_rtt = (1 - Sender.beta) * self.dev_rtt + 0.25 * abs(self.sam_rtt - self.est_rtt)
			self.time_out = self.est_rtt + 4 * self.dev_rtt
		self.rcv_count += 1


	# calculate checksum for packet
	# iterate each two and sum byte value
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


	# close connection by fin request
	def send_fin(self):
		data = ''
		fin_packet = self.build_packet(data,0,0,0,1)
		self.s_udp.sendto(fin_packet,(self.rcv_IP, self.rcv_port))
		self.write_log(self.snd_port, self.rcv_port, 0, 0, 0, 1, self.est_rtt)
		close_time = time.time()
		while time.time()-close_time <= self.est_rtt*4:
			r_list, w_list, e_list = select.select([self.s_ack],[],[])
			if len(r_list) > 0:
				#rcv_fin_packet, rcv_addr = self.s_udp.recvfrom(4096)
				rcv_fin_packet = self.s_ack.recv(4096)
				if len(rcv_fin_packet) > 0:
					fin_header = struct.unpack(Sender.HEADER_FORMAT, rcv_fin_packet[:20])
					self.write_log(fin_header[0],fin_header[1],fin_header[2],fin_header[3],fin_header[4],fin_header[5],self.est_rtt)
					ack_flag = fin_header[4]
					fin_flag = fin_header[5]
					if ack_flag==1 and fin_flag==1:
						break

		print 'Delivery completed successfully'
		print 'Total bytes sent =', self.total_byte
		print 'Segments sent =', self.sent
		print 'Segments retransmitted =', float(self.retransmitted) / float(self.sent) * 100, '%'
		#self.s_udp.close()		


	# the main part for sender class
	# send packets to receiver
	def sender(self, data_file, remote_IP, remote_port, ack_port, log_file, window_size):
		try:
			self.init_sender(data_file, remote_IP, remote_port, ack_port, log_file, window_size)
		
			self.create_socket()
			self.send_file()
			#print 'send_file end'
			self.send_fin()
			self.data.close()
			self.log.close()
		except KeyboardInterrupt:
			print 'KeyboardInterrupt (Ctrl+C). Stop Sender.'
			self.s_udp.close()
			self.s_ack.close()
			sys.exit()

		self.s_udp.close()
		self.s_ack.close()

	
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


