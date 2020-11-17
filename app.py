#
# Mike Magee  Milestone 3 for Code Institute
# Final 11/17/2020
#

import os
from flask import (Flask, render_template, redirect, request, url_for,
                   flash, session, abort)
from datetime import date
from flask_pymongo import PyMongo
import pymongo
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

# Common values for dropdowns
HOURS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
PRIORITIES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
POINTS = [1, 5, 10, 15, 20, 25]

# used in Pop A Project
POPS = [1, 3, 5]    # limit number of popped projects
SORT_TYPES = [{"sort_type": "pymongo.DESCENDING",
               "display_name": "Descending"},
              {"sort_type": "pymongo.ASCENDING",
               "display_name": "Ascending"}]

SORT_FIELDS = [{"field_name": "project_points",
                "display_name": "Project Points"},
               {"field_name": "project_priority",
                "display_name": "Project Priority"},
               {"field_name": "project_hour_estimate",
                "display_name": "Project Duration Estimate"}]

"""                 ===      PROJECT (Home) related code  ===    """


@app.route("/")
@app.route("/<project_state>")
def get_projects(project_state=""):

    if session.get("ACCOUNT") is None:
        flash("Please register or login first")
        return redirect(url_for("login"))

    if session.get("ACTIVE_USER") is None:
        flash("Please select your user name")
        return redirect(url_for("user_select"))
    try:
        # pass along project counts  Probably a better way to do this
        # via some aggregation or something
        status_counts = {}
        status_counts["closed"] = mongo.db.projects.count_documents(
                {"project_status": "closed",
                    "project_account_name": session["ACCOUNT"]})

        status_counts["new"] = \
            mongo.db.projects.count_documents(
                                {"project_status": "new",
                                 "project_account_name":
                                 session["ACCOUNT"]})

        status_counts["open"] = mongo.db.projects.count_documents(
                {"project_status": "open",
                    "project_account_name": session["ACCOUNT"]})

        # send totals in as well
        status_counts["total"] = (status_counts["open"] +
                                  status_counts["new"] +
                                  status_counts["closed"])

        # determine of view is filtered by state
        if project_state == "closed":
            projects = list(mongo.db.projects.find({"project_status": "closed",
                            "project_account_name": session["ACCOUNT"]}))

        elif project_state == "open":
            projects = list(mongo.db.projects.find({"project_status": "open",
                            "project_account_name": session["ACCOUNT"]}))

        elif project_state == "new":
            projects = list(mongo.db.projects.find({"project_status": "new",
                            "project_account_name": session["ACCOUNT"]}))

        else:
            # show all open and new but hide the closed ones
            projects = list(mongo.db.projects.find(
                {"project_status": {"$ne": "closed"},
                    "project_account_name": session["ACCOUNT"]}))

        return render_template("projects.html",
                               projects=projects,
                               status_counts=status_counts,
                               status_type=project_state)

    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html", projects=projects,
                               status_counts=status_counts,
                               status_type=project_state)


# Add a new project
@app.route("/project_add", methods=["GET", "POST"])
def project_add():
    if request.method == "POST":
        project_is_urgent = \
            "on" if request.form.get("project_is_urgent") else "off"
        new_project = {
            "project_category_name": request.form.get("project_category_name"),
            "project_name": request.form.get("project_name"),
            "project_description": request.form.get("project_description"),
            "project_due_date": request.form.get("project_due_date"),
            "project_is_urgent": project_is_urgent,
            "project_status": "new",
            "project_priority": request.form.get("project_priority", type=int),
            "project_points": request.form.get("project_points", type=int),
            "project_hour_estimate": request.form.get(
                            "project_hour_estimate", type=int),
            "project_date_created": date.today().strftime("%d %B, %Y"),
            "project_created_by": session["ACTIVE_USER"],
            "project_account_name": session["ACCOUNT"],
            "project_date_opened": "",
            "project_opened_by": "",
            "project_date_closed": "",
            "project_closed_by": ""

        }
        try:

            mongo.db.projects.insert_one(new_project)
            flash("Project Added")
            return redirect(url_for("get_projects"))
        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

    # else it's a get
    all_categories = list(mongo.db.categories.find(
                        {"account_name": session.get("ACCOUNT")}).sort(
                        "category_name", 1))  # sort ascending

    return render_template("project_add.html", categories=all_categories,
                           priorities=PRIORITIES, points=POINTS,
                           hours=HOURS)


