# ? Cross-origin Resource Sharing - here it allows the view and core applications deployed on different ports to communicate. No need to know anything about it since it's only used once
from flask_cors import CORS, cross_origin
# ? Python's built-in library for JSON operations. Here, is used to convert JSON strings into Python dictionaries and vice-versa
import json
# ? flask - library used to write REST API endpoints (functions in simple words) to communicate with the client (view) application's interactions
# ? request - is the default object used in the flask endpoints to get data from the requests
# ? Response - is the default HTTP Response object, defining the format of the returned data by this api
from flask import Flask, request, Response, jsonify, render_template, url_for, flash, redirect, session
# ? sqlalchemy is the main library we'll use here to interact with PostgresQL DBMS
import sqlalchemy
# ? Just a class to help while coding by suggesting methods etc. Can be totally removed if wanted, no change
import requests
from forms import RegistrationForm, LoginForm, ListingForm, ReviewForm, FilterForm, UpdateForm
from sql_functions import generate_create_table_statement, generate_delete_statement, generate_insert_table_statement, generate_select_from_table_query, generate_table_return_result, generate_update_table_statement, generate_distinct_values_from_column, generate_count_of_classes_from_column, generate_max_val_of_col, generate_total_count_from_column, generate_avg_val_of_col, generate_get_particular_value_from_table_query,update_val_of_col, generate_top_n_by_col, generate_total_of_type

# ? web-based applications written in flask are simply called apps are initialized in this format from the Flask base class. You may see the contents of `__name__` by hovering on it while debugging if you're curious
app = Flask(__name__,static_folder='static')
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
# ? Just enabling the flask app to be able to communicate with any request source
CORS(app)

# ? building our `engine` object from a custom configuration string
# ? for this project, we'll use the default postgres user, on a database called `postgres` deployed on the same machine
YOUR_POSTGRES_PASSWORD = "postgres"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@localhost/sharenstay"
engine = sqlalchemy.create_engine(
    "postgresql://postgres:postgres@localhost/sharenstay"
)

# ? `db` - the database (connection) object will be used for executing queries on the connected database named `postgres` in our deployed Postgres DBMS
db = engine.connect()

# MISCELLANEOUS FUNCTIONS
def distinct_value_from_column(col):
    statement = generate_distinct_values_from_column(["sharenstay",col])
    res = db.execute(statement)
    results = [r[0] for r in res.fetchall()]  # fetch all rows and convert to a list
    db.commit()
    return results

def get_listing_id(listing_id):
    statement = generate_select_from_table_query(["sharenstay", "id", listing_id])
    id = db.execute(statement).fetchone()
    db.commit()
    return id[3]

