from flask import Flask,redirect,session,render_template
import mysql.connector as connector


app=Flask(__name__)


@app.route('/home')
def home():
	return render_template("home.html")

app.run(debug=True)


