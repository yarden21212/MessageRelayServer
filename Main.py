import sys
from pathlib import Path

import ConnectionCreator

def main():
    myport_path = Path("myport.info.txt")
    try:
        port = int(myport_path.read_text())
        ConnectionCreator.create_connection(port)
    except OSError:
        print(f"File {myport_path} doesn't exist. Will be automatically connected to port 1357")
        ConnectionCreator.create_connection(1357)
        return 1
    except ValueError:
        print("cannot parse the contents of {myport_path} as an integer")
        return 1



if __name__ == "__main__":
    sys.exit(main())

# To understand the build better: https://discord.com/channels/267624335836053506/1469317566999695435