# ? @app.get is called a decorator, from the Flask class, converting a simple python function to a REST API endpoint (function)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # add user info to the user database
        username = form.username.data
        email = form.email.data
        password = form.password.data

        details = {"email": email,
                   "username": username,
                   "password": password,
                   "user_id": "DEFAULT"
                   }
        
        vtypes = {"email": "TEXT",
                  "username": "TEXT",
                  "password": "TEXT",
                  "user_id": "INT"
                 }

        try:
            insertion = {"name": "users",
                        "body": details,
                        "valueTypes": vtypes
                        }
            statement1_email = generate_select_from_table_query(['users','email',insertion["body"]['email']])
            tex1 = db.execute(statement1_email)
            db.commit()
            # Returns None if this is a new user
            if tex1.fetchone() == None:
                statement2_username = generate_select_from_table_query(['users','username',insertion["body"]['username']])
                tex2 = db.execute(statement2_username)
                db.commit()
                if tex2.fetchone() == None:
                    statement3 = generate_insert_table_statement(insertion)
                    db.execute(statement3)
                    db.commit()
                    flash("You have successfully registered!", 'success')
                    return redirect(url_for('login'))
                else: 
                    flash("Username is already taken! Try again.", 'danger')
                    return redirect(url_for('register'))
            else: 
                flash("Email is already taken! Try again.", 'danger')
                return redirect(url_for('register'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('register.html', title='Register', form=form)

@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        given_email = form.email.data
        given_password = form.password.data
        statement1_email = generate_select_from_table_query(['users','email',given_email])
        tex1 = db.execute(statement1_email)
        db.commit()
        user_deets = tex1.fetchone() # This will return None if no result and iterable iterm otherwise
        # user_deets is a tuple in the format(email, username, password, user_id)
        session['user_id'] = user_deets[1] #for now we will put username
        if user_deets != None: # email exists in database
            if user_deets[2] == given_password:
                if given_email == "admin@adminer.com":
                    flash('Welcome back admin!', 'success')
                    return redirect(url_for('admin_page'))
                else:
                    flash('You have been logged in!', 'success')
                    return redirect(url_for('home'))
            else:
              flash('Login Unsuccessful. Please check your password again', 'danger')
              return redirect(url_for('login'))  
        else:
            flash('Login Unsuccessful. Please check your email again', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', title='Login', form=form)

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user_name = session['user_id']
        # Return user name to be injected into template
        return {'user_name' : user_name}
    else:
        return {}

@app.route('/logout')
def logout():
    #Remove user ID from session
    session.pop('user_id',None)

    return redirect(url_for('login'))

@app.route("/listings")
def listings():
    # get filter and sort values from query parameters
    neighbourhood = request.args.get('neighbourhood', None)
    room_type = request.args.get('room_type', None)
    sort_by = request.args.get('sort_by', 'price')
    sort_order = request.args.get('sort_order', 'asc')
    sort_direction = "ASC" if sort_order == 'asc' else "DESC"

    # generate SQL statement with filters and sort
    filters = []
    if neighbourhood:
        filters.append(f"neighbourhood = '{neighbourhood}'")
    if room_type:
        filters.append(f"room_type = '{room_type}'")
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    sort_clause = f"ORDER BY {sort_by} {sort_direction}" if sort_by in ['number_of_reviews', 'minimum_nights', 'price'] else ""
    statement = sqlalchemy.text(f"SELECT * FROM sharenstay {where_clause} {sort_clause} LIMIT 50;")
    
    # execute SQL statement and generate data for template
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)

    # get unique values for each filter
    neighbourhoods = distinct_value_from_column('neighbourhood')
    room_types = distinct_value_from_column('room_type')

    return render_template('listings.html', data=data, 
        neighbourhoods=neighbourhoods, room_types=room_types, sort_by=sort_by, 
        neighbourhood=neighbourhood, room_type=room_type, sort_order=sort_order)

@app.route("/listings/<int:listing_id>", methods = ['GET'])
def get_listing(listing_id):
    statement = sqlalchemy.text(f"SELECT * FROM sharenstay WHERE id = {listing_id} LIMIT 50;")
    
    # execute SQL statement and generate data for template
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('single_listing.html', data=data)

@app.route("/listings/<int:listing_id>/reviews", methods = ['GET'])
def listing_review(listing_id):
    statement = sqlalchemy.text(f"SELECT * FROM reviews WHERE listing_id = {listing_id} LIMIT 50;")
    
    # execute SQL statement and generate data for template
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('reviews.html', data=data, listing_id = listing_id)

@app.route("/admin_page/listings/<int:listing_id>/reviews", methods = ['GET'])
def listing_review_admin(listing_id):
    statement = sqlalchemy.text(f"SELECT * FROM reviews WHERE listing_id = {listing_id} LIMIT 50;")
    
    # execute SQL statement and generate data for template
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('reviews_admin.html', data=data, listing_id = listing_id)

@app.route("/home")
def home():
    statement = sqlalchemy.text(f"SELECT * FROM sharenstay LIMIT 50;")
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('home.html', data=data)

@app.route("/admin_page/home")
def home_admin():
    statement = sqlalchemy.text(f"SELECT * FROM sharenstay LIMIT 50;")
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('home_admin.html', data=data)

@app.route("/users")
def users():
    statement = sqlalchemy.text(f"SELECT email, username FROM users;")
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('users.html', data=data)

@app.route("/admin_page/users")
def users_admin():
    statement = sqlalchemy.text(f"SELECT email, username FROM users;")
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('users_admin.html', data=data)


@app.get("/table")
def get_relation():
    # ? This method returns the contents of a table whose name (table-name) is given in the url `http://localhost:port/table?name=table-name`
    # ? Below is the default way of parsing the arguments from http url's using flask's request object
    relation_name = request.args.get('name', default="", type=str)
    # ? We use try-except statements for exception handling since any wrong query will crash the whole flow
    try:
        # ? Statements are built using f-strings - Python's formatted strings
        # ! Use cursors for better results
        statement = sqlalchemy.text(f"SELECT * FROM {relation_name};")
        # ? Results returned by the DBMS after execution are stored into res object defined in sqlalchemy (for reference)
        res = db.execute(statement)
        # ? committing the statement writes the db state to the disk; note that we use the concept of rollbacks for safe DB management
        db.commit()
        # ? Data is extracted from the res objects by the custom function for each query case
        # ! Note that you'll have to write custom handling methods for your custom queries
        data = generate_table_return_result(res)
        # ? Response object is instantiated with the formatted data and returned with the success code 200
        return Response(data, 200)
    except Exception as e:
        # ? We're rolling back at any case of failure
        db.rollback()
        # ? At any error case, the error is returned with the code 403, meaning invalid request
        # * You may customize it for different exception types, in case you may want
        return Response(str(e), 403)


# ? a flask decorator listening for POST requests at the url /table-create
@app.post("/table-create")
def create_table():
    # ? request.data returns the binary body of the POST request
    data = request.data.decode()
    try:
        # ? data is converted from stringified JSON to a Python dictionary
        table = json.loads(data)
        # ? data, or table, is an object containing keys to define column names and types of the table along with its name
        statement = generate_create_table_statement(table)
        # ? the remaining steps are the same
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-insert")
# ? a flask decorator listening for POST requests at the url /table-insert and handles the entry insertion into the given table/relation
# * You might wonder why PUT or a similar request header was not used here. Fundamentally, they act as POST. So the code was kept simple here
def insert_into_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        insertion = json.loads(data)
        statement = generate_insert_table_statement(insertion)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-update")
# ? a flask decorator listening for POST requests at the url /table-update and handles the entry updates in the given table/relation
def update_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        update = json.loads(data)
        statement = generate_update_table_statement(update)
        db.execute(statement)
        db.commit()
        return Response(statement.text, 200)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/entry-delete")
# ? a flask decorator listening for POST requests at the url /entry-delete and handles the entry deletion in the given table/relation
def delete_row():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        delete = json.loads(data)
        statement = generate_delete_statement(delete)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.route("/add_listing", methods=["GET", "POST"])
def add_listing():
    form = ListingForm()
    if form.validate_on_submit():
        name = form.name.data
        neighbourhood = form.neighbourhood.data
        room_type = form.room_type.data
        price = form.price.data
        min_nights = form.min_nights.data
        description = form.description.data
        username = session['user_id']

        # Retrieve user id from username
        userid_query = generate_get_particular_value_from_table_query(["users","user_id", "username", username])
        try:
            user_id = db.execute(userid_query).fetchone()[0]
            db.commit()
        except Exception as e:
            db.rollback()
            
        try:
            details = {"id": 'DEFAULT',
                       "name": description,
                       "host_name": name,
                       "host_id": user_id,
                       "neighbourhood_group": "NA",
                       "neighbourhood": neighbourhood,
                       "room_type": room_type,
                       "price": price,
                       "minimum_nights": min_nights,
                       "number_of_reviews": 0,
                       "license": "None",
                       "average_review": 0.00
                       }
            
            vtypes = {"id": "INT",
                       "name": "TEXT",
                       "host_name": "TEXT",
                       "host_id": "INT",
                       "neighbourhood_group": "TEXT",
                       "neighbourhood": "TEXT",
                       "room_type": "TEXT",
                       "price": "INT",
                       "minimum_nights": "INT",
                       "number_of_reviews": "INT",
                       "license": "TEXT",
                       "average_review": "INT"
                       }

            insertion = {"name": "sharenstay",
                         "body": details,
                         "valueTypes": vtypes}
            statement1 = generate_insert_table_statement(insertion)
            db.execute(statement1)
            db.commit()
            flash("Listing successfully added!", "success")
            return redirect(url_for('add_listing'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
            
    return render_template('add_listing.html', form=form)

@app.route("/admin_page/add_listing", methods=["GET", "POST"])
def add_listing_admin():
    form = ListingForm()
    if form.validate_on_submit():
        name = form.name.data
        neighbourhood = form.neighbourhood.data
        room_type = form.room_type.data
        price = form.price.data
        min_nights = form.min_nights.data
        description = form.description.data
        username = session['user_id']

        # Retrieve user id from username
        userid_query = generate_get_particular_value_from_table_query(["users","user_id", "username", username])
        try:
            user_id = db.execute(userid_query).fetchone()[0]
            db.commit()
        except Exception as e:
            db.rollback()
            
        try:
            details = {"id": 'DEFAULT',
                       "name": description,
                       "host_name": name,
                       "host_id": user_id,
                       "neighbourhood_group": "NA",
                       "neighbourhood": neighbourhood,
                       "room_type": room_type,
                       "price": price,
                       "minimum_nights": min_nights,
                       "number_of_reviews": 0,
                       "license": "None",
                       "average_review": 0.00
                       }
            
            vtypes = {"id": "INT",
                       "name": "TEXT",
                       "host_name": "TEXT",
                       "host_id": "INT",
                       "neighbourhood_group": "TEXT",
                       "neighbourhood": "TEXT",
                       "room_type": "TEXT",
                       "price": "INT",
                       "minimum_nights": "INT",
                       "number_of_reviews": "INT",
                       "license": "TEXT",
                       "average_review": "INT"
                       }

            insertion = {"name": "sharenstay",
                         "body": details,
                         "valueTypes": vtypes}
            statement1 = generate_insert_table_statement(insertion)
            db.execute(statement1)
            db.commit()
            flash("Listing successfully added!", "success")
            return redirect(url_for('add_listing_admin'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
            
    return render_template('add_listing_admin.html', form=form)

@app.route("/listings/<int:listing_id>/add_review", methods=["GET", "POST"])
def add_review(listing_id):
    form = ReviewForm()
    if form.validate_on_submit():
        reviewer = form.reviewer.data
        review = form.review.data
        rating = form.rating.data

        details = {"listing_id":listing_id,
                "reviewer": reviewer,
                "review": review,
                "rating": rating
                }
    
        vtypes = {"listing_id": "INT",
                "reviewer": "TEXT",
                "review": "TEXT",
                "rating": "INT"
                }

        try:
            insertion = {"name": "reviews",
                        "body": details,
                        "valueTypes": vtypes
                        }
            
            statement1 = generate_insert_table_statement(insertion)
            db.execute(statement1)
            db.commit()
            statement2 = generate_avg_val_of_col(["reviews","rating","listing_id",listing_id])
            avg_value_sql = db.execute(statement2)
            avg_value = avg_value_sql.fetchone()[0]
            db.commit()
            statement3 = update_val_of_col(["sharenstay","average_review", avg_value, "id", listing_id])
            db.execute(statement3)
            db.commit()

            statement4 = generate_total_of_type(["reviews","listing_id", listing_id])
            total_review_sql = db.execute(statement4)
            total_review = total_review_sql.fetchone()[0]
            db.commit()
            statement5 = update_val_of_col(["sharenstay","number_of_reviews", total_review, "id", listing_id])
            db.execute(statement5)
            db.commit()
            flash("Thank you for your review!", 'success')
            return redirect(url_for('listing_review', listing_id = listing_id))
        except Exception as e:
            db.rollback()
            flash("An error has occured")
            return Response(str(e), 403)
            
    return render_template('add_review.html', form=form)

@app.route("/admin_page/listings/<int:listing_id>/add_review", methods=["GET", "POST"])
def add_review_admin(listing_id):
    form = ReviewForm()
    if form.validate_on_submit():
        reviewer = form.reviewer.data
        review = form.review.data
        rating = form.rating.data

        details = {"listing_id":listing_id,
                "reviewer": reviewer,
                "review": review,
                "rating": rating
                }
    
        vtypes = {"listing_id": "INT",
                "reviewer": "TEXT",
                "review": "TEXT",
                "rating": "INT"
                }

        try:
            insertion = {"name": "reviews",
                        "body": details,
                        "valueTypes": vtypes
                        }
            
            statement1 = generate_insert_table_statement(insertion)
            db.execute(statement1)
            db.commit()
            statement2 = generate_avg_val_of_col(["reviews","rating","listing_id",listing_id])
            avg_value_sql = db.execute(statement2)
            avg_value = avg_value_sql.fetchone()[0]
            db.commit()
            statement3 = update_val_of_col(["sharenstay","average_review", avg_value, "id", listing_id])
            db.execute(statement3)
            db.commit()

            statement4 = generate_total_of_type(["reviews","listing_id", listing_id])
            total_review_sql = db.execute(statement4)
            total_review = total_review_sql.fetchone()[0]
            db.commit()
            statement5 = update_val_of_col(["sharenstay","number_of_reviews", total_review, "id", listing_id])
            db.execute(statement5)
            db.commit()
            flash("Thank you for your review!", 'success')
            return redirect(url_for('listing_review_admin', listing_id = listing_id))
        except Exception as e:
            db.rollback()
            flash("An error has occured")
            return Response(str(e), 403)
            
    return render_template('add_review_admin.html', form=form)

@app.route("/admin_page/listings")
def admin_page():
    statement = sqlalchemy.text(f"SELECT * FROM sharenstay LIMIT 50;")
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)

    count_statement = generate_total_count_from_column(['sharenstay', 'id'])
    count_res = db.execute(count_statement)
    db.commit()
    count_data = count_res.fetchone()[0]
    return render_template('admin_page.html', data=data, count = count_data)

@app.route("/admin_page/listings/<int:listing_id>", methods = ['GET'])
def admin_get_listing(listing_id):
    statement = sqlalchemy.text(f"SELECT * FROM sharenstay WHERE id = {listing_id} LIMIT 50;")
    
    # execute SQL statement and generate data for template
    res = db.execute(statement)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)
    return render_template('single_listing_admin.html', data=data, listing_id=listing_id)


@app.route("/admin_page/listing-statistics", methods = ["GET","POST"])
def listing_statistics():
    form = FilterForm()
    query = generate_top_n_by_col(['sharenstay',None,None])
    print(query.text)
    res = db.execute(query)
    db.commit()
    data = generate_table_return_result(res)
    data = json.loads(data)

    if form.validate_on_submit():
        n = form.top_n.data
        col = form.column.data
        query = generate_top_n_by_col(['sharenstay',col, n])
        print(query)
        res = db.execute(query)
        db.commit()
        data = generate_table_return_result(res)
        data = json.loads(data)
        return render_template('listing_statistics.html', form=form, data=data)
    return render_template('listing_statistics.html', form=form, data=data)


@app.route("/admin_page/listings/<int:listing_id>/delete_listing", methods = ['GET'])
def delete_listing(listing_id):
    statement = sqlalchemy.text(f"DELETE FROM sharenstay WHERE id = {listing_id};")
    
    # execute SQL statement and generate data for template
    db.execute(statement)
    db.commit()
    return render_template('delete_listing.html')


@app.route("/admin_page/listings/<int:listing_id>/update_listing", methods = ['GET','POST'])
def update_listing(listing_id):
    form = UpdateForm()
    if form.validate_on_submit():
        name = form.name.data
        neighbourhood = form.neighbourhood.data
        room_type = form.room_type.data
        price = form.price.data
        min_nights = form.min_nights.data
        description = form.description.data
        username = session['user_id']

        # Retrieve user id from username
        userid_query = generate_get_particular_value_from_table_query(["users","user_id", "username", username])
        try:
            user_id = db.execute(userid_query).fetchone()[0]
            db.commit()
        except Exception as e:
            db.rollback()
            
        try:
            details = {"name": description,
                       "host_name": name,
                       "host_id": user_id,
                       "neighbourhood": neighbourhood,
                       "room_type": room_type,
                       "price": price,
                       "minimum_nights": min_nights
                        }

            insertion = {"name": "sharenstay",
                         "body": details,
                         "id": listing_id
                        }
            statement1 = generate_update_table_statement(insertion)
            db.execute(statement1)
            db.commit()
            flash("Listing successfully updated!", "success")
            return redirect(url_for('update_listing',listing_id=listing_id))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
            
    return render_template('update_listing.html', form=form)


@app.route("/booked")
def booked():
    return render_template('booked.html')

# ? This method can be used by waitress-serve CLI 
def create_app():
   return app

# ? The port where the debuggable DB management API is served
PORT = 3000
# ? Running the flask app on the localhost/0.0.0.0, port 2222
# ? Note that you may change the port, then update it in the view application too to make it work (don't if you don't have another application occupying it)
if __name__ == "__main__":
    # app.run("0.0.0.0", PORT)
    # ? Uncomment the below lines and comment the above lines below `if __name__ == "__main__":` in order to run on the production server
    # ? Note that you may have to install waitress running `pip install waitress`
    # ? If you are willing to use waitress-serve command, please add `/home/sadm/.local/bin` to your ~/.bashrc
    from waitress import serve
    serve(app, host="0.0.0.0", port=2222)
