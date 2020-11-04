import os
from flask import (Flask, render_template, redirect, request, url_for,
                   flash, session)
from datetime import date
from flask_pymongo import PyMongo
from bson.objectid import ObjectId  # converts object ids
import bcrypt

# MIKE REMOVE AFTER Mentor Discussiontest werkzeug vs bcrypt
#from werkzeug.security import generate_password_hash, check_password_hash

environment = os.getenv("MS3_ENVIRONMENT")
print("Runtime environment detected: ", environment)
app = Flask(__name__)                       # *** Flask app
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["MONGO_URI"] = os.getenv("MS3_MONGO_URI")
app.config["MONGO_DBNAME"] = os.getenv("MS3_MONGO_DBN")
app.secret_key = os.getenv("MS3_SECRET_KEY")


# *** wires PyMongo to the APP and saves mongo
mongo = PyMongo(app)

"""                 ===      PROJECT (Home) related code  ===    """


@app.route("/")
@app.route("/get_projects")
def get_projects():
    if session.get("ACCOUNT") is None:
        flash("You must login first")
        return redirect(url_for("login"))

    if session.get("ACTIVE_USER") is None:
        flash("You must select your user name")
        return redirect(url_for("user_select"))


    return render_template("projects.html")


@app.route("/project_add")
def project_add():
    flash("project_add Flash Works!")
    return render_template("project_add.html")


@app.route("/project_edit")
def project_edit():
    flash("projects_edit Flash Works!")
    return render_template("projects_edit.html")


@app.route("/projects_search")
def projects_search():
    flash("projects_search Flash Works!")
    return render_template("projects_search.html")


"""                 ===      CATEGORY related code  ===    """


@app.route("/get_categories")
def get_categories():
    flash("get_categories Flash Works!")
    return render_template("categories.html")


@app.route("/category_add")
def category_add():
    flash("category_add Flash Works!")
    return render_template("category_add.html")


@app.route("/category_edit")
def category_edit():
    flash("category_edit Flash Works!")
    return render_template("category_edit.html")


"""                 ===      PREFERENCE related code  (TBD)===    """

#MIKE REMOVE IF NOT USED 
@app.route("/get_preferences")
def get_preferences():
    flash("get_preferences Flash Works!")
    return render_template("preferences_tbd.html")


"""                 ===      REGISTER/ LOGIN / LOGOUT related code  ===    """


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if account already exists in DB
        existing_user = mongo.db.users.find_one(
            {"account_name": request.form.get("account_name").lower()},
            {"user_type": "account"})

        if existing_user:
            flash("Account name unavailable.")
            return redirect(url_for("register"))

        """ MIKE, REMOVE after discussion with Mentor           
                #  password field for match validation done in the html
                bcrypt_hashed_password = bcrypt.hashpw(bytes(request.form.get("password"), "utf-8"), bcrypt.gensalt())
                werkzeug_hashed_password = generate_password_hash(request.form.get("password"))

                #  Just confirm the hased values are correct
                if check_password_hash(werkzeug_hashed_password, request.form.get("password")):
                    print("werkzeug_hashed_password is OK")
                if bcrypt.checkpw(bytes(request.form.get("password"), "utf-8"), bcrypt_hashed_password):
                    print("bcrypt_hashed_password is OK")
        """
        bcrypt_hashed_password = bcrypt.hashpw(bytes(request.form.get("password"), 
            "utf-8"), bcrypt.gensalt())

        register_data = {    # dictionary for insert
            "account_name": request.form.get("account_name").lower(),
            "account_password": bcrypt_hashed_password,
            "user_type": "account",
            "account_status": "active",         # possibly locked in future?
            "date_created": date.today().strftime("%d %B, %Y")
        }

        # add the new account
        mongo.db.users.insert_one(register_data)

        # put the new user into flask "session"
        session["ACCOUNT"] = request.form.get("account_name").lower()
        flash("Registration Successful")

        return redirect(url_for("get_users", account_name=session.get("ACCOUNT")))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if account already exists in DB
        existing_user = mongo.db.users.find_one(
            {"account_name": request.form.get("account_name").lower(), "user_type": "account"})

        """ MIKE, REMOVE after discussion with Mentor
                            # Now, check the passwords from the database 
                            if check_password_hash(existing_user["werkzeug_hashed_password"], request.form.get("password")):
                                print("werkzeug_hashed_password is OK")
                            else: 
                                print("bcrypt_hashed_password FAILED")

                            if bcrypt.checkpw(bytes(request.form.get("password"), "utf-8"), existing_user["bcrypt_hashed_password"]):
                                print("bcrypt_hashed_password is OK")
                            else: 
                                print("bcrypt_hashed_password FAILED")

                            return redirect(url_for("login"))
            """
        if existing_user:
            # now compare that against the one in the DB
            if bcrypt.checkpw(bytes(request.form.get("password"), "utf-8"), existing_user["account_password"]):
                # Creds are good, so set account in session and send it to select a user
                session["ACCOUNT"] = request.form.get("account_name").lower()
                flash("Account login Successful")
                return redirect(url_for("get_users"))
        flash("User name and / or password incorrect.  Please retry or register.")

    # Appears that creds are no good, ask them to retry.
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    # remove user & account from Flask session (NOT the cookie)

    if session.get("ACCOUNT") is None:
        flash("You were already logged out")
    else:
        session.pop("ACCOUNT")

    if session.get("ACTIVE_USER") is not None:
        session.pop("ACTIVE_USER")

    flash("You are logged out")
    
    return redirect(url_for("login"))


