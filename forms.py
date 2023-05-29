from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.fields import SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, AnyOf
import sqlalchemy
from sql_functions import generate_distinct_values_from_column

YOUR_POSTGRES_PASSWORD = "postgres"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@localhost/sharenstay"
engine = sqlalchemy.create_engine(
    "postgresql://postgres:postgres@localhost/sharenstay"
)

db = engine.connect()

# Return all the classes in a column available as a list from sharenstay table
def get_types(column):
    statement = generate_distinct_values_from_column(["sharenstay",column])
    table = db.execute(statement)
    db.commit()
    types = list(map(lambda x: x[0], table.fetchall()))
    types.sort()
    return types

NEIGHBOURHOODS = get_types("neighbourhood")
ROOM_TYPES = get_types("room_type")
RATINGS = [1,2,3,4,5]
COLUMNS = ["average_review"]

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ListingForm(FlaskForm):
    name = StringField("Name",
                       validators=[DataRequired()])
    neighbourhood = SelectField("Neighbourhood",
                                choices = NEIGHBOURHOODS)
    room_type = SelectField("Room type",
                            choices = ROOM_TYPES)
    price = StringField("Price",
                        validators = [DataRequired()])
    min_nights = StringField("Minimum nights to stay",
                             validators = [DataRequired()])
    description = StringField("Description",
                              validators=[DataRequired()])
    submit = SubmitField("Add your listing")
    
class ReviewForm(FlaskForm):
    reviewer = StringField("Reviewer",
                       validators=[DataRequired()])
    review = StringField("Review")
    rating = SelectField("Rating",
                            choices = RATINGS)
    submit = SubmitField("Add your review")

class FilterForm(FlaskForm):
    top_n= StringField("n", validators = [DataRequired()])
    column= SelectField("Column", choices = COLUMNS)
    submit = SubmitField("Submit")

class UpdateForm(FlaskForm):
    name = StringField("Name",
                       validators=[DataRequired()])
    neighbourhood = SelectField("Neighbourhood",
                                choices = NEIGHBOURHOODS)
    room_type = SelectField("Room type",
                            choices = ROOM_TYPES)
    price = StringField("Price",
                        validators = [DataRequired()])
    min_nights = StringField("Minimum nights to stay",
                             validators = [DataRequired()])
    description = StringField("Description",
                              validators=[DataRequired()])
    submit = SubmitField("Update this listing")