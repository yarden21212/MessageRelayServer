# 💬 MessageRelay

MessageRelay is a TCP-based client-server messaging application developed using C++ and Python. It allows users to register and exchange encrypted messages through a custom binary communication protocol, with SQLite used for persistent data storage.

This project was developed as part of my Computer Science degree, providing hands-on experience with socket programming, network communication, cryptography, and client-server architecture.

The primary focus was understanding how messaging systems operate at a lower level, including binary message parsing, TCP connections, and secure data exchange.

---

# Features

- **Client-server messaging:** Exchange messages between users through a centralized TCP server.
- **Custom binary protocol:** Structure and parse binary requests and responses for communication between the C++ client and Python server.
- **User registration:** Register users and maintain their information on the server.
- **Encrypted communication:** Implement RSA and AES encryption mechanisms to support secure message exchange.
- **Persistent storage:** Store user and messaging-related data using SQLite.
- **Socket programming:** Establish TCP connections and handle network communication between clients and the server.

---

# Tech Stack

| Layer | Technologies |
|---|---|
| Client | C++ |
| Server | Python |
| Networking | TCP/IP, Socket Programming |
| Communication | Custom Binary Protocol |
| Database | SQLite |
| Security | RSA, AES |
| Architecture | Client-Server |

---

# Architecture

**MessageRelay follows a client-server architecture, separating the C++ client application from the Python server responsible for handling requests and communication.**

**Client:** C++ application → TCP socket connection

**Communication:** C++ client ↔ Custom Binary Protocol ↔ Python server

**Server:** Python application → Request processing and message handling

**Database:** Python server → SQLite

**Security:** RSA and AES cryptographic mechanisms for encrypted message exchange.

The client communicates with the server through TCP sockets using a custom binary protocol rather than a REST API.

The server processes incoming requests, manages user registration, and handles message exchange between clients.

SQLite provides persistent storage for user information and messaging-related records.

The communication system uses cryptographic mechanisms to protect exchanged messages.

---

# Screenshots & Videos

**Will be added soon — Screenshots and a demonstration of the messaging system.**

- [Client application]
- [User registration]
- [Message exchange]
- [Server communication]

---

# Project Background

MessageRelay was developed as a university project to explore the fundamentals of network programming and secure communication.

Unlike web-based messaging applications that rely on existing HTTP APIs, this project uses direct TCP socket communication and a custom binary protocol.

The project provided practical experience with implementing communication between applications written in different programming languages, handling binary data, integrating encryption, and maintaining persistent records in a database.