"""                 ===      USER related code  ===    """


@app.route("/get_users")
def get_users():
    # MIKE ADD TRY CATCH.  Now just confirm we have the account active
    if session.get("ACCOUNT") is None:
        flash("You must login first")
        return redirect(url_for("login"))

    if session.get("ACTIVE_USER") is None:
        flash("You must select a user name")
        return redirect(url_for("user_select"))

    users = list(mongo.db.users.find(
        {"user_type": "user", "account_name": session.get("ACCOUNT")}).sort("username", 1))
    if len(users) == 0:
        flash("Please add a user to get started")
        return render_template("user_add.html")
    return render_template("users.html", users=users)


@app.route("/user_edit")
def user_edit():
    flash("user_edit Flash Works!")
    return render_template("user_edit.html")

@app.route("/user_select")
def user_select():
    users = list(mongo.db.users.find(
        {"user_type": "user", "account_name": session.get("ACCOUNT")}).sort("username", 1))
    if len(users) == 0:
        flash("Please add a user to get started")
        return render_template("user_add.html")
    return render_template("user_select.html", users=users)

@app.route("/user_set/<user_name>")
def user_set(user_name):
    if session.get("ACTIVE_USER") is not None:
        session.pop("ACTIVE_USER")
    session["ACTIVE_USER"] = user_name
    flash_message =("User: ", user_name,  "is now active.")
    flash(flash_message)
    
    return redirect(url_for("get_projects"))



# MIKE Add some defensive programing here specially existing session data


@app.route("/user_add", methods=["GET", "POST"])
def user_add():
    if request.method == "POST":
        # See if this is the first user added and make it active in session
        users_exist = len(list(mongo.db.users.find(
            {"user_type": "user", "username": session.get("ACCOUNT")})))

        # Check if account/user already exists
        existing_user = mongo.db.users.find_one(
            {"user_name": request.form.get("user_name").lower(),
             "account_name": session.get("ACCOUNT"),
             "user_type": "user"})

        if existing_user:
            flash("User name already exists.  Please try a new one")
            return redirect(url_for("get_users"))

        user_data = {    # dictionary for insert
            "account_name": session.get("ACCOUNT"),
            "password": "",
            "user_type": "user",
            "user_name": request.form.get("user_name"),
            "user_notes": request.form.get("user_notes"),
            "account_status": "active",         # possibly locked in future?
            "date_created": date.today().strftime("%d %B, %Y"),
            "user_points:": 0
        }

        mongo.db.users.insert_one(user_data)
        flash("New user Added")

        # if the initial user count was 0, this user can be set as the active user in session
        if users_exist == 0:
            session["ACTIVE_USER"] = request.form.get("user_name").lower()
        return redirect(url_for("get_users"))

    return render_template("user_add.html")


"""
    Select the correct environment 
"""
if environment == "flask":
    if __name__ == '__main__':
        app.run(use_debugger=False, use_reloader=False,
                passthrough_errors=True)

elif environment == "vscode":
    if __name__ == '__main__':
        app.run(use_debugger=True, use_reloader=False,
                passthrough_errors=True)


elif environment == "heroku":
    if __name__ == '__main__':
        app.run(host=os.environ.get('IP', "0.0.0.0"),
                port=int(os.environ.get('PORT', "5000")),
                debug=False)

else:
    print(" Unknown environment")
