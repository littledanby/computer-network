import sys

class receiver:




def main():
	try:
		while len(sys.argv) != 5:
			print "Invalid Command. Retype command or Ctrl+C to exit."
		filename = sys
	except KeyboardInterrupt:
		print 'KeyboardInterrupt (Ctrl+C). Exiting...'
		sys.exit()

	
def main():
	if len(sys.argv) == 6:
		filename = sys.argv[1]
		listen_port = int(sys.argv[2])
		server_IP = sys.argv[3]
		server_port = sys.argv[4]
		log_file = sys.argv[5]
		newC = Client()
		newC.client(host, port)
	else: # clarify the usage of Client.py.
		print 'Usage: python receiver.py <filename> <listenging_port> <server_IP> <server_port> <log_filename>'

if __name__ == '__main__':
	main()