# "Pop" (help me select a project)
@app.route("/project_pop", methods=["GET", "POST"])
def project_pop():
    if request.method == "POST":
        flash("Processing Pops :" + request.form.get("pops_requested"))

        try:
            # pass along project counts  Probably a better way to do this
            # via some aggregation or something
            status_counts = {}
            status_counts["closed"] = mongo.db.projects.count_documents(
                    {"project_status": "closed",
                        "project_account_name": session["ACCOUNT"]})

            status_counts["new"] = \
                mongo.db.projects.count_documents(
                                        {"project_status": "new",
                                         "project_account_name":
                                         session["ACCOUNT"]})

            status_counts["open"] = mongo.db.projects.count_documents(
                    {"project_status": "open",
                        "project_account_name": session["ACCOUNT"]})

            # send totals in as well
            status_counts["total"] = (status_counts["open"] +
                                      status_counts["new"])

            # ONLY show the new projects
            query = {"project_account_name": session["ACCOUNT"],
                     "project_status": "new"}
            sort_field = request.form.get("sort_requested")
            xsort_direction = request.form.get("xsort_direction")
            pops_requested = request.form.get("pops_requested", type=int)
            sort_direction = pymongo.DESCENDING
            if xsort_direction == "pymongo.ASCENDING":
                sort_direction = pymongo.ASCENDING

            projects = list(mongo.db.projects.find(query).
                            sort(sort_field, sort_direction).
                            limit(pops_requested))

            return render_template("projects.html",
                                   projects=projects,
                                   status_counts=status_counts,
                                   status_type="popped")

        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html", projects=projects,
                                   status_counts=status_counts,
                                   status_type="popped")

    # else it's a get - render the page
    return render_template("project_pop.html", pops=POPS,
                           sort_types=SORT_TYPES,
                           sort_fields=SORT_FIELDS)


# change status to closed
@app.route("/project_close/<project_id>")
def project_close(project_id):
    try:
        mongo.db.projects.find_one_and_update(
                    {"_id": ObjectId(project_id)},
                    {"$set": {"project_status": "closed",
                              "project_date_closed":
                              date.today().strftime("%d %B, %Y"),
                              "project_closed_by": session["ACTIVE_USER"]}})

        flash("Project Closed")

        # Now grab the points for this project
        # and increment the balance of the user doing it
        project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
        mongo.db.users.find_one_and_update(
                                {"account_name": session["ACCOUNT"],
                                    "user_name": session["ACTIVE_USER"]},
                                {"$inc":
                                    {"user_points":
                                     project["project_points"]}})

        return redirect(url_for("get_projects"))

    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"


# change status to open
@app.route("/project_open/<project_id>")
def project_open(project_id):

    try:
        mongo.db.projects.find_one_and_update(
                    {"_id": ObjectId(project_id)},
                    {"$set": {"project_status": "open",
                              "project_date_opened":
                              date.today().strftime("%d %B, %Y"),
                              "project_opened_by": session["ACTIVE_USER"]}})

        flash("Project Opened")
        return redirect(url_for("get_projects"))

    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"


# Edit the Project
@app.route("/project_edit/<project_id>", methods=["GET", "POST"])
def project_edit(project_id):
    if request.method == "POST":
        project_is_urgent = \
            "on" if request.form.get("project_is_urgent") else "off"
        try:
            p = mongo.db.projects
            p.find_one_and_update(
                {"_id": ObjectId(project_id)},
                {"$set":
                    # Easier to read on one line but PEP8 says NO!
                    {"project_category_name":
                        request.form.get("project_category_name"),
                     "project_name":
                        request.form.get("project_name"),
                     "project_description":
                        request.form.get("project_description"),
                     "project_due_date":
                        request.form.get("project_due_date"),
                     "project_is_urgent":
                        project_is_urgent,
                     "project_priority":
                        request.form.get("project_priority", type=int),
                     "project_points":
                        request.form.get("project_points", type=int),
                     "project_hour_estimate":
                        request.form.get("project_hour_estimate", type=int)}})

            flash("Project Updated")
            return redirect(url_for("get_projects"))

        except:
            flash("Error accessing the database.  Please retry")
            return redirect(url_for("get_projects"))

    # else it's a get
    # get the project/categories necessary and pass to the project_edit.html
    try:
        project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
        all_categories = list(mongo.db.categories.find(
                            {"account_name": session.get("ACCOUNT")}).sort(
                                "category_name", 1))  # sort ascending

        return render_template("project_edit.html", project=project,
                               categories=all_categories,
                               priorities=PRIORITIES, points=POINTS,
                               hours=HOURS)

    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"


