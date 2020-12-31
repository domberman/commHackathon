import socket
import threading
import random
import struct
import time
import select
from scapy.all import get_if_addr

lock = threading.Lock() #global lock, used for communicating between threads (when to start and stop the game, etc.)

def send_offers(sock, port):     #for sending the offers through UDP
    CLIENT_PORT = 13117
    adds = get_if_addr('eth1').split(.)
    SEND_UDP_TO = adds[0] + "." + adds[1] + ".255.255"
    while True:
        if lock.locked():   #continue sending until 10 seconds have passed, then the lock will lock and func will end
            return
        sock.sendto(struct.pack("!IbH",0xfeedbeef, 0x02, port), (SEND_UDP_TO, CLIENT_PORT))
        time.sleep(1.0)

def count_keystrokes(conn, addr, names1, names2, score, num_of_teams):  #the function that handle each client
    keystrokes = 0
    while not lock.locked(): #wait until we finish accepting contestants
        time.sleep(1.0)
    group1 = ""
    for name in names1:
        group1 += f"{name}\n"   #make lists of the groups
    group2 = ""
    for name in names2:
        group2 += f"{name}\n"
    conn.send(bytes(f"Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n{group1}\nGroup 2:\n==\n{group2}\nStart!", "utf8"))    #send start of game messages to the clients
    while lock.locked():    #goes until game ends
        ready_to_read, ready_to_write, in_error = select.select([conn], [], [], 3) #check if the client has sent something
        for c in ready_to_read:
            c.recv(BUFFER_SIZE)
            keystrokes += 1
    lock.acquire()
    score[0] += keystrokes  #add the client's score to the total for its team
    num_of_teams[0] -= 1    #signal that the client finished updating the score
    lock.release()
    while num_of_teams[0] > 0:
        time.sleep(1.0)
    end_message = f"Game over!\nGroup 1 - {score1[0]}\nGroup 2 - {score2[0]}\n"  #print results and announce the winners
    if score1[0] > score2[0]:
        end_message += "Group 1 wins!"
    elif score2[0] > score1[0]:
        end_message += "Group 2 wins!"
    else:
        end_message += "It was a tie! Unbelievable!"
    conn.send(bytes(end_message, "utf8"))
    conn.close()

def count_to_ten(): #for signaling when to start and finish the game
    time.sleep(10.0)
    if lock.locked():
        lock.release()
        print("Game over, sending out offer requests...")
    else:
        lock.acquire()
        print("starting game!")

my_ip = get_if_addr('eth1')
BUFFER_SIZE = 1024
sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_port.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
udp_port.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
udp_port = 0
tcp_port = 0
sock_udp.bind((my_ip, udp_port))
udp_port = sock_udp.getsockname()[1]
team_names1 = []
team_names2 = []
score1 = [0]
score2 = [0]
num_of_teams = [0]
sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_tcp.bind((my_ip, tcp_port))
tcp_port = sock_tcp.getsockname()[1]
print(f"Server started, listening on IP address {my_ip} port {tcp_port}")
while True:
    num_of_teams[0] = 0
    score1[0] = 0
    score2[0] = 0
    team_names1 = []
    team_names2 = []
    lock = threading.Lock()
    sender = threading.Thread(target = send_offers, args = (sock_udp, tcp_port))
    sender.start()  #start sending UDP offers
    sock_tcp.listen()
    counter = threading.Thread(target = count_to_ten, args = ())
    counter.start() #start counting down to the start of the game
    while not lock.locked():    #until game starts, accept new connections
        ready_to_read, ready_to_write, in_error = select.select([sock_tcp], [], [], 3)  #check if there are any new connections to accept
        for s in ready_to_read:
            conn, addr = s.accept()
            print(f"accepted connection {addr}")
            team = random.choice([1,2]) #assign random team
            num_of_teams[0] += 1
            if team == 1:
                team_names1.append((conn.recv(BUFFER_SIZE)).decode("utf8")) #receive team name and add to the right group
                count_keys = threading.Thread(target = count_keystrokes, args = (conn, addr, team_names1, team_names2, score1, num_of_teams))
                count_keys.start()  #start the thread that handles the client
            else:
                team_names2.append((conn.recv(BUFFER_SIZE)).decode("utf8"))
                count_keys = threading.Thread(target = count_keystrokes, args = (conn, addr, team_names1, team_names2, score2, num_of_teams))
                count_keys.start()
    counter = threading.Thread(target = count_to_ten, args = ())
    counter.start() #count down to the end of the game
    while num_of_teams[0] > 0:
        time.sleep(1.0)