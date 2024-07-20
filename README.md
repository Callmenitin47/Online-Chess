# Online Chess

## Description

This project is a real-time, multiplayer chess game developed using Flask for the backend, Flask-SocketIO for real-time gameplay, MySQL for user authentication, and MongoDB for storing match history. The game ensures low-latency gameplay and provides a smooth user experience. The chessboard is dynamically updated in real-time as players make moves.

## Features

**Real-time gameplay:** Utilizes WebSockets for low-latency, bi-directional communication.
**User Authentication:** Secure login and signup using MySQL.
**Match History:** Stores details of matches in MongoDB.
**Move Validation:** Ensures valid moves and checks for check, checkmate, and draw conditions.

## Requirements

* Python 3.x
* Flask
* Flask-SocketIO
* MySQL
* MongoDB
* mysql-connector
* PyMongo
* bcrypt
* flask-CORS