# View closed projects with all fields
@app.route("/project_view/<project_id>", methods=["GET", "POST"])
def project_view(project_id):
    if request.method == "POST":
        return redirect(url_for("get_projects"))

    # else it's a get
    # get project/categories for project_edit.html
    try:
        project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
        return render_template("project_view.html", project=project)

    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"

"""                 ===      CATEGORY related code  ===
NOTE:   Concern here is that deleting a category associated
        projects will leave "broken"
        relationships between projects and catagories.
"""


# Get the categories
@app.route("/get_categories")
def get_categories():

    try:
        categories = list(mongo.db.categories.find(
                            {"account_name": session.get("ACCOUNT")}))
    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")

    if len(categories) == 0:
        flash("Please add a category to get started")
        return render_template("category_add.html")

    # embed the category counts
    for cat in categories:

        # Get all of the totals for various categories
        category_project_count_closed = mongo.db.projects.count_documents(
                            {"project_status": "closed",
                             "project_category_name": cat["category_name"],
                             "project_account_name":
                                session["ACCOUNT"]})

        category_project_count_open = mongo.db.projects.count_documents(
                            {"project_status": "open",
                             "project_category_name": cat["category_name"],
                             "project_account_name":
                                session["ACCOUNT"]})

        category_project_count_new = mongo.db.projects.count_documents(
                            {"project_status": "new",
                             "project_category_name": cat["category_name"],
                             "project_account_name":
                                session["ACCOUNT"]})

        cat["category_project_count_closed"] = category_project_count_closed
        cat["category_project_count_open"] = category_project_count_open
        cat["category_project_count_new"] = category_project_count_new

        cat["category_project_count_total"] = (category_project_count_new +
                                               category_project_count_open +
                                               category_project_count_closed)

    return render_template("categories.html", categories=categories)


# add a Category
@app.route("/category_add", methods=["GET", "POST"])
def category_add():
    if request.method == "POST":

        # Check if category already exists  (No lower case issues)
        try:
            existing_cat = mongo.db.categories.find_one(
                        {"category_name": request.form.get("category_name"),
                         "account_name": session.get("ACCOUNT")})

        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")  # send them back to "home"

        if existing_cat:
            flash("Category name already exists.  Please try a new one")
            return redirect(url_for("category_add"))

        category_data = {"account_name": session.get("ACCOUNT"),
                         "category_name": request.form.get("category_name"),
                         "category_notes": request.form.get("category_notes"),
                         "date_created": date.today().strftime("%d %B, %Y"),
                         "created_by": session.get("ACTIVE_USER")}

        try:
            mongo.db.categories.insert_one(category_data)

        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

        flash("Category Added")
        return redirect(url_for("get_categories"))

    # NOT a post so send along to category_add
    return render_template("category_add.html")

"""
NOTE:   Concern here is that editing a category name associated
        projects will leave "broken" relationships between projects
        and catagories.  Will need to revisit this.
        Consider doing a mass update of name for targeted projects?
"""


# Category editing
@app.route("/category_edit/<category_id>", methods=["GET", "POST"])
def category_edit(category_id):
    if request.method == "POST":
        try:
            # retain non displayed values,
            # note: uspsert appears to default to false in the doc
            mongo.db.categories.update({"_id": ObjectId(category_id)},
                                       {"$set":
                                       {"category_name":
                                        request.form.get("category_name"),
                                        "category_notes":
                                        request.form.get("category_notes")}})

        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

        return redirect(url_for("get_categories"))

    # Not a post, so get the row and send it to the edit page
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("category_edit.html", category=category)


"""
NOTE:   Concern here is that deleting a category associated
        projects will leave "broken" relationships between projects
        and catagories.  Will need to revisit this
"""


# delete a category
@app.route("/category_delete/<category_id>")
def category_delete(category_id):
    try:
        mongo.db.categories.remove({"_id": ObjectId(category_id)})

    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")  # send them back to "home"

    flash("Category Deleted")
    return redirect(url_for("get_categories"))


"""                 ===      REGISTER/ LOGIN / LOGOUT related code  ===    """


