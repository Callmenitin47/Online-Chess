from flask import Flask,redirect,session,render_template,request,jsonify
import mysql.connector as connector
import bcrypt
from pymongo import MongoClient
import random
from flask_socketio import SocketIO,join_room
from flask_cors import CORS
import time
from flask_session import Session
import redis



sqlDB_username="root"
sqlDB_password="root"
sqlDB_host="localhost"
sqlDB_database="chess"
client=MongoClient("mongodb://localhost:27017/")
db=client["chess"]
match_history=db["games"]
player_ids=[]
sessions={}
ongoing_matches={}
pieces={
'p':'url(../static/files/pieces/black_pawn.png)',
'P':'url(../static/files/pieces/white_pawn.png)',
'r':'url(../static/files/pieces/black_rook.png)',
'R':'url(../static/files/pieces/white_rook.png)',
'b':'url(../static/files/pieces/black_bishop.png)',
'B':'url(../static/files/pieces/white_bishop.png)',
'n':'url(../static/files/pieces/black_knight.png)',
'N':'url(../static/files/pieces/white_knight.png)',
'q':'url(../static/files/pieces/black_queen.png)',
'Q':'url(../static/files/pieces/white_queen.png)',
'k':'url(../static/files/pieces/black_king.png)',
'K':'url(../static/files/pieces/white_king.png)',

}

app = Flask(__name__)
app.secret_key = "enufwbqbiuwefbwebfuwergbfyewrgbuewrgbuyrbbwueuwen"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app, manage_session=True, cors_allowed_origins='*')
cors = CORS(app, resources={r"/socket.io/*": {"origins": "http://localhost:5000"}})
player1=['p','n','r','k','q','b']
player2=['P','N','R','K','Q','B']

class Match:
	def __init__(self,id1,id2):
		self.players=[id1,id2]
		self.turn=random.randint(0,1);
		self.board=[
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["q", "q", "q", "p", "p", "p", "p", "p"],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["P", "P", "P", "P", "P", "P", "P", "P"],
            ["R", "N", "B", "Q", "K", "B", "N", "R"]
        ]
		self.status="ongoing"
		self.winner=-1


def checkLogin():
	if session.get('username'):
		return True
	return False

def generate_room_id():
    return str(int(time.time() * 1000))

def playerStats(userid):

	#Total games
	total_games_query={"$or": [{"player1_id":userid},{"player2_id":userid}]}
	total=match_history.count_documents(total_games_query)

	#Games won
	games_won_query={"winner_id":userid}
	won=match_history.count_documents(games_won_query)

	#Games drawn
	games_drawn_query={
		   "$and": [
		       {"$or": [{"player1_id":userid}, {"player2_id":userid}]},
		       {"result": "draw"}
		   ]
	}
	drawn=match_history.count_documents(games_drawn_query)

	return total,won,drawn,total-won-drawn


def random_filename():
    out=""
    arr=[[ord('a'),ord('z')],[ord('A'),ord('Z')],[ord('0'),ord('9')]]
    for i in range(0,20):
        choice=random.randint(0,2)
        out=out+chr(random.randint(arr[choice][0],arr[choice][1]));      
    return out

def get_db_connection():
	return connector.connect(
	host=sqlDB_host,
	user=sqlDB_username,
	password=sqlDB_password,
	database=sqlDB_database
	)

@app.route('/home')
def home():
	if checkLogin()==True:
		return redirect('/profile')
	return render_template("home.html")

@app.route('/signup',methods=['POST'])
def signup():
	username=request.form['username']
	fullname=request.form['fullname']
	email=request.form['email']
	country=request.form['country']
	password=request.form['password']
	connection=get_db_connection()
	cursor=connection.cursor();
	query="select * from users where username=%s or email=%s"
	cursor.execute(query,(username,password));
	rows=cursor.fetchall()
	if rows:
		return jsonify({"error":"Account with given Email/Username already exists"}),409
	else:
		hashed_password=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
		query="INSERT into users(username,fullname,country,password_hash,elo_rating,email) values(%s,%s,%s,%s,%s,%s)"
		cursor.execute(query,(username,fullname,country,hashed_password,1500,email))
		connection.commit()
		return jsonify({"message":"Account has been created. Login Now"}),200


