import socket
import Database

legalRequests = (700, 701, 702, 703, 704)

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


def build_success_response(version: int, code: int, payload_size: int):

    version_to_bytes = version.to_bytes(1, "little")
    code_success_response_little_endian = code.to_bytes(2, "little")
    payload_size_little_endian = payload_size.to_bytes(4, "little")

    return version_to_bytes + code_success_response_little_endian + payload_size_little_endian

def build_failure_response(version: int = 2):
    version_bytes = version.to_bytes(1, "little")
    code_bytes = (9000).to_bytes(2, "little")
    payload_size_bytes = (0).to_bytes(4, "little")

    return version_bytes + code_bytes + payload_size_bytes

# ---------------------------------------------REGISTER REQUEST----------------------------------------------------



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
                print("[DEBUG]: validate_register_request passed!")
                return True
        except UnicodeDecodeError as e:
            print("[Decoding Error] name given contains a unicode character:", e)
            return False  # payload's name-part doesn't contain any null-terminator '\0'
    return False

# After validating the payload by "validate_register_request" method. We need to parse & get the username and public key.
# Because of "validate_register_request" we know that username contains null terminator.
def parse_register_request(payload: bytes):
    # "Try" condition confirms the string contains only ascii characters
    name_part = payload[0:255]  # Name contains any null-terminator?
    null_terminator_index = name_part.find(b'\x00')

    name_part = str(payload[0:null_terminator_index].decode('ascii'))
    print(name_part)
    public_key = payload[255:415]
    print("Name:", name_part, "Public Key:", public_key)

    print("[DEBUG]: parse_register_request passed!")
    return name_part, public_key


# Checks if payload is legal, check if the data given s successfully parsed, and returns response.
def register_operation_handler(payload: bytes, payload_size: int):
    payload_legal = validate_register_request(payload, payload_size)
    if payload_legal:
        name_part, public_key = parse_register_request(payload)

        print("[DEBUG]: register_operation_handler passed!")
        return name_part, public_key
    else:
        print("[DEBUG]: register_operation_handler failed")
        return None, None

# Check if db's response and returns response as followed:
# Response - 2100, 9000 : success, failure
def check_db_registration_response(db_response: bool, uuid):
    if db_response:
        print("DB succeed to store the new user:", uuid)
        return 2100
    else:
        print("DB failed to store the new user:")
        return 9000





# ---------------------------------------------MEMBERS LIST REQUEST----------------------------------------------------
# Get a client ID, and extract from DB a list of the other registered users in form of [ID, UserName]
# If the given client ID doesn't exist in the DB (the ID is not registered), the process will return false
def get_members_list_request(client_id: bytes, payload : bytes, payload_size: int, database: Database):

    payload_validation =  len(payload) == 0 and payload_size == 0
    try:
        client_existence = database.check_client_id_existence(client_id)

        if not payload_validation or not client_existence:
            return 9000, []
        else:
            response, users_list = database.get_members_list_without_given_id(client_id)

            # If user ID is registered and no errors occurred
            if response:
                return 2101, users_list
            else:
                return 9000, []

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return False, []