# Register a new account
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
            return render_template("projects.html")

        if existing_user:
            flash("Account name unavailable.")
            return redirect(url_for("register"))

        bcrypt_hashed_password = bcrypt.hashpw(
                                    bytes(request.form.get("password"),
                                          "utf-8"), bcrypt.gensalt())

        register_data = {
                    "account_name": request.form.get("account_name").lower(),
                    "account_password": bcrypt_hashed_password,
                    "user_type": "account",
                    "account_status": "active",   # possibly locked in future?
                    "date_created": date.today().strftime("%d %B, %Y")
                }

        # add the new account
        try:
            mongo.db.users.insert_one(register_data)
        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

        # put the new user into flask "session"
        session["ACCOUNT"] = request.form.get("account_name").lower()

        # add a few default categories just to get them started
        home_category = {
                        "account_name": session.get("ACCOUNT"),
                        "category_name": "Home",
                        "category_notes": "Home related category",
                        "date_created": date.today().strftime("%d %B, %Y"),
                        "created_by": "default"
                    }

        work_category = {
                        "account_name": session.get("ACCOUNT"),
                        "category_name": "Work",
                        "category_notes": "Work related category",
                        "date_created": date.today().strftime("%d %B, %Y"),
                        "created_by": "default"
                    }

        other_category = {
                        "account_name": session.get("ACCOUNT"),
                        "category_name": "Other",
                        "category_notes": "Other category",
                        "date_created": date.today().strftime("%d %B, %Y"),
                        "created_by": "default"
                    }

        try:
            mongo.db.categories.insert_one(home_category)
            mongo.db.categories.insert_one(work_category)
            mongo.db.categories.insert_one(other_category)

        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

        flash("Registration Successful")

        return redirect(url_for("get_users",
                                account_name=session.get("ACCOUNT")))

    # Just a "get", so serve the form
    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if account already exists in DB
        try:
            existing_user = mongo.db.users.find_one(
                {"account_name": request.form.get("account_name").lower(),
                    "user_type": "account"})

        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

        if existing_user:
            # now compare that against the one in the DB
            if bcrypt.checkpw(bytes(request.form.get("password"), "utf-8"),
                              existing_user["account_password"]):
                # Creds are good, so set account in session
                # and send it to select a user
                session["ACCOUNT"] = request.form.get("account_name").lower()

                flash("Account login Successful")
                return redirect(url_for("get_users"))

        flash("User name and / or password incorrect.  \
                Please retry or register.")

    # Appears that creds are no good, ask them to retry.
    return render_template("login.html")


# Handle Logout
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

    if session.get("ACCOUNT") is not None:
        session.pop("ACCOUNT")

    flash("You are logged out")

    return redirect(url_for("login"))


"""                 ===      USER related code  ===    """


# Get users here
@app.route("/get_users")
def get_users():

    if session.get("ACCOUNT") is None:
        flash("You must login first")
        return redirect(url_for("login"))

    if session.get("ACTIVE_USER") is None:
        return redirect(url_for("user_select"))
    # get users
    try:
        users = list(mongo.db.users.find(
            {"user_type": "user",
             "account_name": session.get("ACCOUNT")}).sort("username", 1))

    except:
        flash("Error accessing the database.  Please retry")
        return render_template("projects.html")

    if len(users) == 0:
        flash("Please add a user to get started")
        return render_template("user_add.html")

    return render_template("users.html", users=users)

"""
NOTE:   Concern here is that editing a user associated
        projects will leave "broken"
        relationships between projects and users.
        Will need to revisit this
"""


# user Edit here
@app.route("/user_edit/<user_id>", methods=["GET", "POST"])
def user_edit(user_id):
    update_active_user = False
    if request.method == "POST":
        try:
            # get the user_name being updated here
            # see if the user_name has changed
            u = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if u["user_name"] != request.form.get("user_name"):
                update_active_user = True

            # If this is an admin, respect the admin switch, else no
            user_admin = False
            if request.form.get("user_admin") == "on":
                user_admin = True

            if session.get("ACTIVE_ADMIN") is not None:
                # Make sure that the last admin is not turned off.
                # Get a count and make sure it's at least 1
                admin_count = mongo.db.users.count_documents(
                    {"user_type": "user", "user_admin": True,
                     "account_name": session.get("ACCOUNT")})

                # should never be 0, but just in case
                if admin_count <= 1 and request.form.get("user_admin") != "on":
                    # We know it's an admin doing this,
                    # and that admin is the only one-force admin to stay true
                    user_admin = True
                    flash("Unable to remove admin role\
                        from only remaining admin.")

                mongo.db.users.update(
                        {"_id": ObjectId(user_id)},
                        {"$set":
                            {"user_name": request.form.get("user_name"),
                             "user_notes": request.form.get("user_notes"),
                             "user_admin": user_admin}})

                # FINALLY, if user is active and removed their own admin priv,
                # remove the fact that they are an admin by popping it off
                # the session Note user/active user set this way to make PEP8
                # happy.  Also update the ACTIVE_USER NAME is changed
                user = request.form.get("user_name")
                active_user = session.get("ACTIVE_USER")
                if (user == active_user and user_admin is False):
                    session.pop("ACTIVE_ADMIN")

            else:
                mongo.db.users.update(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"user_name": request.form.get("user_name"),
                              "user_notes": request.form.get("user_notes")}})

        except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

        # if the username has changed for the active user, set the active user
        if update_active_user is True:
            session.pop("ACTIVE_USER")  # not sure I need this, just in case
            session["ACTIVE_USER"] = request.form.get("user_name")

        return redirect(url_for("get_users"))

    # Not a post, so get the row and send it to the edit page
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return render_template("user_edit.html", user=user)

