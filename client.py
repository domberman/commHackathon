import socket
import getch
import struct
import select
from scapy.all import get_if_addr

myIP = get_if_addr('eth1')
print(myIP)
MY_PORT = 13117
MAGIC_COOKIE = 0xfeedbeef
BUFFER_SIZE = 1024
TEAM_NAME = '"DROP TABLE teamNames; --'
tcp_port = 0
sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sockUDP.bind(("", MY_PORT))
print("Client started, listening for offer requests...")
while True:
    try:
        data = sockUDP.recvfrom(BUFFER_SIZE)    #receive offer
        print("received packet")
    except ConnectionResetError:
        print("unable to receive offer")
        continue
    message_cookie, message_type, message_port = struct.unpack("!IbH", data[0])
    server_addr = data[1][0]
    print(f"{server_addr}, {message_port}")
    if message_cookie == MAGIC_COOKIE and message_type == 0x2:  #check offer
        print(f"Received offer from {server_addr}, {message_port} attempting to connect...​")
        try:
            sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockTCP.bind((myIP, tcp_port))
            tcp_port = sockTCP.getsockname()[1]
            sockTCP.connect((server_addr, message_port))
        except socket.timeout as e:
            print(f"exception occured while trying to connect: {e}")
            continue
        sockTCP.send(bytes(f"{TEAM_NAME}\n", "utf8"))   #send team name
        game_start = sockTCP.recv(BUFFER_SIZE).decode("utf8")  #receive game start message
        print(f"%s" % game_start)
        while True:
            try:
                ready_to_read, ready_to_write, in_error = select.select([sockTCP], [], [], 0)  #check if there are any new connections to accept
                for s in ready_to_read:
                    game_end = s.recv(BUFFER_SIZE).decode("utf8")
                    print(f"%s" % game_end)
                    break
                sockTCP.send(bytes(getch.getch(), "utf8")) #every time a key is pressed, it is sent to the server
            except BrokenPipeError or ConnectionResetError:
                print("Server disconnected, listening for offer requests...")
                break
        sockTCP.close()
    else:
        print("bad packet")
        continue