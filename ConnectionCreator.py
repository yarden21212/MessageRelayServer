import socket
import uuid

import ServerOperations
import Database

HOST = ''
VERSION = 2

# https://realpython.com/python-sockets/ For python sockets understanding
# https://discord.com/channels/267624335836053506/1468512436301725706 for more info


def create_connection(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((HOST, port))
            try:
                sock.listen()
                print("Listening to the network, waits for a connection...")

                database = Database.Database()
                database.create_table()

                # FIX: removed "VERSION = 2" here
                # Why: VERSION is already global and equal to 2

            except OSError:
                print("Could not connect to the network, server's listening error")
                return  # FIX
                # Why: if listen/setup failed, stop the function cleanly

            # FIX: outer loop for accepting clients repeatedly
            while True:
                conn, addr = sock.accept()
                print("Connected by", addr)

                with conn:
                    # FIX: removed connection_closed = False
                    # Why: it was unused

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

                        if code == 700 and payload_size != 415:
                            print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
                            conn.sendall(ServerOperations.build_failure_response(version))
                            break  # FIX
                            # Why: with conn: will close the socket automatically, no need for conn.close()

                        elif code == 701 and payload_size != 0:
                            print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
                            conn.sendall(ServerOperations.build_failure_response(version))
                            break  # FIX

                        elif code == 702 and payload_size != 16:
                            print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
                            conn.sendall(ServerOperations.build_failure_response(version))
                            break  # FIX

                        # 3) Read payload
                        payload = b''
                        if payload_size > 0:
                            print("Here: payload_size > 0")
                            payload = ServerOperations.read_exactly_n_bytes_from_socket(payload_size, conn, payload)
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
                                    username, public_key = ServerOperations.register_operation_handler(payload, payload_size)
                                    db_response, new_user_uuid = database.register_user(username, public_key)
                                    response_code = ServerOperations.check_db_registration_response(db_response, new_user_uuid)

                                    if response_code == 2100:
                                        payload = new_user_uuid
                                        response_header = ServerOperations.build_success_response(
                                            VERSION, response_code, len(payload)
                                        )
                                        data = response_header + payload
                                    else:
                                        response_header = ServerOperations.build_failure_response(VERSION)
                                        data = response_header

                                    print(len(data))
                                    conn.sendall(data)

                                except Exception as e:
                                    print("[Error]", e)
                                    data = ServerOperations.build_failure_response(VERSION)
                                    print(len(data))
                                    conn.sendall(data)

                            elif code == 701:
                                server_response_code, members_list = ServerOperations.get_members_list_request(
                                    client_id, payload, payload_size, database
                                )

                                if server_response_code == 2101:
                                    payload = b''
                                    for member in members_list:
                                        member_client_id, username = member
                                        member_in_byte = username.encode("ascii") + b'\0'
                                        padding_member_in_byte = member_in_byte + b'\0' * (255 - len(member_in_byte))
                                        payload += member_client_id + padding_member_in_byte

                                    payload_size = len(payload)
                                    header = ServerOperations.build_success_response(VERSION, server_response_code, payload_size)
                                    data = header + payload

                                else:
                                    header = ServerOperations.build_failure_response(VERSION)
                                    data = header

                                print("data size:", len(data))
                                print("header size:", len(header), " | ", "payload size:", len(payload))
                                conn.sendall(data)

                            elif code == 702:
                                print("PUBLIC KEY REQUEST received")
                                server_response_code, target_public_key = ServerOperations.get_user_public_key(
                                    client_id, payload, payload_size, database
                                )

                                if server_response_code == 2102:
                                    target_client_id = payload
                                    payload_to_send = target_client_id + target_public_key
                                    header = ServerOperations.build_success_response(
                                        VERSION, server_response_code, len(payload_to_send)
                                    )
                                    data = header + payload_to_send
                                else:
                                    header = ServerOperations.build_failure_response(VERSION)
                                    data = header

                                conn.sendall(data)

                            elif code == 703:
                                print("Send MESSAGE WITH TYPE REQUEST")
                                response_code, message_id = ServerOperations.send_message_to_client(
                                    client_id, payload, payload_size, database
                                )

                                if response_code == 2103:
                                    respond_payload = payload[0:16] + message_id.to_bytes(4, "little")
                                    respond_header = ServerOperations.build_success_response(
                                        VERSION, response_code, len(respond_payload)
                                    )
                                    data = respond_header + respond_payload
                                else:
                                    respond_header = ServerOperations.build_failure_response(VERSION)
                                    data = respond_header

                                conn.sendall(data)

                            elif code == 704:
                                print("Debug 1")
                                data = b""

                                if payload_size != 0 and len(payload) != 0:
                                    print("Debug 2.1")
                                    print("Invalid payload given by the client. Payload needs to be empty!")
                                    data = ServerOperations.build_failure_response(VERSION)

                                print("Debug 2.2")
                                response_code, records_list = ServerOperations.retrieve_hanging_messages(client_id,
                                                                                                   database)
                                print("Debug 3")
                                data = b""
                                print("Debug 3.1")
                                print("debug response:", response_code)
                                if response_code == 9000:
                                    print("Debug 4.1")
                                    print("Invalid payload given OR len(payload) != payload_size")
                                    data = ServerOperations.build_failure_response(VERSION)
                                print("Debug 4.2")
                                if response_code == 2104:

                                    payload = b""
                                    for record in records_list:
                                        print("Debug 5")
                                        payload += record[0] + record[1] + record[2] + record[3] + record[4]

                                    header = ServerOperations.build_success_response(VERSION, response_code, len(payload))
                                    print("Debug 6")
                                    data = header + payload
                                print("Debug 7")
                                conn.sendall(data)

                            else:
                                print("Invalid REGISTER payload size")
                                print("Client disconnected.")
                                break

                        else:
                            print("Illegal code request:", code)
                            print("Client disconnected.")
                            break

    except OSError:
        print("[ConnectionCreator ERROR]:Connection refused")
        # FIX: removed "addr" from here
        # Why: if accept() never succeeded, addr does not exist yet