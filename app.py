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

"""                 ===      PROJECT (Home) related code  ===    """
@app.route("/")
@app.route("/get_projects")
def get_projects():
    flash("Home Flash Works!")
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
@app.route("/get_preferences")
def get_preferences():
    flash("get_preferences Flash Works!")
    return render_template("preferences_tbd.html")


"""                 ===      REGISTER/ LOGIN / LOGOUT related code  ===    """

@app.route("/register")
def register():
    flash("register Flash Works!")
    return render_template("register.html")

@app.route("/login")
def login():
    flash("login Flash Works!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    flash("logout Flash Works!")
    return render_template("login.html")


"""                 ===      USER related code  ===    """
@app.route("/get_users")
def get_users():
    flash("get_users Flash Works!")
    return render_template("users.html")

@app.route("/user_edit")
def user_edit():
    flash("user_edit Flash Works!")
    return render_template("user_edit.html")

@app.route("/user_add")
def user_add():
    flash("user_add Flash Works!")
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
