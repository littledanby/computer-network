## file description ##
README.txt: description for the files and functions
test.txt: test data for sending and receiving
Receiver.py: include Receiver class and run the receiver program
Sender.py: include Sender class and run the sender program

## development environment ##
Python 2.7.10

## How to run it ##
step0: run the proxy 			: ./newudpl -i <sender_addr>:* -o <receiver_addr>:<receiver_port> <some other parameters>
step1: run the sender file 		: python Sender.py <file_to_send> <remote_ip> 41192 <ack_port_num> <log_file> <window_size> (window_size is optional, and the default value is 1)
step2: run the receiver file 	: python Receiver.py <receive_file_name> <listening_port> <sender_ip> <sender_port> <log_file>

Example: run on the one computer(with emulator)
step0: ./newudpl -i 129.236.212.48:* -o 129.236.212.48:20000 -v -L7 -B5 -O8
step1: python Sender.py test.txt 129.236.212.48 41192 20001 send_log.txt 5
step2: python Receiver.py rcv.txt 20000 129.236.212.48 20001 rcv_log.txt

-i 129.236.212.48:* means input data from any port of this IP address
-o 129.236.212.48:20000 means output data to port 20000 of this IP address
-L7 means random packet loss: 7(1/100 per packet)
-B5 means bit erroe: 5(1/100000 per bit)
-O8 means out of order: 8(1/100 per packet)
41192 is default port of the proxy
20000: receiver listening port number
20001: sender ack port number

Example: run on the one computer(without emulator)
step1: python Sender.py test.txt 129.236.212.48 20000 20001 send_log.txt 5
step2: python Receiver.py rcv.txt 20000 129.236.212.48 20001 rcv_log.txt


## code description ##
Sender:
I created 2 kind of socket. One UDP socket for data transmitting, another TCP socket for receiving ACKs from receiver. Then I use the struct pack method according to my TCP segment structure. I almost did not use the window size part and urgent data pointer part. The important parameters of my TCP segment structure is sequence number, ACK number, ACk flag, SYN and FIN combined flag and checksum. I packed the header to a 20-byte with format 'HHiibbHHH', i.e. (2-2-4-4-1-1-2-2-2-byte). 
Each time I packet data in this way and check if the packet is time out. Then send or resend them to the receiver in the area of window size and at the same time waiting for ACKs from receiver. If time out happened, we resend the from oldest packet which is time out. 
After completing the data transmitting. Sender will send packet with FIN flag(1) to receiver to end the connection.

Receiver:
I also created 2 kind of socket. One UDP socket for data receiving, another TCP socket for transmitting ACKs to sender. I still use the same TCP segment structure and header format to pack the segment. Each packet by receiver has the ACK flag (1) ack number. Also, receier will calculate and update the ACK number and the sequence number expected. When the received sequence number is not receiver want. It will not respond by ACK (In the extra feature I change it to sending the duplicate ACK).
When receiving packet with FIN flag. receiver will send back a packet with ACK flag(1) and FIN flag(1) and disconnect.

# TCP segment structure
-----------------------------------------
|    source port    |  destination port |
-----------------------------------------
|            sequence number            |
-----------------------------------------
|         acknowledgment number         |
-----------------------------------------
|   ACK   | SYN_FIN |   window size     |
-----------------------------------------
|      checksum     |urgent data pointer|
-----------------------------------------
|                                       |
|                 data                  |
|                                       |
-----------------------------------------

The relationship between FIN, SYN and SYN_FIN is as follows:

SYN_FIN | FIN | SYN
---------------------
   0    |  0  |  0
   1    |  1  |  0
   2    |  0  |  1
   3    |  1  |  1


## extra feature ##
1. I add 3-way hand shaking. At first sender will send a special segment to receiver. It contains SYN flag(1) and a random choice of sender_isn in order to avoid certain security attacks. Then when receiver receives the special segment. It will send a ACK flag(1) with random choice of receiver_isn and ACK number (sender_isn+1). When sender received the propriate segment and respond by sending segment with sequence number (receiver_isn+1) and SYN flag 0. When all conditions in the 3 handshaking meets, the connection succeeds. Else the connection will close and system will exit.

2. I am not sure if the duplicate ACK is requiered or not by the assignment description. (Cause in the textbook, Fast Retransmit is included in section of Reliable Data Transfer(3.5.4)) If it's not required, it is my second feature :D. When receiver receives the segement with sequence number it doesn't want, it will send back the same ACk with the previous sent one. Sender will count the ACK it receives. When sender gets 3 duplicate ACK number, It should resend from the packet with the duplicate ACK.

3. If Fast retransmission is required. Then my second feature is I added SYN flag to the log file!

## error handling ##
1. control + C will be detected and error message will be printed, socket will be closed and system will exit.
2. socket error will be detected and error message will be printed, socket will be closed and system will exit
3. invalid instruction will be handled, run instruction will be printed and system will exit.
4. I/O error will be detected, error message will be printed and system will exit.


## known bugs ##
1. When the UDP socket of receiver is lost, the sender won't know and it might keep resending packets forever. I'm not sure what method I should use to check the UDP connection to receiver.
