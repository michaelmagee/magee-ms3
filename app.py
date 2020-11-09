import os
from flask import (Flask, render_template, redirect, request, url_for,
                   flash, session)
from datetime import date
from flask_pymongo import PyMongo
from bson.objectid import ObjectId  # converts object ids
import bcrypt

environment = os.getenv("MS3_ENVIRONMENT")
print("Runtime environment detected: ", environment)
app = Flask(__name__)                       # *** Flask app
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["MONGO_URI"] = os.getenv("MS3_MONGO_URI")
app.config["MONGO_DBNAME"] = os.getenv("MS3_MONGO_DBN")
app.secret_key = os.getenv("MS3_SECRET_KEY")

# *** wires PyMongo to the APP and saves mongo
mongo = PyMongo(app)

"""
TO DO:
    - ALL try/except send the user back to home and do not handle specific exception types.
        Revisit return flow and see if there's a better way to inetrcept potential
        database errors abd get failure info
    - look at class="brand-logo"> for header wrap
"""

"""                 ===      PROJECT (Home) related code  ===    """


@app.route("/")
def get_projects():
    if session.get("ACCOUNT") is None:
        flash("You must login first")
        return redirect(url_for("login"))

    if session.get("ACTIVE_USER") is None:
        flash("You must select your user name")
        return redirect(url_for("user_select"))

    return render_template("projects.html")


@app.route("/project_add", methods=["GET", "POST"])
def project_add():
    if request.method == "POST":
        project_is_urgent = "on" if request.form.get("project_is_urgent") else "off"
        new_project = {
            "project_category_name": request.form.get("project_category_name"),
            "project_name": request.form.get("project_name"),
            "project_description": request.form.get("project_description"),
            "project_due_date": request.form.get("project_due_date"),
            "project_is_urgent": project_is_urgent,
            "project_status": "new",
            "project_date_created": date.today().strftime("%d %B, %Y"),
            "project_created_by": session["ACTIVE_USER"]   # will be username not logged name
        }
        mongo.db.projects.insert_one(new_project)
        flash("Task Added")
        return redirect(url_for("get_projects"))

    # else it's a get
    all_categories = list(mongo.db.categories.find().sort(
        "category_name", 1))  # sort ascending
    return render_template("project_add.html", categories=all_categories)




@app.route("/project_edit")
def project_edit():
    return render_template("projects_edit.html")


@app.route("/projects_search")
def projects_search():
    return render_template("projects_search.html")


"""                 ===      CATEGORY related code  ===
NOTE:   Concern here is that deleting a category associated projects will leave "broken"
        relationships between projects and catagories.
"""


@app.route("/get_categories")
def get_categories():

    try:
        categories = list(mongo.db.categories.find(
            {"account_name": session.get("ACCOUNT")}))
    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"

    if len(categories) == 0:
        flash("Please add a category to get started")
        return render_template("category_add.html")

    # here is where will embed the category counts
    """
        for cat in categories:
            Get the count of projects in major states for each one
            cat["number_new"] = result
    """
    return render_template("categories.html", categories=categories)


@app.route("/category_add", methods=["GET", "POST"])
def category_add():
    if request.method == "POST":

        # Check if category already exists  (No lower case issues) 
        try:
            existing_cat = mongo.db.categories.find_one(
                {"category_name": request.form.get("category_name"),
                "account_name": session.get("ACCOUNT")
                })
        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

        if existing_cat:
            flash("Category name already exists.  Please try a new one")
            return redirect(url_for("category_add"))

        category_data = {    # dictionary for insert
            "account_name": session.get("ACCOUNT"),
            "category_name": request.form.get("category_name"),
            "category_notes": request.form.get("category_notes"),
            "date_created": date.today().strftime("%d %B, %Y"),
            "created_by": session.get("ACTIVE_USER")
        }
        try:
            mongo.db.categories.insert_one(category_data)
        except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

        flash("Category Added")
        return redirect(url_for("get_categories"))

    # NOT a post so send along to category_add
    return render_template("category_add.html")

"""                 
NOTE:   Concern here is that editing a category name associated projects will leave "broken"
        relationships between projects and catagories.  Will need to revisit this.
        Consider doing a mass update of name for targeted projects?
"""
@app.route("/category_edit/<category_id>", methods=["GET", "POST"])
def category_edit(category_id):
    if request.method == "POST":
        try:
            # retain non displayed values, note: uspsert appears to be false in the doc
            mongo.db.categories.update( {'_id': ObjectId(category_id)},   
            {"$set": {'category_name': request.form.get('category_name'),
                "category_notes": request.form.get('category_notes') }} )
        except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

        return redirect(url_for("get_categories"))

    # Not a post, so get the row and send it to the edit page
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("category_edit.html", category=category)


"""                 
NOTE:   Concern here is that deleting a category associated projects will leave "broken"
        relationships between projects and catagories.  Will need to revisit this
"""
@app.route("/category_delete/<category_id>")
def category_delete(category_id):
    try:
        mongo.db.categories.remove({"_id": ObjectId(category_id)})
    except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

    flash("Category Deleted")
    return redirect(url_for("get_categories"))



"""                 ===      PREFERENCE related code  (TBD)===    """

# MIKE REMOVE IF NOT USED 
@app.route("/get_preferences")
def get_preferences():
    return render_template("preferences_tbd.html")


