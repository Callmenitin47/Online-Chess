from flask import Flask,redirect,session,render_template,request,jsonify
import mysql.connector as connector
import bcrypt
from pymongo import MongoClient

app=Flask(__name__)
app.secret_key="enufwbqbiuwefbwebfuwergbfyewrgbuewrgbuyrbbwueuwen"
sqlDB_username="root"
sqlDB_password="root"
sqlDB_host="localhost"
sqlDB_database="chess"
client=MongoClient("mongodb://localhost:27017/")
db=client["chess"]
match_history=db["games"]


def checkLogin():
	if session.get('username'):
		return True
	return False

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
		return render_template('dashboard.html')
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
	query="SELECT password_hash from users where username=%s"
	connection=get_db_connection()
	cursor=connection.cursor();
	cursor.execute(query,(username,))
	row=cursor.fetchone();
	if row:
		if bcrypt.checkpw(password.encode('utf-8'),row[0].encode('utf-8')):
			session['username']=username;
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
		username=session.get('username')
		user_data=dict()

		user_profile_query="""
		SELECT * FROM users WHERE username=%s
		"""
		cursor.execute(user_profile_query,(username,))
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
		cursor.execute(world_rank_query,(username,))
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
		cursor.execute(country_rank_query,(username,username,))
		row=cursor.fetchone()
		user_data['country_rank']=row['country_rank']

		#Total games
		total_games_query={"$or": [{"player1_id":user_data['id']},{"player2_id":user_data['id']}]}
		total=match_history.count_documents(total_games_query)

		#Games won
		games_won_query={"winner_id":user_data['id']}
		won=match_history.count_documents(games_won_query)

		#Games drawn
		games_drawn_query={
		    "$and": [
		        {"$or": [{"player1_id":user_data['id']}, {"player2_id":user_data['id']}]},
		        {"result": "draw"}
		    ]
		}
		drawn=match_history.count_documents(games_drawn_query)

		user_data['total']=total
		user_data['won']=won
		user_data['drawn']=drawn
		user_data['lost']=total-won-drawn
		return render_template('dashboard.html',data=user_data)
	else:
		return redirect('/home')

app.run(debug=True)


