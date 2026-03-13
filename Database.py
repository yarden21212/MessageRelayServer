import sqlite3
import sys
import uuid
import datetime
import struct


# Read more about:
# datetime library here: https://docs.python.org/3/library/datetime.html
# Sqlite exceptions handling:
# https://www.zetcode.com/python/sqlite3-error/
# https://www.pythonlore.com/handling-sqlite3-database-exceptions-and-errors/
class Database:
    def __init__(self, db_path="defensive.db"):
        self.path = db_path

    # Table creation:
    # Create 2 different tables (in case do not exist):
    # A table for clients' data & a table for messages (to client and from whom)
    def create_table(self):

        with sqlite3.connect(self.path) as conn:
            conn.executescript("""
                                CREATE TABLE IF NOT EXISTS clients
                                (
                                    ID BLOB PRIMARY KEY,
                                    UserName TEXT UNIQUE NOT NULL,
                                    PublicKey BLOB NOT NULL,
                                    LastSeen TEXT NOT NULL
                                );

                                CREATE TABLE IF NOT EXISTS messages
                                (
                                    ID INTEGER PRIMARY KEY,
                                    ToClient BLOB NOT NULL,
                                    FromClient BLOB NOT NULL,
                                    Type INTEGER NOT NULL,
                                    Content BLOB NOT NULL
                                );
                               """)
            conn.commit()

    # Register a new user.
    # Each user gets a unique ID (UUID) and store Username & Public key
    def register_user(self, username: str, publickey: bytes):
        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.cursor()

                new_uuid = uuid.uuid4().bytes  # Conversion to bytes (16 bytes as requested)
                last_seen = str(datetime.datetime.now(datetime.timezone.utc))

                cur.execute("INSERT INTO clients(ID, UserName, PublicKey, LastSeen) VALUES(?,?,?,?)"
                            , [new_uuid, username, publickey, last_seen])

                conn.commit()
                print(f"[{new_uuid.hex()}] User {username} registered successfully.")

                return True, new_uuid

        except sqlite3.IntegrityError as e:
            print("Username with the given name already exists in the database.")
            return False, None
        except sqlite3.OperationalError as e:
            # Two processes accessing the same database. The second process fails  it can't acquire a lock.
            print(f"Database locked error: {e}")
        except sqlite3.Error as e:
            print(f"Unexpected database error occurred: {e}")
        finally:

            conn.close()
            conn.close()

    # Check if the given client_id exists in the DB, means client is registered (stored in the DB)
    def check_client_id_existence(self, client_id: bytes):

        print("---- DEBUG DB LOOKUP ----")
        print("DB path:", self.path)
        print("Client ID received (hex):", client_id.hex())
        print("Client ID length:", len(client_id))
        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.cursor()
                # cur.execute("SELECT UserName FROM clients WHERE ID = ?", [client_id])
                cur.execute("SELECT UserName FROM clients WHERE ID = ?", [client_id])
                member = cur.fetchone()

                if member is None:
                    print("[DATA BASE]: Could not find client with the given ID.")
                    return False
                else:
                    print("[DATA BASE]: Found the client with the given ID.")
                    return True

        except sqlite3.DatabaseError as e:
            print("[DATA BASE]: Could not connect to the database with the given path:", self.path)
        except sqlite3.Error as e:
            print(f"Unexpected database error occurred: {e}")

        finally:
            cur.close()

    # Collect all pairs of [ID, UserName] from the database except for client_id
    def get_members_list_without_given_id(self, client_id: bytes):

        try:
            with sqlite3.connect(self.path) as conn:
                cur = conn.cursor()

                cur.execute("SELECT ID, UserName FROM clients WHERE ID != ?", [client_id])
                members = cur.fetchall()
                print("Members:", members)
                members_list = []
                for member in members:
                    members_list.append(member)

                return True, members_list


        except sqlite3.IntegrityError as e:
            print("[DATA BASE]: Could not connect to the database with the given path:", self.path)
            return False, None
        except sqlite3.Error as e:
            print(f"Unexpected database error occurred: {e}")
            return False, None

        finally:
            cur.close()

    # Retrieves the public_key of the client with the given id
    def get_public_key(self, client_id: bytes):
        # Checking again for client_id if registered (defensive necessity)
        client_registered = self.check_client_id_existence(client_id)
        if not client_registered:
            return None
        else:
            with sqlite3.connect(self.path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT PublicKey FROM clients WHERE ID = ?", [client_id])
                public_key = cur.fetchone()

                if public_key is None:
                    return None
                else:
                    return public_key[0]

    # Creates a new row in the "messages" table with target_id, requester_id, message_type and message_content
    def insert_message_to_db(self, to_client_id, from_client_id, message_type,
                             message_contents):
        with sqlite3.connect(self.path) as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO messages(ToClient, FromClient, Type, Content) VALUES (?, ?, ?, ?)",
                    (to_client_id, from_client_id, message_type, message_contents)
                )
                # "lastrowid": Retrieves inserted id after inserting row in SQLite
                message_id = cur.lastrowid
                # message_id_to_int = int(message_id)
                conn.commit()

                return message_id

            # If the process fails to insert the row, -1 will be returned (ID could never be a negative number)
            except sqlite3.IntegrityError as e:
                print(f"[DATA BASE ERROR]: could not insert the row: {e}")
                return -1
            except sqlite3.Error as e:
                print(f"Unexpected database error occurred: {e}")
                return -1

    def retrieve_messages_for_id(self, client_id: bytes):
        with sqlite3.connect(self.path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT FromClient, ID, Type, Content FROM messages WHERE ToClient = ?", [client_id])

            records = cur.fetchall()
            messages_list = []
            print(
                "                          FromClient          MessageID Type               ToClient,                                             Content")
            for record in records:
                from_client = record[0]
                message_id = record[1]
                message_type = record[2]
                message = record[3]
                message_size = len(message)

                # Convert message ID, message type and message size to bytes from int and then store it
                message_id, message_type, message_size = convert_to_byte(message_id, message_type, message_size)
                record_converted = (from_client, message_id, message_type, message_size, message)
                messages_list.append(record_converted)

            return True, messages_list


def convert_to_byte(message_id, message_type, message_size):
    message_id_to_bytes = message_id.to_bytes(4, byteorder='little')
    message_type_to_bytes = message_type.to_bytes(1, byteorder='little')
    message_size_to_bytes = message_size.to_bytes(4, byteorder='little')

    return message_id_to_bytes, message_type_to_bytes, message_size_to_bytes

#------------------------------- Debugging ------------------------------------------------------
# client_id = "6CE8B00899BA48568B3FC26F88A2531D"
# print("string:", client_id)
# try:
#     client_id_in_byte = bytes.fromhex(client_id)
#     print("bytes:", client_id_in_byte)
#     print(type(client_id_in_byte))
#
#     db = Database()
#     # response = db.check_client_id_existence(client_id_in_byte)
#     # print(response)
#     # list_of_members = db.get_members_list_without_given_id(client_id_in_byte)
#     # print("List:", list_of_members)
#
#     client_public_key = db.get_public_key(client_id_in_byte)
#     if not client_public_key is None:
#         print("Client_id: ", client_id_in_byte, "Public key:", client_public_key)
#     else:
#         print("Client_id: Doesn't exist in the database.")
#
#     # response = db.insert_message_to_db(client_id_in_byte, client_id_in_byte, 1,
#     #                      b"2rfn1md21mc1nv3v2ivn2NDFJASNFAR32JIF3NFN3")
#     # print(response)
#
#     print("Print messages:")
#     messages_list = db.retrieve_messages_for_id(client_id_in_byte)
#     print(messages_list)
#
# except Exception as e:
#     print(f"[DATABASE ERROR:] {e}")
#     print(
#         "|-------------------------------------------------------------------------------------------------------------|")
#     print(
#         "| [ERROR]: Make sure all the chars given are hexa chars. For example 'S', 's' 'x', etc... are not hexa chars  |")
#     print(
#         "|-------------------------------------------------------------------------------------------------------------|")
#

