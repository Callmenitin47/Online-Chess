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

app = Flask(__name__)
app.secret_key = "enufwbqbiuwefbwebfuwergbfyewrgbuewrgbuyrbbwueuwen"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app, manage_session=False, cors_allowed_origins='*')
cors = CORS(app, resources={r"/socket.io/*": {"origins": "http://localhost:5000"}})




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
		print("here\n\n\n\n")
		print(userid)
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

def find_match(user_id):
	user_id=int(user_id)
	global player_ids
	print(player_ids)
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
		print(user_id)
		total,won,drawn,lost=playerStats(user_id)
		player1['fullname']=row['fullname']
		player1['country']=row['country']
		player1['dp']=row['DP']
		player1['total']=total
		player1['won']=won
		player1['drawn']=drawn
		player1['lost']=lost

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

		socketio.emit('match_found', player2, room=user_id)
		socketio.emit('match_found', player1, room=opponent_id)
 


@socketio.on('join_room')
def join(user_session): 
	if sessions[user_session['sid']] !=	int(user_session['id']):
		return False
	join_room(int(user_session['id']))
	session['id']=user_session['id']
	find_match(user_session['id'])

socketio.run(app,debug=True)