"""                 ===      REGISTER/ LOGIN / LOGOUT related code  ===    """


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if account already exists in DB
        try:
            existing_user = mongo.db.users.find_one(
                {"account_name": request.form.get("account_name").lower()},
                {"user_type": "account"})
        except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

        if existing_user:
            flash("Account name unavailable.")
            return redirect(url_for("register"))

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
        try:
            mongo.db.users.insert_one(register_data)
        except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

        # put the new user into flask "session"
        session["ACCOUNT"] = request.form.get("account_name").lower()
        flash("Registration Successful")

        return redirect(url_for("get_users", account_name=session.get("ACCOUNT")))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if account already exists in DB
        try:
            existing_user = mongo.db.users.find_one(
                {"account_name": request.form.get("account_name").lower(), "user_type": "account"})
        except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

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
    # remove user, account and admin status from Flask session (NOT the cookie)

    if session.get("ACCOUNT") is None:
        flash("You were already logged out")
    else:
        session.pop("ACCOUNT")

    if session.get("ACTIVE_USER") is not None:
        session.pop("ACTIVE_USER")

    if session.get("ACTIVE_ADMIN") is not None:
        session.pop("ACTIVE_ADMIN")
        
    flash("You are logged out")
    
    return redirect(url_for("login"))


"""                 ===      USER related code  ===    """
@app.route("/get_users")
def get_users():
    
    if session.get("ACCOUNT") is None:
        flash("You must login first")
        return redirect(url_for("login"))

    if session.get("ACTIVE_USER") is None:
        flash("You must select a user name")
        return redirect(url_for("user_select"))
    # get users
    try:
        users = list(mongo.db.users.find(
            {"user_type": "user", "account_name": session.get("ACCOUNT")}).sort("username", 1))
    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"

    if len(users) == 0:
        flash("Please add a user to get started")
        return render_template("user_add.html")

    return render_template("users.html", users=users)

"""                 
NOTE:   Concern here is that editing a user associated projects will leave "broken"
        relationships between projects and users.  Will need to revisit this
"""
@app.route("/user_edit/<user_id>", methods=["GET", "POST"])
def user_edit(user_id):
    if request.method == "POST":
        try:
            # retain non displayed values, note: uspsert appears to be false in the doc
            mongo.db.users.update( {'_id': ObjectId(user_id)},   
            {"$set": {'user_name': request.form.get('user_name'),
                "user_notes": request.form.get('user_notes') }} )
        except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

        return redirect(url_for("get_users"))

    # Not a post, so get the row and send it to the edit page
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return render_template("user_edit.html", user=user)

"""                 
NOTE:   Concern here is that deleting a user associated projects will leave "broken"
        relationships between projects and users.  Will need to revisit this
        For now, only an "admin" can do it 
"""
@app.route("/user_delete/<user_id>")
def user_delete(user_id):
    try:
        mongo.db.users.remove({"_id": ObjectId(user_id)})
    except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

    flash("User Deleted")
    return redirect(url_for("get_users"))


@app.route("/user_select")
def user_select():
    try:
        users = list(mongo.db.users.find(
            {"user_type": "user", "account_name": session.get("ACCOUNT")}).sort("username", 1))
    except: 
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

    if len(users) == 0:
        flash("Please add a user to get started")
        return render_template("user_add.html")

    return render_template("user_select.html", users=users)

# sets the active "User" 
@app.route("/user_set/<user_name>")
def user_set(user_name):
    try:
       new_user = mongo.db.users.find_one(
            {"user_name": user_name,
             "account_name": session.get("ACCOUNT"),
             "user_type": "user"})
    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"
    
    # set the active user name
    if session.get("ACTIVE_USER") is not None:
        session.pop("ACTIVE_USER")
    session["ACTIVE_USER"] = user_name

    # set the admin status of the user 
    if session.get("ACTIVE_ADMIN") is not None:
        session.pop("ACTIVE_ADMIN")
    session["ACTIVE_ADMIN"] = new_user["user_admin"]

    flash_message =("User: ", user_name,  "is now active.")
    flash(flash_message)
    
    return redirect(url_for("get_projects"))

@app.route("/user_add", methods=["GET", "POST"])
def user_add():
    if request.method == "POST":
        account_name = session.get("ACCOUNT")
        # See if this is the first user added and make it active in session 
        users_exist = len(list(mongo.db.users.find(
            {"user_type": "user", "account_name": account_name })))

        # Check if account/user already exists
        existing_user = mongo.db.users.find_one(
            {"user_name": request.form.get("user_name").lower(),
             "account_name": account_name,
             "user_type": "user"})

        if existing_user:
            flash("User name already exists.  Please try a new one")
            return redirect(url_for("get_users"))
        
        # If this is the first user added after account creation, 
        # make this user an admin
        if users_exist == 0:
            user_admin = True
        else:
            user_admin = False
        user_data = {    # dictionary for insert
            "account_name": account_name,
            "password": "",
            "user_type": "user",
            "user_admin": user_admin,
            "user_name": request.form.get("user_name").lower(),
            "user_notes": request.form.get("user_notes"),
            "account_status": "active",         # possibly locked in future?
            "date_created": date.today().strftime("%d %B, %Y"),
            "created_by": session.get("ACTIVE_USER"),
            "user_points": 0
        }

        mongo.db.users.insert_one(user_data)
        flash("New user Added")

        # if the initial user count was 0, this user can be set as the active user in session
        # Also add the  fact that they are an admin 
        if users_exist == 0:
            session["ACTIVE_USER"] = request.form.get("user_name").lower()
            session["ACTIVE_ADMIN"] = user_admin

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
