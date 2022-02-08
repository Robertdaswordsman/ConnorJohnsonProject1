import os

from cs50 import SQL
from flask import Flask, session, request, render_template, jsonify, redirect
from flask_session import Session
from sqlalchemy import create_engine
#from sqlalchemy.orm import scoped_session, sessionmaker
import requests
#import render_templates

#import re

app = Flask(__name__)




# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure api

library_api = "https://www.googleapis.com/books/v1/volumes"

#Establish database via heroku
db = SQL("postgresql://jnjdrxzaynywqi:2a28da550040edb766c39a4353ea19ef824727e680a1a20e65628799e6f45032@ec2-54-224-64-114.compute-1.amazonaws.com:5432/d1aud2alpnntff")




#res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": "isbn:080213825X"})
#print(res.json())


@app.route("/")
def index():
    if not session.get("name") or not session.get("password"):
        return redirect("/login")
    return render_template("index.html")

@app.route("/test1")
def test1():
    return render_template("index.html")



@app.route("/login", methods=["GET", "POST"])
def login():
        if request.method == "POST":
                #Secure link verified
                session["name"] = request.form.get("name")
                session["password"] = request.form.get("password")

        if verify_member():
            #Login confirmed
            return redirect("/")

    #else login
        return render_template("login.html")
                        
def verify_member():
    member = db.execute("SELECT * FROM members \
                    WHERE name = ? AND password = ?", session["name"], session["password"])
    if(len(member) == 0):
        #Member does not exist yet
        return False
    elif(len(member) == 1):
        #Member exists
        session["member_id"] = member[0]["id"]
        return True
    else:
        #Resolve multiple members
        return render_template("error.html", message="Multiple members detected!")
                                
@app.route("/signUp", methods=["GET", "POST"])
def signup():
                                #Safetey lines
        if request.method == "POST":
                    
            session["name"] = request.form.get("name")
            session["password"] = request.form.get("password")
        
            if verify_member():
                                return redirect("/logout")
            new_Member()
            return redirect("/logout")
                               
                                
                                
def new_member():
                                    db.execute("INSERT INTO members (name, password) \
                VALUES (?, ?)", session["name"], session["password"])
@app.route("/logout")
def logout():
    session["name"] = None
    session["member_id"] = None
    session["password"] = None
    

    return redirect('/')                        
                                
@app.route("/search", methods=["GET", "POST"])
def search():
    booklist = []
    if request.method == "POST":
        isbn = request.form.get("isbn")
        author = request.form.get("author")                                       
        title = request.form.get("title")                        
                                
        booklist = db.execute("SELECT * FROM library WHERE \
                            isbn LIKE ? and \
                            author LIKE ? and \
                            title LIKE ?", f"%{isbn}%", f"%{title}%", f"%{author}%")   
                                
        return render_template("/search.html", books=booklist)                        
                                
                                
@app.route("/book", methods=["GET","POST"])
def book():
    BookPrime = {}
    reviews = []
    if request.method == "POST":   
        
        BookPrime["isbn"] = request.form.get("isbn")
        BookPrime["author"] = request.form.get("author")
        BookPrime["title"] = request.form.get("title")
        BookPrime["year"] = int(request.form.get("year"))
        res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{Book['isbn']}"})
        dic = res.json()
        review = db.execute("SELECT * \
                            FROM reviews r  \
                            INNER JOIN members u \
                            ON r.member_id = u.id \
                            WHERE r.isbn = ?", BookPrime["isbn"])
        if dic["totalItems"] == 0:
            BookPrime["average_Rating"] = "Null"
            BookPrime["ratings_total"] = "Null"

    return render_template("/bookinfo.html", book=BookPrime, reviews=review)
                            
@app.route("/review", methods=["GET","POST"])
def review():    

    if request.method == "POST":
        isbn = request.form.get("isbn")
        rating = int(request.form.get("rating"))
        review = request.form.get("review")
        
        
        db.execute("INSERT INTO reviews (member_id, isbn, rating, revier) \
                    VALUES (?, ?, ?, ?)", session["member_id"], isbn, rating, review) 
            
            
        return redirect('/book')
            
@app.route("/api/<isbn_10>")
def book_api(isbn_10):
    json = {
        "author": "Null",
        "title": "Null",
        "publishedDate": "Null",
        "ISBN_10": "Null",
        "ISBN_13": "Null",
        "review_total": "Null",
        "average_ratings": "Null"
    }

    #basic book info
    dic = db.execute("SELECT * \
                        FROM library \
                        WHERE isbn = ?", isbn_10)
    print(dic)
    if dic is None:
        return jsonify({"error": "ISBN not found"}), 404
    json["ISBN_10"] = dic[0]["isbn"]
    json["title"] = dic[0]["title"]
    json["author"] = dic[0]["author"]
    

    #use api to get extra info
    #google api
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{dic[0]['isbn']}"})
    dic = res.json()

    #if book is not found
    if dic["totalItems"] == 0:
        json["average_Rating"] = "Null"
        json["ratings_total"] = "Null"


    return jsonify(json)
