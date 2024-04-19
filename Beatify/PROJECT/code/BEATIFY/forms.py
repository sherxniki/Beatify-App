from flask_wtf import FlaskForm
from .models import User
from wtforms_alchemy import QuerySelectMultipleField
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField,SubmitField,BooleanField, PasswordField, IntegerField, PasswordField, EmailField, TextAreaField, SelectField
from .models import User
from wtforms.validators import DataRequired,EqualTo, Length, ValidationError, Email, NumberRange

genre_choices = [('Rock', 'Rock'), 
                 ('Pop', 'Pop'),
            ('Hip-Hop', 'Hip-Hop'),
            ('Electronic','Electronic'),
            ('RnB','RnB'),
            ( 'Bollywood','Bollywood'),
            ('Melancholy','Melancholy' ),
            ('Country', 'Country')]



class AdminLoginForm(FlaskForm):
    username=StringField('Enter your username:', validators=[DataRequired()])
    password=PasswordField('Enter your password:',validators=[DataRequired(),Length(8,25)])
    remember=BooleanField('Remember me')
    submit=SubmitField('Submit')

class RegisterAsCreator(FlaskForm):
    name=StringField('Your name:', validators=[DataRequired()])
    profile_picture = FileField(label='Add a profile picture:', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    description=TextAreaField('Add a description:',validators=[DataRequired(),Length(15,200)])
    submit=SubmitField('Get Started!')

class PublishSongForm(FlaskForm):
    title=StringField('Title:', validators=[DataRequired()])
    genre = SelectField('Genres', choices=genre_choices, validators=[DataRequired()])
    picture_file=FileField('Add a Banner:',validators=[FileAllowed(['jpg','png','jpeg'])])
    song_file=FileField('Upload Song:', validators=[FileAllowed(['mp3',"wav","ogg"]), DataRequired()])
    lyrics=TextAreaField('Add lyrics', validators=[DataRequired()])
    submit=SubmitField('Create')

class PublishAlbumForm(FlaskForm):
    title=StringField('Title:', validators=[DataRequired()])
    picture_file=FileField('Add a Banner:',validators=[FileAllowed(['jpg','png','jpeg'])])
    songs = QuerySelectMultipleField('Select Songs:',validators=[DataRequired()])
    submit=SubmitField('Create')

class EditSongForm(FlaskForm):
    title=StringField('Edit Title:', validators=[DataRequired()])
    genre = SelectField('Edit genre:', choices=genre_choices, validators=[DataRequired()])
    picture_file=FileField('Edit Banner:',validators=[FileAllowed(['jpg','png','jpeg'])])
    lyrics=TextAreaField('Edit lyrics', validators=[DataRequired()])
    submit=SubmitField('Save Changes')

class EditAlbumForm(FlaskForm):
    title=StringField('Edit Title:', validators=[DataRequired()])
    picture_file=FileField('Add a Banner:',validators=[FileAllowed(['jpg','png','jpeg'])])
    songs = QuerySelectMultipleField('Select Songs:',validators=[DataRequired()])
    submit=SubmitField('Save Changes')


class SearchForm(FlaskForm):
    searched=StringField('Search', validators=[DataRequired()])
    submit=SubmitField('Search')


class LoginForm(FlaskForm):
    username=StringField('Enter your username:', validators=[DataRequired()])
    password=PasswordField('Enter your password:',validators=[DataRequired(),Length(8,25)])
    remember=BooleanField('Remember me')
    submit=SubmitField('Submit')


class RegistrationForm(FlaskForm):
    username=StringField('Enter your username:', validators=[DataRequired()])
    email = EmailField('Enter your email:', validators=[DataRequired(), Email()])
    password=PasswordField('Enter your password:',validators=[DataRequired(),Length(min=8,max=25)])
    confirm_password=PasswordField('Confirm password:',validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('Submit')

    def validate_username(self,username):
        user=User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')
        
    def validate_email(self,email):
        user=User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already taken.')
        

class CreatePlaylistForm(FlaskForm):
    title=StringField('Title:', validators=[DataRequired()])
    songs = QuerySelectMultipleField('Select Songs:',validators=[DataRequired()])
    submit=SubmitField('Create')

class EditPlaylistForm(FlaskForm):
    title=StringField('Edit Title', validators=[DataRequired()])
    songs = QuerySelectMultipleField('Select Songs:',validators=[DataRequired()])
    submit=SubmitField('Save Changes')