@app.route('/login',methods=['POST'])
def login():
	username=request.form['username']
	password=request.form['password']
	query="SELECT id,password_hash from users where username=%s"
	connection=get_db_connection()
	cursor=connection.cursor();
	cursor.execute(query,(username,))
	row=cursor.fetchone();
	if row:
		if bcrypt.checkpw(password.encode('utf-8'),row[1].encode('utf-8')):
			socketio.server.environ['session'] = session
			session['username']=username
			session['id']=row[0]
			sessions[session.sid]=session['id']
			return jsonify({"message":"Login successful"}),200
		else:
			return jsonify({"message":"Username/Password is Incorrect"}),401
	else:
		return jsonify({"message":"Username/Password is Incorrect"}),401


@app.route('/updatepassword')
def updatepassword():
	if checkLogin()==True:
		return render_template('updatepassword.html')
	return redirect('/home')

@app.route('/changepassword',methods=['POST'])
def changepassword():
	if checkLogin()==False:
		return redirect('/home')

	connection=get_db_connection()
	cursor=connection.cursor()
	username=session.get('username')
	password=request.form['password']
	old_password=request.form['old-password']

	query="SELECT password_hash from users where username=%s"
	cursor.execute(query,(username,))
	row=cursor.fetchone();
	if not bcrypt.checkpw(old_password.encode('utf-8'),row[0].encode('utf-8')):
		return jsonify({"message":"Old password is Incorrect"}),401

	hashed_password=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
	query="UPDATE users set password_hash=%s where username=%s"
	cursor.execute(query,(hashed_password,username,))
	connection.commit()

	return jsonify({"message":"Password has been succesfully updated."}),200



@app.route('/profile')
def profile():
	if checkLogin()==True:
		connection=get_db_connection()
		cursor=connection.cursor(dictionary=True)
		userid=session.get('id')
		user_data=dict()

		user_profile_query="""
		SELECT * FROM users WHERE id=%s
		"""
		cursor.execute(user_profile_query,(userid,))
		row=cursor.fetchone();
		
		user_data['id']=row['id']
		user_data['username']=row['username']
		user_data['fullname']=row['fullname']
		user_data['email']=row['email']
		user_data['dp']=row['DP']
		user_data['elo_rating']=row['elo_rating']

		world_rank_query = """
		SELECT COUNT(*) + 1 AS world_rank
		FROM users
		WHERE elo_rating > (
		    SELECT elo_rating
		    FROM users
		    WHERE id = %s
		);
		"""
		cursor.execute(world_rank_query,(userid,))
		row=cursor.fetchone()
		user_data['world_rank']=row['world_rank']

		country_rank_query = """
		SELECT COUNT(*) + 1 AS country_rank
		FROM users
		WHERE country = (
		    SELECT country
		    FROM users
		    WHERE id = %s
		) AND elo_rating > (
		    SELECT elo_rating
		    FROM users
		    WHERE id = %s
		);
		"""
		cursor.execute(country_rank_query,(userid,userid,))
		row=cursor.fetchone()
		user_data['country_rank']=row['country_rank']

		total,won,drawn,lost=playerStats(userid);

		user_data['total']=total
		user_data['won']=won
		user_data['drawn']=drawn
		user_data['lost']=lost

		userid=session.get('username')
		return render_template('dashboard.html',data=user_data)
	else:
		return redirect('/home')

@app.route('/updatedata')
def updatedata():
	if checkLogin()==True:
		data=dict()
		userid=session.get('id')
		username=session.get('username')
		connection=get_db_connection()
		cursor=connection.cursor(dictionary=True)
		cursor.execute("SELECT * FROM users WHERE username=%s and id=%s",(username,userid,))
		row=cursor.fetchone();
		data['username']=row['username']
		data['email']=row['email']
		data['dp']=row['DP']
		data['country']=row['country']
		data['fullname']=row['fullname']
		return render_template('updateprofile.html',data=data)
	return redirect('/home')

