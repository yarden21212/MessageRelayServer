# --------------------------- TOTALLY IGNORE IT, SUPPOSE TO BE DELETED! NOT PART OF THE PROJECT, JUST FOR TESTING
# FOR TEMPORARY CLIENT, ITS NOT MY CODE! IF I DIDN'T DELETE IT SO JUST IGNORE IT-------------------------
import struct
class DisplayDifferentResponses:

    @staticmethod
    def display701(data: bytes):

        if len(data) < 7:
            print("Invalid response")
            return

        version = data[0]
        code = int.from_bytes(data[1:3], "little")
        payload_size = int.from_bytes(data[3:7], "little")

        print("Version:", version)
        print("Response code:", code)
        print("Payload size:", payload_size)

        if code != 2101:
            print("Request failed")
            return

        payload = data[7:7 + payload_size]

        record_size = 271
        users_count = payload_size // record_size

        print("Users found:", users_count)

        for i in range(users_count):
            start = i * record_size
            record = payload[start:start + record_size]

            client_id = record[0:16]
            username_field = record[16:271]

            null_index = username_field.find(b'\0')
            username = username_field[:null_index].decode("ascii")

            print("User", i + 1)
            print("Client ID:", client_id.hex())
            print("Username:", username)
            print()


def read_exactly(sock, n):
    data = b""

    while len(data) < n:
        chunk = sock.recv(n - len(data))

        if not chunk:
            raise ConnectionError("Socket closed before receiving enough data")

        data += chunk

    return data


def receive_full_response(sock):
    # Response header = 7 bytes:
    # Version   = 1 byte
    # Code      = 2 bytes
    # PayloadSz = 4 bytes
    header = read_exactly(sock, 7)

    version, code, payload_size = struct.unpack("<BHI", header)

    payload = read_exactly(sock, payload_size)

    return header + payload


def parse_2104_response(data: bytes):
    if len(data) < 7:
        raise ValueError("Response too short to contain header")

    version, code, payload_size = struct.unpack("<BHI", data[:7])

    print("=" * 80)
    print(f"Version      : {version}")
    print(f"Code         : {code}")
    print(f"Payload Size : {payload_size}")
    print("=" * 80)

    payload = data[7:]

    if len(payload) != payload_size:
        print(f"[Warning] Header payload size = {payload_size}, actual payload size = {len(payload)}")

    offset = 0
    message_index = 1

    while offset < len(payload):
        # Fixed part of one notification:
        # 16 + 4 + 1 + 4 = 25 bytes
        if offset + 25 > len(payload):
            print(f"[Warning] Remaining bytes are too short for another full message at offset {offset}")
            break

        client_id = payload[offset:offset + 16]
        offset += 16

        message_id = struct.unpack("<I", payload[offset:offset + 4])[0]
        offset += 4

        message_type = payload[offset]
        offset += 1

        message_size = struct.unpack("<I", payload[offset:offset + 4])[0]
        offset += 4

        if offset + message_size > len(payload):
            print(f"[Warning] Content of message {message_index} goes past payload boundary")
            break

        content_bytes = payload[offset:offset + message_size]
        offset += message_size

        try:
            content_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_text = content_bytes.decode("utf-8", errors="replace")

        print(f"Message #{message_index}")
        print(f"  Client ID    : {client_id.hex().upper()}")
        print(f"  Message ID   : {message_id}")
        print(f"  Message Type : {message_type}")
        print(f"  Message Size : {message_size}")
        print(f"  Content      : {content_text}")
        print("-" * 80)

        message_index += 1