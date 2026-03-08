import sys

import ConnectionCreator

file_name = "myport.info"
def main():
    try:
        with open(file_name, "r") as file:
            port_path = file.read()
        try:
            port = int(port_path.strip())
            ConnectionCreator.create_connection(port)

            return 0
        except ValueError:
            print(f"[Error]: Cannot parse the contents of {port_path} as an integer")
            return 1

    except FileNotFoundError:
        print(f"[Error]: File '{file_name}' doesn't exist. Using default port 1357")
        port = 1357
        ConnectionCreator.create_connection(port)
        return 0

    except PermissionError:
        print(f"[Error]: Permission denied. Unable to access the file '{file_name}'.")
        return 1

    except UnicodeError:
        print(f"[Error]: A Unicode char was found in the file '{file_name}' .")
        return 1

    except Exception as e:
        print(f"[Error]: An unexpected error occurred: {e}")
        return 1



if __name__ == "__main__":
    sys.exit(main())

# To understand the build better: https://discord.com/channels/267624335836053506/1469317566999695435