@app.route('/updateprofile',methods=['POST'])
def updateprofile():
	userid=session.get('id')
	username=session.get('username')
	input_username=request.form['username']
	email=request.form['email']
	fullname=request.form['fullname']
	country=request.form['country']
	file=request.files['dp']
	connection=get_db_connection()
	cursor=connection.cursor(dictionary=True)
	cursor.execute("SELECT * FROM users WHERE username=%s and id!=%s",(input_username,userid,))
	username_exists=cursor.fetchone()
	cursor.execute("SELECT * FROM users WHERE email=%s and id!=%s",(email,userid,))
	email_exists=cursor.fetchone()
	if username_exists:
		return jsonify({'error':'Username is already taken'}),400
	if email_exists:
		return jsonify({'error':'Email is already taken'}),400

	if file.filename!='':
		fname=random_filename()
		file.save(f"static/files/{fname}")
		update_query="UPDATE users SET email=%s,username=%s,fullname=%s,country=%s,DP=%s WHERE id=%s"
		cursor.execute(update_query,(email,input_username,fullname,country,fname,userid))
	else:
		update_query="UPDATE users SET email=%s,username=%s,fullname=%s,country=%s WHERE id=%s"
		cursor.execute(update_query,(email,input_username,fullname,country,userid))

	session['username']=input_username
	connection.commit()
	
	return jsonify({'message':'Profile has been sucessfully updated.'})

@app.route('/chessboard')
def chessboard():
	if checkLogin()==True:
		data=dict()
		userid=session.get('id')
		username=session.get('username')
		connection=get_db_connection()
		cursor=connection.cursor(dictionary=True)
		cursor.execute("SELECT * FROM users WHERE username=%s and id=%s",(username,userid,))
		row=cursor.fetchone();

		total,won,drawn,lost=playerStats(userid)

		data['fullname']=row['fullname']
		data['country']=row['country']
		data['dp']=row['DP']
		data['total']=total
		data['won']=won
		data['drawn']=drawn
		data['lost']=lost
		data['sid']=session.sid
		data['id']=session.get('id')

		return render_template('chessboard.html',data=data)
	return redirect('/home')

def create_match(id1,id2,room_id):
	match=Match(id1,id2)
	ongoing_matches[room_id]=match



def find_match(user_id):
	user_id=int(user_id)
	global player_ids
	if len(player_ids)==0:
		player_ids.append(user_id)
	else:
		room_id = generate_room_id()
		opponent_id = player_ids.pop(0)
		connection=get_db_connection()
		cursor=connection.cursor(dictionary=True)
		player1=dict()
		cursor.execute("SELECT * FROM users WHERE id=%s",(user_id,))
		row=cursor.fetchone();
		total,won,drawn,lost=playerStats(user_id)
		player1['fullname']=row['fullname']
		player1['country']=row['country']
		player1['dp']=row['DP']
		player1['total']=total
		player1['won']=won
		player1['drawn']=drawn
		player1['lost']=lost
		player1['room_id']=room_id

		player2=dict()
		cursor.execute("SELECT * FROM users WHERE id=%s",(opponent_id,))
		row=cursor.fetchone();
		total,won,drawn,lost=playerStats(opponent_id)
		player2['fullname']=row['fullname']
		player2['country']=row['country']
		player2['dp']=row['DP']
		player2['total']=total
		player2['won']=won
		player2['drawn']=drawn
		player2['lost']=lost
		player2['room_id']=room_id

		create_match(user_id,opponent_id,room_id)

		socketio.emit('match_found', player2, room=user_id)
		socketio.emit('match_found', player1, room=opponent_id)

@socketio.on('join_room')
def join(user_session): 
	if sessions[user_session['sid']] !=	int(user_session['id']):
		return False
	join_room(int(user_session['id']))
	session['id']=int(user_session['id'])
	find_match(user_session['id'])

@socketio.on('join_match')
def join_match(match_details):
	session['room_id']=match_details['room_id']
	join_room(match_details['room_id'])


def validate_pawn(board,source,dest,player):

	if player==0 and board[source[0]][source[1]]=='P':
		return False
	if player==1 and board[source[0]][source[1]]=='p':
		return False

	if board[source[0]][source[1]]=='p':
		if dest[0]==source[0]+1 and board[source[0]+1][source[1]]=="":
			return True
		elif dest[0]==source[0]+2 and board[source[0]+1][source[1]]=="" and board[source[0]+2][source[1]]=="":
			return True
		elif dest[0]==source[0]+1 and dest[1]==source[1]-1 and board[source[0]+1][source[1]-1] in player2:
			return True
		elif dest[0]==source[0]+1 and dest[1]==source[1]+1 and board[source[0]+1][source[1]+1] in player2:
			return True
		else:	
			return False
	else:
		if dest[0]==source[0]-1 and board[source[0]-1][source[1]]=="":
			return True
		elif dest[0]==source[0]-2 and board[source[0]-1][source[1]]=="" and board[source[0]-2][source[1]]=="":
			return True
		elif dest[0]==source[0]-1 and dest[1]==source[1]-1 and board[source[0]-1][source[1]-1] in player1:
			return True
		elif dest[0]==source[0]-1 and dest[1]==source[1]+1 and board[source[0]-1][source[1]+1] in player1:
			return True
		else:	
			return False
	return False



