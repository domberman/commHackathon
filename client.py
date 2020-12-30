import socket
import getch
import struct
import select

myIP = "localhost"
MY_PORT = 13117
MAGIC_COOKIE = 0xfeedbeef
BUFFER_SIZE = 1024
TEAM_NAME = '"DROP TABLE teamNames; --'
sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockUDP.bind((myIP, MY_PORT))
print("Client started, listening for offer requests...")
while True:
    try:
        data = sockUDP.recvfrom(BUFFER_SIZE)    #receive offer
    except ConnectionResetError:
        print("unable to receive offer")
        continue
    message_cookie, message_type, message_port = struct.unpack("Ibh", data[0])
    server_addr = data[1][0]
    print(f"{server_addr}, {message_port}")
    if message_cookie == MAGIC_COOKIE and message_type == 0x2:  #check offer
        print(f"Received offer from {server_addr}, {message_port} attempting to connect...​")
        try:
            sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockTCP.bind((myIP, 3000))
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