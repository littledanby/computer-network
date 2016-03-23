## file description ##
README.txt: description for the files and functions
user_pass.txt: store user name and related password (already hashed)
Client.py: include Client class and run the client program
Server.py: include Server class and run the server program

## development environment ##
Python 2.7.10

## code description ##
Server:
Initially I stored password, online status, last active time, last lot out time and blocked IP and time for one user. Also I stored a list of socket combine with username for easy finding.
At first, create Server socket and listen to connections. Then I use a while loop, each time I check if there is inactive user who reaches the TIME_OUT and automatically log out the user. Then I use select to get the wait for message from users. 
One kind of message is connection request. Once receive the message, run login part for client. When client log in successfully, he could send command to server and communication with other connected users.
Another kind of message is the command from online users. Server receives the command, decides if it is valid command and run the according functions.

Client:
The client part is much simpler. What I need to do is create socket and request connection to server. This time I ask users to input username and password and I send the username and hashed password combination to server. Once logged in successfully, I also use select. Waiting messages from sys.stdin as well as socket.
once received message from stdin, I send the message to server. Once received message from socket. I firstly check if there is any instruction to ask me to close the socket. At last print the message.

## How to run it ##
1st step: python Server.py <port_number>
	port_number can be ignored and the default port number is 4119
2nd step: python Client.py <server_IP_address> <server_port_number>
	both the server_IP_address and server_port_number are required
we could do step 2 for many times

once run the server program, the server will listen for clients and wait for connection request and client command.
once run the client program, each user is asked to login with username and password. invalid name will be rejected and invalid password will result in try for at most 3 times. Once the IP address is blocked, the user could only wait for 60 seconds and then try to login again at the same IP address.

command available for clients:
1. who: display name of other connected users
2. last <number>: display name of users who connected within the last <number> of minutes
3. broadcast <message>: broadcast <message> to all connected users 
4. send (<user1> <user2> <user3> ... ) <message>: send <message> to selected users
5. send <user> <message>: send private <message> to single user
6. logout: log out this user

## extra feature command ##
7. busy: when called busy, the status of ‘busy’ is True for the user. Then the user will not receive others’ message. When other users tries to send or broadcast message to the busy user, they will receive a auto reply from the busy user.
8. idle: when called idle, the status of ‘busy’ is False for the user. Then he can receive message and auto reply is cancelled as well.

9. hide: when called hide, the status of ‘visible’ is False. In this case, this user won’t be seen by other connected users. That is, when others call ‘who’ or ‘last <number>’, they won’t see the hide user. But when they broadcast or send message to the hide target, he can get the message.
10. appear: when called appear, the status of ‘visible’ is True. In this case, this user can be seen by other connected users.

11. status: called ‘status’ to show the busy and visible status of the user

## error handling ##
1. control + C will be detected and error message will be printed, socket will be closed and system will exit.
2. socket error will be detected and error message will be printed, socket will be closed and system will exit
3. invalid input will be detected and users will be asked to input again
4. invalid instruction will be handled, run instruction will be printed and system will exit.