def validate_king(board,source,dest,player):
	if player==0:
		enemies=player2
	else: 
		enemies=player1

	if dest[0]==source[0]-1 and dest[1]==source[1]-1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]-1 and dest[1]==source[1] and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]-1 and dest[1]==source[1]+1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True 
	elif dest[0]==source[0] and dest[1]==source[1]-1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0] and dest[1]==source[1]+1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]+1 and dest[1]==source[1]-1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]+1 and dest[1]==source[1] and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]+1 and dest[1]==source[1]+1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	else:
		return False

def validate_knight(board,source,dest,player):
	if player==0:
		enemies=player2
	else: 
		enemies=player1

	if dest[0]==source[0]-2 and dest[1]==source[1]-1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]-2 and dest[1]==source[1]+1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]+2 and dest[1]==source[1]-1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True 
	elif dest[0]==source[0]+2 and dest[1]==source[1]+1 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]-1 and dest[1]==source[1]+2 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]-1 and dest[1]==source[1]-2 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]+1 and dest[1]==source[1]+2 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	elif dest[0]==source[0]+1 and dest[1]==source[1]-2 and (board[dest[0]][dest[1]] in enemies or board[dest[0]][dest[1]]==""):
		return True
	else:
		return False

def validate_bishop(board,source,dest,player):
	if player==0:
		enemies=player2
	else: 
		enemies=player1

	print("bishop")
	print(player)
	print(enemies)

	diff=int(abs(dest[0]-source[0])/abs(dest[1]-source[1]))

	if diff==1:
		if dest[1]<source[1] and dest[0]<source[0]:
			row_dir=-1
			col_dir=-1
		elif dest[1]<source[1] and dest[0]>source[0]:
			row_dir=1
			col_dir=-1
		elif dest[1]>source[1] and dest[0]<source[0]:
			row_dir=-1
			col_dir=1
		elif dest[1]>source[1] and dest[0]>source[0]:
			row_dir=1
			col_dir=1
		start_row,start_col=source[0]+row_dir,source[1]+col_dir
		while True:
			if start_row==dest[0] and start_col==dest[1]:
				if board[dest[0]][dest[1]]=="" or board[dest[0]][dest[1]] in enemies:
					return True
				else:
					return False 
			if board[start_row][start_col]!="":
				return False
			start_row=start_row+row_dir
			start_col=start_col+col_dir
	else:
		return False
	return False

def validate_queen(board,source,dest,player):
	if player==0:
		enemies=player2
	else: 
		enemies=player1

	if dest[1]==source[1] and dest[0]<source[0]:
		row_dir=-1
		col_dir=0
	elif dest[1]==source[1] and dest[0]>source[0]:
		row_dir=1
		col_dir=0
	elif dest[1]>source[1] and dest[0]==source[0]:
		row_dir=0
		col_dir=1
	elif dest[1]<source[1] and dest[0]==source[0]:
		row_dir=0
		col_dir=-1
	else :
		diff=abs(dest[0]-source[0])/abs(dest[1]-source[1])
		if diff==1:
			if dest[1]<source[1] and dest[0]<source[0]:
				row_dir=-1
				col_dir=-1
			elif dest[1]<source[1] and dest[0]>source[0]:
				row_dir=1
				col_dir=-1
			elif dest[1]>source[1] and dest[0]<source[0]:
				row_dir=-1
				col_dir=1
			elif dest[1]>source[1] and dest[0]>source[0]:
				row_dir=1
				col_dir=1
		else:
			return False

	start_row,start_col=source[0]+row_dir,source[1]+col_dir

	while True:
		if start_row==dest[0] and start_col==dest[1]:
			if board[dest[0]][dest[1]]=="" or board[dest[0]][dest[1]] in enemies:
				return True
			else:
				return False 
		if board[start_row][start_col]!="":
			return False
		start_row=start_row+row_dir
		start_col=start_col+col_dir



