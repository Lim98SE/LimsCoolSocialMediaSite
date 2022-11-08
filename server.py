import flask
from flask import request, render_template, make_response
import yaml
import hashlib
import uuid

def sha256(string):
    string = bytes(string, encoding="utf-8")
    return hashlib.sha256(string).hexdigest()

app = flask.Flask(__name__)

website_error = ""
yml_loader = yaml.Loader

try:
    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)
        database["NoneUser"]
except Exception:
    with open("database.yml", "w") as database_file:
        yaml.dump({"NoneUser":{"password":"None", "posts":[]}}, database_file)

@app.route("/")
def index_get():
    name = request.cookies.get("name")
    name = f"Welcome back, {name}!" if name is not None else "Welcome to [WEBSITE NAME HERE]!"
    return make_response(render_template("index.html", name=name))

@app.route("/signup", methods=["GET"])
def signup_get():
    return make_response(render_template("signup.html"))

@app.route("/signup", methods=["POST"])
def signup_post():
    global website_error

    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)

    name = request.form.get("name")
    password = request.form.get("password")
    if name is None:
        website_error = "Username does not exist. Give me a name!"
        return website_error

    if name in database:
        website_error = "User already exists. Try to remember your password, please. I can't implement a reset password system."
        return website_error

    if password is None:
        website_error = "Password doesn't exist. You kinda need one of those."
        return website_error

    if len(password) < 6:
        website_error = "Password is too short. <strike>unlike my long penis</strike>"
        return website_error

    database[name] = {"password":sha256(password), "posts":[], "id":str(uuid.uuid1())}

    with open("database.yml", "w") as database_file:
        yaml.dump(database, database_file)

    return make_response(render_template("redirect.html", page="/login"))

@app.route("/login", methods=["GET"])
def login_get():
    return make_response(render_template("login.html"))

@app.route("/login", methods=["POST"])
def login_post():
    name = request.form.get("name")
    password = request.form.get("password")

    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)

    if not name in database:
        return "User not found idiot"

    sha_pss = sha256(password)

    response = make_response(render_template("redirect.html", page="/"))

    if not sha_pss == database[name]["password"]:
        response.set_cookie("id", "N/A")
        response.set_cookie("loggedin", "0")
        response.set_cookie("name", "", expires=0)
        return response

    response.set_cookie("id", database[name]["id"])
    response.set_cookie("loggedin", "1")
    response.set_cookie("name", name)

    return response

@app.route("/database")
def view_database():
    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)

    return str(database)

@app.route("/cookies")
def cookie_get():
    return str(request.cookies)

@app.route("/clear/cookies")
def clear_cookies_get():
    response = make_response(render_template("redirect.html", page="/"))

    for i in request.cookies:
        response.set_cookie(i, "", expires=0)

    return response

@app.route("/post", methods=["GET"])
def post_get():
    if request.cookies.get("loggedin") != "1":
        return make_response(render_template("redirect.html", page="/login"))

    return make_response(render_template("make_post.html"))

@app.route("/post", methods=["POST"])
def post_post():
    name = request.cookies.get("name")

    if name is None or request.cookies.get("loggedin") != "1":
        return make_response(render_template("redirect.html", page="/post"))

    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)

    if request.form.get("post") == None or len(request.form.get("post")) == 0 or len(request.form.get("post")) > 200:
        return make_response(render_template("redirect.html", page="/post"))

    database[name]["posts"].append(request.form.get("post"))

    with open("database.yml", "w") as database_file:
        yaml.dump(database, database_file)

    return make_response(render_template("redirect.html", page=f"/posts?name={name}"))

@app.route("/posts", methods=["GET"])
def posts_name():
    user = request.args.get("name")

    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)

    users = list(database.keys())
    users.sort(key=str.lower)

    if user is None:
        return make_response(render_template("users.html", users=users))

    user_posts = database[user]["posts"]
    user_bio = database[user]["bio"] if "bio" in database[user] else "No bio provided."
    user_posts.reverse()

    return make_response(render_template("posts.html", name=user, posts=user_posts, num_posts = len(user_posts), bio = user_bio))

@app.route("/view", methods=["GET"])
def view_get():
    user = request.args.get("name")
    pid = request.args.get("id")

    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)

    if not user in database:
        return make_response(render_template("redirect.html", page="/"))

    try:
        posts = database[user]["posts"]
        post = posts[int(pid)]
    except:
        return make_response(render_template("redirect.html", page="/"))

    return make_response(render_template("single_post.html", name=user, post=post))

@app.route("/settings", methods=["GET"])
def settings_get():
    if request.cookies.get("loggedin") != "1":
        return make_response(render_template("redirect.html", page="/login"))

    return make_response(render_template("settings.html"))

@app.route("/settings", methods=["POST"])
def settings_post():
    name = request.cookies.get("name")
    with open("database.yml") as database_file:
        database = yaml.load(database_file, yml_loader)

    if request.form.get("bio") is not None:
        database[name]["bio"] = request.form.get("bio")

    with open("database.yml", "w") as database_file:
        yaml.dump(database, database_file)

    return make_response(render_template("redirect.html", page="/posts"))