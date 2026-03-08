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