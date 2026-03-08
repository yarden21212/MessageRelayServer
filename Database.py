import sqlite3
import uuid
import datetime
import struct


# Read more about:
# datetime library here: https://docs.python.org/3/library/datetime.html
# Sqlite exceptions handling:
# https://www.zetcode.com/python/sqlite3-error/
# https://www.pythonlore.com/handling-sqlite3-database-exceptions-and-errors/
class Database:
    def __init__(self, db_path = "defensive.db"):
        self.path = db_path

    # Table creation:
    # Create 2 different tables (in case do not exist):
    # A table for clients' data & a table for messages (to client and from whom)
    def create_table(self):

        with sqlite3.connect(self.path) as conn:

            conn.executescript(""" 
                CREATE TABLE IF NOT EXISTS clients(
                    ID BLOB PRIMARY KEY,
                    UserName TEXT UNIQUE NOT NULL,
                    PublicKey BLOB NOT NULL,
                    LastSeen TEXT NOT NULL
                );
    
                CREATE TABLE IF NOT EXISTS messages( 
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

                new_uuid = uuid.uuid4().bytes # Conversion to bytes (16 bytes as requested)
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


string = "6CE8B00899BA48568B3FC26F88A2531D"
print("string:", string)
in_byte = bytes.fromhex(string)
print("bytes:",in_byte)
print(type(in_byte))

db = Database()
response = db.check_client_id_existence(in_byte)
print(response)
list_of_members = db.get_members_list_without_given_id(in_byte)
print("List:", list_of_members)
