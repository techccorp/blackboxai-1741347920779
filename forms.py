from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired, Length, EqualTo, URL, Optional, NumberRange, Email

# ------------------------------------------------------------
# Auth forms
# ------------------------------------------------------------
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3, max=15)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=15)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ChangeUsernameForm(FlaskForm):
    new_username = StringField('New Username', validators=[DataRequired(), Length(min=3, max=15)])
    submit = SubmitField('Change Username')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired(), Length(min=3, max=15)])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=3, max=15)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')
    
# ------------------------------------------------------------
# Recipe Forms
# ------------------------------------------------------------

class IngredientForm(FlaskForm):
    ingredient = StringField('Ingredient', validators=[DataRequired(), Length(min=1, max=100)])
    
class StepForm(FlaskForm):
    step = TextAreaField('Step', validators=[DataRequired(), Length(min=1, max=100)])

class DirectionForm(FlaskForm):
    direction = TextAreaField('Direction', validators=[DataRequired(), Length(min=1)])

class RecipeSubmissionForm(FlaskForm):
    title = StringField('Recipe Title', validators=[DataRequired()])
    description = TextAreaField('Recipe Description', validators=[DataRequired()])
    cuisine = StringField('Cuisine', validators=[DataRequired()])
    cookery_method = StringField('Cookery Method', validators=[DataRequired()])
    dietary_restrictions = StringField('Dietary Restrictions', validators=[DataRequired()])
    meal_type = StringField('Meal Type', validators=[DataRequired()])
    ingredients = FieldList(FormField(IngredientForm), min_entries=1, max_entries=50)
    steps = FieldList(FormField(StepForm), min_entries=1, max_entries=50)
    submit = SubmitField('Save Recipe')


class RecipeForm(FlaskForm):
    recipe_name = StringField('Recipe Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    cuisine_type = SelectField('Cuisine Type', choices=[('', 'Select Cuisine')] + [
        (cuisine, cuisine) for cuisine in [
            "Brazilian cuisine", "Cantonese cuisine", "Caribbean cuisine", "Chinese cuisine",
            "European cuisine", "French cuisine", "German cuisine", "Greek food",
            "Indian cuisine", "Indonesian cuisine", "Italian cuisine", "Japanese Cuisine",
            "Kashmiri cuisine", "Korean food", "Lebanese cuisine", "Mediterranean cuisine",
            "Mexican food", "Peruvian cuisine", "Polish cuisine", "Shandong cuisine",
            "Spanish Cuisine", "Thai cuisine", "Turkish cuisine", "Vietnamese cuisine",
            "American Cuisine", "British Cuisine", "Moroccan Cuisine", "Russian Cuisine",
            "Thai Cuisine", "Vietnamese Cuisine"
        ]
    ])
    meal_type = SelectField('Meal Type', choices=[('', 'Select Meal Type')] + [
        (meal, meal) for meal in [
            "Breakfast", "Lunch", "Dinner", "Snack", "Dessert"
        ]
    ])
    diet_type = SelectField('Diet Type', choices=[('', 'Select Diet Type')] + [
        (diet, diet) for diet in [
            "Dairy-Free", "Diabetic-Friendly", "Egg-Free", "FODMAP", "Gluten-Free",
            "Halal", "Keto", "Kosher", "Low-Carb", "Low-Fat", "Low-Sodium", "Low-Sugar",
            "Non-GMO", "Nut-Free", "Organic", "Paleo", "Pescatarian", "Soy-Free",
            "Vegan", "Vegetarian"
        ]
    ])
    cooking_method = SelectField('Cooking Method', choices=[('', 'Select Cooking Method')] + [
        (method, method) for method in [
            "barbeque", "braise", "confit", "deep fry", "grilling", "poaching",
            "roasting", "shallow fry", "sous vide", "cure", "smoked", "fermented", "cured"
        ]
    ])
    cooking_time = IntegerField('Cooking Time (minutes)', validators=[DataRequired(), NumberRange(min=1, max=1440)])
    servings = IntegerField('Servings', validators=[DataRequired(), NumberRange(min=1, max=100)])
    ingredients = FieldList(FormField(IngredientForm), min_entries=1, max_entries=20)
    directions = FieldList(FormField(DirectionForm), min_entries=1, max_entries=20)
    image_url = StringField('Image URL', validators=[Optional(), URL()])
    submit = SubmitField('Submit Recipe')
    
# ------------------------------------------------------------
# Business Onboarding Forms
# ------------------------------------------------------------

class BusinessSetupForm(FlaskForm):
    """Form for initial business setup"""
    business_name = StringField(
        'Business Name',
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )
    venue_type = SelectField(
        'Venue Type',
        choices=[
            ('single', 'Single Venue'),
            ('multiple', 'Multiple Venues')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Continue Setup')

class VenueForm(FlaskForm):
    """Form for venue configuration"""
    name = StringField(
        'Venue Name',
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )
    address = StringField(
        'Address',
        validators=[
            DataRequired(),
            Length(min=5, max=200)
        ]
    )
    contact = StringField(
        'Contact Number',
        validators=[
            DataRequired(),
            Length(min=5, max=20)
        ]
    )
    submit = SubmitField('Add Venue')

class WorkAreaForm(FlaskForm):
    """Form for work area configuration"""
    name = StringField(
        'Work Area Name',
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=500)
        ]
    )
    submit = SubmitField('Add Work Area')

class WorkAreaAssignmentForm(FlaskForm):
    """Form for assigning users to work areas"""
    user_id = StringField(
        'User ID',
        validators=[DataRequired()]
    )
    role = SelectField(
        'Role',
        choices=[
            ('manager', 'Manager'),
            ('staff', 'Staff'),
            ('employee', 'Employee')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Assign User')
