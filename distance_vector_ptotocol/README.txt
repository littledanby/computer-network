### command description ###
type “python router.py listen_port interface1 interface2 …”
use “ctrl+c” to kill a router (but do not disappear) cause later we must re-run the router by typing the same invoking sentence.

example:
python router.py 2001 192.168.0.4:2002:1 192.168.0.4:2003:5
python router.py 2002 192.168.0.4:2001:1 192.168.0.4:2003:3
python router.py 2003 192.168.0.4:2001:5 192.168.0.4:2002:3 192.168.0.4:2004:2
python router.py 2004 192.168.0.4:2003:2 

1. to change the weight on link 1-2:
first: ctrl+C at (192.168.0.4,2001)
then: ctrl+C at (192.168.0.4,2002)
next: python router.py 2001 192.168.0.4:2002:4 192.168.0.4:2003:5
and python router.py 2002 192.168.0.4:2001:4 192.168.0.4:2003:3
In this way the weight on link on 1–2 becomes 4

2. to add a new node to 1:
first: ctrl+C at (192.168.0.4,2001)
next: python router.py 2001 192.168.0.4:2002:1 192.168.0.4:2003:5 192.168.0.4:2005:1
then on another window:python router.py 2005 192.168.0.4:2001:1 
In this way a fifth router is linked to 1 and weight on link 1–5 is 1


### description of packet format ###
I use a dictionary to be sent. The first item is the type of the packet. The second item is the data to be transmitted. Its looking is in the following.
The sending messages have two types. One is the updated table, the other is the kill info (in order to re-run). Thus I concluded two types (‘update’ and ‘kill’). For the update one, I add the updated table to the second item. For the kill one, I add the id of router to be “killed” at the second item.

{‘type’:’kill’, ‘kill_id’:the id of process being killed}
{’type’:’update’, ‘table’: the updated routing table of sender}


### sample topology graph ###

1—-2
| /
 3
 |
 4
weight on link 1 to 2 is 1
weight on link 1 to 3 is 5
weight on link 2 to 3 is 3
weight on link 3 to 4 is 2
1: 127.0.0.1:2001
2: 127.0.0.1:2002
3: 127.0.0.1:2003
4: 127.0.0.1:2004

