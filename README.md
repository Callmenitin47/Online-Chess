# Online Chess

## Description

This project is a real-time, multiplayer chess game developed using Flask for the backend, Flask-SocketIO for real-time gameplay, MySQL for user authentication, and MongoDB for storing match history. The game ensures low-latency gameplay and provides a smooth user experience. The chessboard is dynamically updated in real-time as players make moves.

## Features

* **Real-time gameplay:** Utilizes WebSockets for low-latency, bi-directional communication.
* **User Authentication:** Secure login and signup using MySQL.
* **Match History:** Stores details of matches in MongoDB.
* **Move Validation:** Ensures valid moves and checks for check, checkmate, and draw conditions.

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

## Database Setup

### MySQL

Create a new MySQL database:

```
CREATE DATABASE chess;
```
Use the following schema for user authentication:

```
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    fullname VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    DP VARCHAR(100) NOT NULL DEFAULT 'avatar.jpg',
    country VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    elo_rating INT NOT NULL DEFAULT 1000
);

```

### MongoDB

Ensure MongoDB is running.
Use the following schema for storing match history
```
{
    "_id": ObjectId,
    "player1_id": Number,
    "player2_id": Number,
    "winner_id": Number,
    "result": String, // "finished", "drawn"
}
```
## Future Scope

* **Time Restricted Gamed**: Timed games with different time controls, such as 5-minute and 10-minute games.
* **AI Opponent:** Implement an AI opponent for players to practice against when no human opponent is available.
* **Spectator Mode:** Allow other users to watch ongoing games.
* **Enhanced Statistics:** Track and display detailed statistics for each player, such as win/loss ratio, average game duration, etc.