"""
NOTE:   Concern here is that deleting a user associated projects
        will leave "broken" relationships between projects and users.
        Will need to revisit this For now, only an "admin" can do it
"""


# Delete User, but not if it's the last admin
@app.route("/user_delete/<user_id>")
def user_delete(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user["user_name"] == session.get("ACTIVE_USER"):
            # Make sure that the last admin is not turned off.
            # Get a count and make sure it's at least 1
            # remember that I can't be here unless I'm an admin
            admin_count = mongo.db.users.count_documents(
                    {"user_type": "user", "user_admin": True,
                     "account_name": session.get("ACCOUNT")})

            # At this point, we know that I'm deleting myself and
            # I'm the last admin.  Disallow tghis and return to users
            if admin_count <= 1:
                flash("Unable to remove the only known admin. \
                        Please create another one first.")
                return redirect(url_for("get_users"))

    except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

    try:
        mongo.db.users.remove({"_id": ObjectId(user_id)})

    except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

    # if the user whacked themselves, go set a new one
    if user["user_name"] == session.get("ACTIVE_USER"):
        flash("Self Deleted - You must now select a new user name")
        return redirect(url_for("user_select"))

    flash("User Deleted")
    return redirect(url_for("get_users"))


# Select User
@app.route("/user_select")
def user_select():
    try:
        users = list(mongo.db.users.find(
            {"user_type": "user",
             "account_name": session.get("ACCOUNT")}).sort("username", 1))

    except:
            flash("Error accessing the database.  Please retry")
            return render_template("projects.html")

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
        return render_template("projects.html")

    # set the active user name
    if session.get("ACTIVE_USER") is not None:
        session.pop("ACTIVE_USER")
    session["ACTIVE_USER"] = user_name

    # set the admin status of the user
    if session.get("ACTIVE_ADMIN") is not None:
        session.pop("ACTIVE_ADMIN")

    session["ACTIVE_ADMIN"] = new_user["user_admin"]

    flash(user_name + "  is now active.")
    return redirect(url_for("get_projects", project_state=""))


# Add a User
@app.route("/user_add", methods=["GET", "POST"])
def user_add():
    if request.method == "POST":
        account_name = session.get("ACCOUNT")
        # See if this is the first user added and make it active in session
        users_exist = len(list(mongo.db.users.find(
            {"user_type": "user", "account_name": account_name})))

        # Check if account/user already exists
        existing_user = mongo.db.users.find_one(
            {"user_name": request.form.get("user_name").lower(),
             "account_name": account_name,
             "user_type": "user"})

        if existing_user:
            flash("User name already exists.  Please try a new one")
            return redirect(url_for("get_users"))

        # If this is the **first** user added after account creation,
        # make this user an admin
        # Note: "on" or "off" are only used for the switch
        user_admin = False

        if users_exist == 0:
            user_admin = True
            session["ACTIVE_ADMIN"] = True

        # See if this is an admin requesting to anoint another one
        elif session.get("ACTIVE_ADMIN") is not None:
            user_admin = False
            if request.form.get("user_admin") == "on":
                user_admin = True

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

        # if the initial user count was 0, this user can be
        # set as the active user in session

        if users_exist == 0:
            session["ACTIVE_USER"] = request.form.get("user_name").lower()

        return redirect(url_for("get_users"))

    return render_template("user_add.html")

"""
    Select the correct environment
"""
if environment == "flask":
    if __name__ == "__main__":
        app.run(use_debugger=False, use_reloader=False,
                passthrough_errors=True)

elif environment == "vscode":
    if __name__ == "__main__":
        app.run(use_debugger=True, use_reloader=False,
                passthrough_errors=True)


elif environment == "heroku":
    if __name__ == "__main__":
        app.run(host=os.environ.get("IP", "0.0.0.0"),
                port=int(os.environ.get("PORT", "5000")),
                debug=False)
