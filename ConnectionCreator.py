import socket
import ServerOperations
import Database
import selectors

HOST = ''
VERSION = 2

sel = selectors.DefaultSelector()
database = Database.Database()

# Create the connection. Socket creation, binding to port and address and listening for clients.
# Configured as setblocking(False) so the server won't be blocked in due times.
# Support Selector module. Support multi-client connection.
def create_connection(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((HOST, port))
            try:
                sock.listen()
                print("Listening to the network, waits for a connection...")

                sock.setblocking(False)

                sel.register(sock, selectors.EVENT_READ, accept)

                database.create_table()

            except OSError:
                print("Could not connect to the network, server's listening error")
                return  # FIX

            while True:
                events = sel.select()

                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)

    except OSError as e:
        print(f"[ConnectionCreator ERROR]:Connection refused: {e}")

# Accept new clients to connect to the server. Each client won't block the server when "not in action".
# If client has nothing to send, the server can continue communicating with other clients without creating a bottleneck.
def accept(sock, mask):
    conn, addr = sock.accept()
    print("Connected by", addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

    # with conn:
    #     # while True:
    #         conn.setblocking(False)
    #         sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    try:
        data = start_application(conn, database)
        if data:
            print('echoing', repr(data), 'to', conn)
            print('Im totally here1')
            conn.send(data)
            print('Im totally here2')
        else:
            print('closing', conn)
            sel.unregister(conn)
            conn.close()
    except Exception as e:
        print("[READ ERROR]:", e)
        conn.close()

# The whole logic it-self. The heart of the server.
# Takes care of the requests (700 - 704)
def start_application(conn: socket.socket, database: Database.Database):
    server_operations = ServerOperations.ServerOperations()

    # Read the header sent from the client-side
    header_bytes = server_operations.read_exactly_n_bytes_from_socket(23, conn)
    if header_bytes is None:
        print("Client disconnected.")
        return None

    # Decode header
    header = server_operations.decode_header(header_bytes)
    if header is None:
        print("Invalid header, connection disconnected")
        return None

    client_id = header[0]
    version = header[1]
    code = header[2]
    payload_size = header[3]

    print("code:", code)
    print("payload_size:", payload_size)
    if code == 700 and payload_size != 415:
        print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
        return server_operations.build_failure_response(version)

    elif code == 701 and payload_size != 0:
        print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
        return server_operations.build_failure_response(version)

    elif code == 702 and payload_size != 16:
        print("payload_size is illegal, server disconnected. [Probably len(payload) != payload_size]")
        return server_operations.build_failure_response(version)

    # 3) Read payload
    payload = b''
    if payload_size > 0:
        print("Here: payload_size > 0")
        payload = server_operations.read_exactly_n_bytes_from_socket(payload_size, conn)
        if payload is None:
            print("Client disconnected (payload).")
            return None

    print("Debug:", "client_id(hex) =", client_id.hex(), "version =", version,
          "code =", code, "payload_size =", payload_size, "payload length =", len(payload))

    print("Debug: Payload first 16 bytes of output: ", payload[:16].hex(), "And as string:", payload[16:])

    if server_operations.code_checker(code):
        print("Code approved:")

        # REGISTER (700) request
        if code == 700:
            print("REGISTER REQUEST Received")

            try:
                username, public_key = server_operations.register_operation_handler(payload, payload_size)
                db_response, new_user_uuid = database.register_user(username, public_key)
                response_code = server_operations.check_db_registration_response(db_response, new_user_uuid)

                if response_code == 2100:
                    payload = new_user_uuid
                    response_header = server_operations.build_success_response(
                        VERSION, response_code, len(payload)
                    )
                    data = response_header + payload
                else:
                    response_header = server_operations.build_failure_response(VERSION)
                    data = response_header

                print(len(data))
                print("data to send back to the client is:", data)
                return data

            except Exception as e:
                print("[Error]", e)
                data = server_operations.build_failure_response(VERSION)
                print(len(data))
                return data

        elif code == 701:
            server_response_code, members_list = server_operations.get_members_list_request(
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
                header = server_operations.build_success_response(VERSION, server_response_code, payload_size)
                data = header + payload

            else:
                header = server_operations.build_failure_response(VERSION)
                data = header

            print("data size:", len(data))
            print("header size:", len(header), " | ", "payload size:", len(payload))
            return data

        elif code == 702:
            print("PUBLIC KEY REQUEST received")
            server_response_code, target_public_key = server_operations.get_user_public_key(
                client_id, payload, payload_size, database
            )

            if server_response_code == 2102:
                target_client_id = payload
                payload_to_send = target_client_id + target_public_key
                header = server_operations.build_success_response(
                    VERSION, server_response_code, len(payload_to_send)
                )
                data = header + payload_to_send
            else:
                header = server_operations.build_failure_response(VERSION)
                data = header

            return data

        elif code == 703:
            print("Send MESSAGE WITH TYPE REQUEST")
            response_code, message_id = server_operations.send_message_to_client(
                client_id, payload, payload_size, database
            )

            if response_code == 2103:
                respond_payload = payload[0:16] + message_id.to_bytes(4, "little")
                respond_header = server_operations.build_success_response(
                    VERSION, response_code, len(respond_payload)
                )
                data = respond_header + respond_payload
            else:
                respond_header = server_operations.build_failure_response(VERSION)
                data = respond_header

            return data

        elif code == 704:
            print("Debug 1")
            data = b""

            if payload_size != 0 and len(payload) != 0:
                print("Debug 2.1")
                print("Invalid payload given by the client. Payload needs to be empty!")
                data = server_operations.build_failure_response(VERSION)

            print("Debug 2.2")
            response_code, records_list = server_operations.retrieve_hanging_messages(client_id,
                                                                                      database)
            print("Debug 3")
            data = b""
            print("Debug 3.1")
            print("debug response:", response_code)
            if response_code == 9000:
                print("Debug 4.1")
                print("Invalid payload given OR len(payload) != payload_size")
                data = server_operations.build_failure_response(VERSION)
            print("Debug 4.2")
            if response_code == 2104:

                payload = b""
                for record in records_list:
                    print("Debug 5")
                    payload += record[0] + record[1] + record[2] + record[3] + record[4]

                header = server_operations.build_success_response(VERSION, response_code, len(payload))
                print("Debug 6")
                data = header + payload
            print("Debug 7")
            return data
        else:
            print("Invalid REGISTER payload size")
            print("Client disconnected.")
            return None

    else:
        print("Illegal code request:", code)
        print("Client disconnected.")
        return None