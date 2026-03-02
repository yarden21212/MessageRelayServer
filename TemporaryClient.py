import socket

with open ("myport.info") as file:
    port_text = file.read().strip()
try:
    if port_text:
        print("file content: ", port_text)
        port = int(port_text)
        print("port content: ", port)

        name = b"Yarden21212"
        name_length = len(name)
        name_padding = b"\0"*(255-name_length)
        public_key = b"HG@##$123512DSAASASVASFASR325325\0"
        public_key_length = len(public_key)
        public_key_padding = b"\0"*(160-public_key_length)
        payload = name + name_padding +public_key + public_key_padding
        payload_size = len(payload)
        client_id = b"\x00" * 16
        version = (1).to_bytes(1, byteorder="little")
        code = (700).to_bytes(2, byteorder="little")
        payload_size_bytes = payload_size.to_bytes(4, byteorder="little")
        header = client_id + version + code + payload_size_bytes

        print("Header length:", len(header))  # Must be 23
        print("Payload length:", len(payload))
        print("Total packet length:", len(header + payload))


        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("127.0.0.1", port))
            sock.sendall(header + payload)
            print("sent")


except socket.error:
    print("Client disconnected (payload).")