import os
from flask import Flask, render_template, request, redirect, session
import pyodbc
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

# Read connection strings from environment variables (App Service settings)
sql_conn_str = os.getenv("SQL_CONNECTION_STRING")
blob_conn_str = os.getenv("BLOB_CONNECTION_STRING")

# SQL connection
conn = pyodbc.connect(sql_conn_str)
cursor = conn.cursor()

# Blob storage connection
blob_service = BlobServiceClient.from_connection_string(blob_conn_str)
container_name = "article-images"

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            username, password
        )
        user = cursor.fetchone()

        if user:
            session["user"] = username
            return redirect("/home")
        else:
            return "Login Failed"

    return render_template("login.html")


# HOME PAGE
@app.route("/home")
def home():

    cursor.execute("SELECT title, author, body, image_url FROM articles")
    articles = cursor.fetchall()

    return render_template("index.html", articles=articles)


# CREATE ARTICLE
@app.route("/create", methods=["GET", "POST"])
def create():

    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]
        body = request.form["body"]
        image = request.files["image"]

        # secure filename
        filename = secure_filename(image.filename)

        # upload to blob storage
        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=filename
        )

        blob_client.upload_blob(image, overwrite=True)

        # image url
        image_url = f"https://cmsstorage123.blob.core.windows.net/article-images/{filename}"

        # insert article in SQL
        cursor.execute(
            "INSERT INTO articles (title, author, body, image_url) VALUES (?, ?, ?, ?)",
            title, author, body, image_url
        )

        conn.commit()

        return redirect("/home")

    return render_template("create.html")


if __name__ == "__main__":
    app.run()