def validate_rook(board,source,dest,player):
	if player==0:
		enemies=player2
	else: 
		enemies=player1

	if dest[1]==source[1] and dest[0]<source[0]:
		row_dir=-1
		col_dir=0
	elif dest[1]==source[1] and dest[0]>source[0]:
		row_dir=1
		col_dir=0
	elif dest[1]>source[1] and dest[0]==source[0]:
		row_dir=0
		col_dir=1
	elif dest[1]<source[1] and dest[0]==source[0]:
		row_dir=0
		col_dir=-1
	else:
		return False

	start_row,start_col=source[0]+row_dir,source[1]+col_dir

	while True:
		if start_row==dest[0] and start_col==dest[1]:
			if board[dest[0]][dest[1]]=="" or board[dest[0]][dest[1]] in enemies:
				return True
			else:
				return False 
		if board[start_row][start_col]!="":
			return False
		start_row=start_row+row_dir
		start_col=start_col+col_dir



@socketio.on('move')
def move(move_details):
	match=ongoing_matches[session['room_id']]
	source_row=int(move_details['r1'])-1
	source_col=int(move_details['c1'])-1
	dest_row=int(move_details['r2'])-1
	dest_col=int(move_details['c2'])-1
	print(f"turn of{match.turn}")

	#Player makes a move even if it is not his turn
	cond1=session['id']!=match.players[match.turn]
	#Player selects a blank checkbox 
	cond2=match.board[source_row][source_col]==""
	#Player not making move on his own pieces
	cond3=False
	#source and destination same
	cond4=dest_row==source_row and dest_col==source_col 

	if match.turn==0:
		if (match.board[source_row][source_col] not in ['p','n','r','k','q','b']):
			cond3=True
		if (match.board[dest_row][dest_col] in ['p','n','r','k','q','b']):
			cond3=True

	if match.turn==1:
		if (match.board[source_row][source_col] not in ['P','N','R','K','Q','B']):
			cond3=True
		if (match.board[dest_row][dest_col] in ['P','N','R','K','Q','B']):
			cond3=True

	#print(match.board)

	if  cond1 or cond2 or cond3 or cond4:
		print("no valid move")
		return socketio.emit('move_update',{'status':'Not a valid move'},room=session['id'])
	else:
		move_valid=False
		if match.board[source_row][source_col] in ['p','P']:
			move_valid=validate_pawn(match.board,[source_row,source_col],[dest_row,dest_col],match.turn)
		elif match.board[source_row][source_col] in ['r','R']:
			move_valid=validate_rook(match.board,[source_row,source_col],[dest_row,dest_col],match.turn)
		elif match.board[source_row][source_col] in ['k','K']:
			move_valid=validate_king(match.board,[source_row,source_col],[dest_row,dest_col],match.turn)
		elif match.board[source_row][source_col] in ['n','N']:
			move_valid=validate_knight(match.board,[source_row,source_col],[dest_row,dest_col],match.turn)
		elif match.board[source_row][source_col] in ['q','Q']:
			move_valid=validate_queen(match.board,[source_row,source_col],[dest_row,dest_col],match.turn)
		elif match.board[source_row][source_col] in ['b','B']:
			move_valid=validate_bishop(match.board,[source_row,source_col],[dest_row,dest_col],match.turn)

		if move_valid==True:
			data={}
			data['status']='valid'
			data['dest_row']=move_details['r2']
			data['dest_col']=move_details['c2']
			data['source_row']=move_details['r1']
			data['source_col']=move_details['c1']
			data['piece']=pieces[match.board[source_row][source_col]]
			ongoing_matches[session['room_id']].board[dest_row][dest_col]=match.board[source_row][source_col]
			ongoing_matches[session['room_id']].board[source_row][source_col]=""
			if match.turn==0:
				ongoing_matches[session['room_id']].turn=1
			else:
				ongoing_matches[session['room_id']].turn=0
			return socketio.emit('move_update',data,room=session['room_id'])
		else:
			return socketio.emit('move_update',{'status':'Not a valid move'},room=session['id'])


socketio.run(app,debug=True)


