"""
/* Assume sender is not constrained by TCP flow or congestion control, that than MSS in size, and that 
   data transfer is in one direction only. 
*/

NextSeqNum=InitialSeqNumber
SendBase=InitialSeqNumber

loop (forever) { 
	switch(event)

	event: data received from application above
		create TCP segment with sequence number NextSeqNum 
		if (timer currently not running)
			start timer
		pass segment to IP 
		NextSeqNum=NextSeqNum+length(data) 
		break;

	event: timer timeout
		retransmit not-yet-acknowledged segment with smallest sequence number 
		start timer
		break;

	event: ACK received, with ACK field value of y 
		if (y > SendBase) 
			SendBase=y
			if (there are currently any not-yet-acknowledged segments)
				start timer 
		break;
} /* end of loop forever */

From "Computer Networking A TopDown Approach, 6th Edition"
"""

class Sender:




	
def main():
	if len(sys.argv) == 7:
		filename = sys.argv[1]
		remote_IP = sys.argv[2]
		remote_port = int(sys.argv[3])
		ack_port = int(sys.argv[4])
		log_file = sys.argv[5]
		window_size = sys.argv[6]
		
	else: # clarify the usage of Sender.py.
		print 'Usage: python Sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename> <window_size>'

if __name__ == '__main__':
	main()















