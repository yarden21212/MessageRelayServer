import socket
import ServerOperations

HOST = ''

#https://realpython.com/python-sockets/ For python sockets understanding
#https://discord.com/channels/267624335836053506/1468512436301725706 for more info


def create_connection(port):
    try:
        # - socket.socket() creates a socket object that supports the context manager type
        # - AF_INET is the Internet address family for IPv4
        # - SOCK_STREAM is the socket type for TCP, the protocol that will be used to transport messages in the network.
        # - The .bind() method is used to associate the socket with a specific network interface and port number
        # - .listen() enables a server to accept connections. It makes the server a listening socket
        # - The .accept() method blocks execution and waits for an incoming connection.
        #when a client connects, it returns a new socket object representing the connection and a tuple holding the address of the client.
        #the tuple will contain (host, port) for IPv4 connections
        # - conn is the new socket object used to communicate with the specific client
        # - .recv() reads data from the client; it blocks until data is sent or the client disconnects
        # - An empty bytes object (b'') returned by .recv() signals the client has closed the connection
        # - .sendall() ensures all data in the buffer is sent back to the client before returning
        # - The 'with' statement is used with conn to automatically close the socket at the end of the block.

        with (socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock):
            sock.bind((HOST, port))
            try:
                sock.listen()
                print("Listening to the network, waits for a connection...")
            except OSError:
                print("Could not connect to the network, server's listening error")
            conn, addr = sock.accept()
            print("Connected by", addr)

            with conn:
                connection_closed = False

                while True:
                    data = b''

                    # Read the header sent from the client-side
                    header_bytes = ServerOperations.read_exactly_n_bytes_from_socket(23, conn, data)
                    if header_bytes is None:
                        print("Client disconnected.")
                        break

                    # Decode header
                    header = ServerOperations.decode_header(header_bytes)
                    if header is None:
                        print("Invalid header, connection disconnected")
                        break

                    client_id = header[0]
                    version = header[1]
                    code = header[2]
                    payload_size = header[3]

                    # 3) Read payload
                    payload = b''
                    if payload_size > 0:
                        payload = ServerOperations.read_exactly_n_bytes_from_socket(payload_size, conn,
                                                                                                payload)
                        if payload is None:
                            print("Client disconnected (payload).")
                            break

                    print("Debug:", "client_id(hex) =", client_id.hex(), "version =", version,
                          "code =", code, "payload_size =", payload_size, "payload length =", len(payload))

                    print("Debug: Payload first 16 bytes of output: ", payload[:16].hex(), "And as string:", payload[16:])


                    if ServerOperations.code_checker(code):
                        print("Code approved:")

                        # REGISTER (700) request
                        if code == 700:
                            print("REGISTER REQUEST Received")
                            try:
                                # Validates parameters & parse the data
                                (name_part, public_key) = ServerOperations.register_operation_handler(payload,
                                                                                                      payload_size)
                            except Exception as e:
                                print("[Error]", e)


                        elif code == 701:
                            pass
                        elif code == 702:
                            pass
                        elif code == 703:
                            pass
                        elif code == 704:
                            pass

                        else:
                            print("Invalid REGISTER payload size")
                            print("Client disconnected.")
                            break


                    else:
                        print("Illegal code request:", code)
                        print("Client disconnected.")
                        break


                    #NEXT STEP TO DO:
                    # text = data.decode("utf-8")
                    # print("Received message: " + data)
                    # print("Enter message ")

                    # reply = input()
                    # replydata = bytearray(reply, "utf-8")
                    # newdata = bytearray(1024)
                    # for i in range(min(len(replydata), len(newdata))):
                    #     newdata[i] = replydata[i]
                    # conn.sendall(newdata)

    except OSError:
        print("Connection refused by", addr)

