# A file to check my server, no need to be checked. Totally irrelevant.
# Will be deleted once the project is done.

import socket
import struct
import DisplayDifferentResponses

with open("myport.info") as file:
    port_text = file.read().strip()

try:
    if port_text:
        print("file content: ", port_text)
        port = int(port_text)
        print("port content: ", port)

        # 1 ClientID
        hex_client_id = "6CE8B00899BA48568B3FC26F88A2531D"
        client_id_bytes = bytes.fromhex(hex_client_id)

        # 2 Version
        version = 2
        version_to_bytes = version.to_bytes(1, byteorder="little")


        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("127.0.0.1", port))
            while True:
                # 3 Code
                code = input("Enter your code: ")

                payload_size_bytes = b""
                payload = b""
                print("Client ID:", client_id_bytes, "Version:", version, "Code:", code)

                if code == "exit":
                    break

                code_int = int(code)
                code_to_bytes = code_int.to_bytes(2, byteorder="little")

                if code not in ("700", "701", "702", "703", "704"):
                    print("Invalid request code.")
                    continue

                if code == "700":
                    name = b"Yarden21212"
                    name_length = len(name)
                    name_padding = b"\0" * (255 - name_length)

                    public_key = b"HG@##$123512DSAASASVASFASR325325\0"
                    public_key_length = len(public_key)
                    public_key_padding = b"\0" * (160 - public_key_length)

                    payload = name + name_padding + public_key + public_key_padding
                    payload_size_bytes = len(payload).to_bytes(4, byteorder="little")

                elif code == "701":
                    payload = b""
                    payload_size_bytes = (0).to_bytes(4, byteorder="little")

                elif code == "702":
                    target_client_id = "13D66E18CE14410FABE2E51EFDD25E81"
                    target_client_id_bytes = bytes.fromhex(target_client_id)

                    payload = target_client_id_bytes
                    payload_size_bytes = len(payload).to_bytes(4, byteorder="little")

                elif code == "703":
                    payload = b""
                    message_type = input("Enter your message_type: ")
                    message_type = int(message_type)
                    if message_type not in (1, 2, 3, 4):
                        print("Invalid message type.")
                        continue
                    else:
                        message_type_to_bytes = message_type.to_bytes(1, byteorder="little")
                        # Target's CLIENT ID:
                        target_client_id = "CA1ABFC1B8BD46AA8E59C04B75C8331B"
                        target_client_id_bytes = bytes.fromhex(target_client_id)

                        if message_type == 1:
                            content = b""
                            content_size = len(content).to_bytes(4, byteorder="little")
                            payload = target_client_id_bytes + message_type_to_bytes + content_size + content
                        elif message_type == 2:
                            content = b"FAKE_ENCRYPTED_SYMMETRIC_KEY"
                            content_size = len(content).to_bytes(4, byteorder="little")
                            payload = target_client_id_bytes + message_type_to_bytes + content_size + content
                        elif message_type == 3:
                            content = "Hello World! My name is Yarden21212."
                            content = content.encode("ascii")
                            content_size = len(content).to_bytes(4, byteorder="little")
                            payload = target_client_id_bytes + message_type_to_bytes + content_size + content
                        elif message_type == 4:
                            content = b"FAKE_ENCRYPTED_FILE_CONTENT"
                            content_size = len(content).to_bytes(4, byteorder="little")
                            payload = target_client_id_bytes + message_type_to_bytes + content_size + content

                        payload_size_bytes = len(payload).to_bytes(4, byteorder="little")
                elif(code == "704"):
                    payload = b""
                    payload_size_bytes = (0).to_bytes(4, byteorder="little")


                header = client_id_bytes + version_to_bytes + code_to_bytes + payload_size_bytes

                print("Header length:", len(header))  # Must be 23
                print("Payload length:", len(payload))
                print("Total packet length:", len(header + payload))

                print("------------------------------------------------------------------------------")
                print("header: ", header)
                print("payload: ", payload)
                print("------------------------------------------------------------------------------")

                sock.sendall(header + payload)
                print("sent")

                header = DisplayDifferentResponses.read_exactly(sock, 7)
                payload_size = struct.unpack("<BHI", header)[2]
                payload = DisplayDifferentResponses.read_exactly(sock, payload_size)
                data = header + payload

                if not data:
                    print("Server closed the connection.")
                    break

                responses = DisplayDifferentResponses.DisplayDifferentResponses()

                request_code = code
                response_code = int.from_bytes(data[1:3], "little")

                print("\nRequest code:", request_code)
                print("Response code:", response_code)

                print("\n================ RAW RESPONSE =================")
                print(data)
                print("===============================================")

                if request_code == "701":
                    responses.display701(data)

                elif request_code == "704":
                    print("\n================ PARSED MESSAGES ===============")
                    DisplayDifferentResponses.parse_2104_response(data)


                code = int.from_bytes(data[1:3], "little")
                print(f"Response code:", code)

except ValueError:
    print("Invalid input.")
except socket.error:
    print("Client disconnected (payload).")