import socket
import uuid

import  ServerOperations
import Database

HOST = ''
VERSION = 1

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

                database = Database.Database()
                database.create_table()
                VERSION = 2
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

                    if code == 701 and payload_size != 0:
                        print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
                        conn.sendall(ServerOperations.build_failure_response(VERSION))
                        conn.close()
                    elif code == 702 and payload_size != 0:
                        print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
                        conn.sendall(ServerOperations.build_failure_response(VERSION))
                        conn.close()

                    # 3) Read payload
                    payload = b''
                    if payload_size > 0:
                        print("Here: payload_size > 0")
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
                                username, public_key = ServerOperations.register_operation_handler(payload,
                                                                                                   payload_size)
                                db_response, new_user_uuid = database.register_user(username, public_key)
                                response_code = ServerOperations.check_db_registration_response(db_response, new_user_uuid)

                                # Success response
                                if response_code == 2100:


                                    # Convert header's data to bytes & little endian
                                    version_to_bytes = VERSION.to_bytes(1, "little")
                                    success_response_code_little_endian = response_code.to_bytes(2, "little")
                                    payload = client_id
                                    payload_size_little_endian = len(payload).to_bytes(4, "little")

                                    header = version_to_bytes + success_response_code_little_endian + payload_size_little_endian
                                    data = header + payload

                                #Failure response
                                else: # success_response == 9000:

                                    header = ServerOperations.build_failure_response(VERSION)
                                    data = header
                                print(len(data))
                                conn.sendall(data)

                            except Exception as e:
                                print("[Error]", e)


                        elif code == 701:
                            server_response_code, members_list = ServerOperations.get_members_list_request(client_id, payload, payload_size, database)

                            if server_response_code == 2101:

                                # Building the payload
                                payload = b''
                                for member in members_list:
                                    member_client_id, username = member
                                    member_in_byte = username.encode("ascii") + b'\0'
                                    padding_member_in_byte = member_in_byte + b'\0' * (255 - len(member_in_byte))
                                    payload += member_client_id + padding_member_in_byte

                                payload_size = len(payload)

                                header = ServerOperations.build_success_response(VERSION, server_response_code, payload_size)

                                data = header + payload

                            else: # server_response_code = 9000

                                header = ServerOperations.build_failure_response(VERSION)
                                data = header

                            print("data size:", len(data))
                            print("header size:", len(header), " | ", "payload size:", len(payload))
                            conn.sendall(data)

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

    except OSError:
        print("Connection refused by", addr)



