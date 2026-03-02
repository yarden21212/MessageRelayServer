import socket


# Read more about sockets here: https://docs.python.org/3/library/socket.html

# Extracts the data from the tcp stream, waiting until the whole data transferred and then continue
# We enter data = b'' which is an empty byte stream, so len(data) = 0.
# The loop will continue transfer chunks of bytes until the first n bytes are transferred.
def read_exactly_n_bytes_from_socket(n: int, conn: socket.socket, data):

    try:
        while len(data) < n:
            chunk = conn.recv(n - len(data))
            if chunk == b'': #  Empty bytes object indicates that the client has disconnected.
                return None  # Connection closed
            data += chunk

        return data
    except OSError:
       print("Connection Error")
       return None


# Gets the 23 bytes data and decodes its data (like Code and PayloadSize)
def decode_header(data):
    if data is None or len(data) != 23:
        return None

    client_id = data[0:16]
    version = data[16]
    code = int.from_bytes(data[17:19], 'little')
    payload_size = int.from_bytes(data[19: 23], 'little')

    if version != 1 and version != 2:
        return None

    header = (client_id, version, code, payload_size)
    return header

# The server checks that the code given is legal (one of the given legal client's codes)
def code_checker(code: int):
    if code in legalRequests: #Registration request
        return True
    else:
        return False

# Checks that the info received from the client is in the right structure. For example: code = 110, payload has 415 bytes
def request_checker(code: int, payload_size: int, payload : bytes):
    if code == 110: #Registration request
        return validate_register_request(payload, payload_size)
    else: #TODO: missing the other options.
        return False

# Validates the given payload contains a legal sequence of data.
# Validates the payload is 415 bytes, name is in the size of 255 bytes & contains null terminator
def validate_register_request(payload: bytes, payload_size: int):
    payload_validation =  len(payload) == 415 and payload_size == 415
    if payload_validation:
        try:
            # Convert to str from bytes & check for null-terminator
            name_part = str(payload[0:255].decode('ascii')) # Name contains any null-terminator?
            null_terminator_index = name_part.find('\0')

            if null_terminator_index == -1:
                return False
            elif null_terminator_index == 0:
                return False
            else:
                return True
        except UnicodeDecodeError as e:
            print("[Decoding Error] name given contains a unicode character:", e)
            return False  # payload's name-part doesn't contain any null-terminator '\0'
    return False

# "validate_register_request" validates that null_terminator_index is not -1 or 0
def parse_register_request(payload: bytes):
    # "Try" condition confirms the string contains only ascii characters
    name_part = payload[0:255]  # Name contains any null-terminator?
    null_terminator_index = name_part.find(b'\x00')

    name_part = str(payload[0:null_terminator_index].decode('ascii'))
    public_key = payload[255:415]
    print("Name:", name_part, "Public Key:", public_key)

    return name_part, public_key



legalRequests = (110, 120, 130, 140, 150, 151, 152, 153)