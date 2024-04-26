from . import db, login_manager
from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from datetime import datetime
from werkzeug.security import check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'))


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'Role({self.name})'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    roles = db.relationship('Role', secondary='user_role', backref='users')
    profile = db.Column(db.LargeBinary)
    description = db.Column(db.String(255))
    is_blacklisted = db.Column(db.Boolean, default=False)

    songs = db.relationship('Song', backref='artist')
    albums = db.relationship('Album', backref='artist')
    playlists = db.relationship('Playlist', backref='user')

    def check_password(self, attempted_password):
        return check_password_hash(self.password_hash, attempted_password)


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    lyrics = db.Column(db.Text)
    song_file = db.Column(db.LargeBinary, nullable=False)
    cover_file = db.Column(db.LargeBinary)
    date_uploaded = db.Column(db.Date, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    album_id = db.Column(db.Integer, db.ForeignKey('album.id', ondelete='CASCADE'))
    genre = db.Column(db.String, nullable=False)
    ratings = db.relationship('User', secondary='rating')

    def avg_rating(self):
        ratings = [rating.rating for rating in Rating.query.filter_by(song_id=self.id).all()]
        return round(sum(ratings) / len(ratings), 1) if ratings else 0.0

    __table_args__ = (
        CheckConstraint(
            genre.in_(['Rock', 'Pop', 'Hip-Hop', 'Electronic', 'RnB', 'Bollywood', 'Melancholy', 'Country']),
            name='check_valid_genre'
        ),
    )

    def __str__(self):
        return f'{self.title}'


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    rating = db.Column(db.Integer, nullable=False)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    songs = db.relationship('Song', secondary='playlist_song')


class PlaylistSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id', ondelete='CASCADE'))
    song_id = db.Column(db.Integer, db.ForeignKey('song.id', ondelete='CASCADE'))
    datetime = db.Column(db.DateTime, default=datetime.now)


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    cover_file = db.Column(db.LargeBinary)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)
    songs = db.relationship('Song', backref='album')


class UserActivity(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    datetime = db.Column(db.DateTime, default=datetime.now)
    activity = db.Column(db.String(100), nullable=False)
    song = db.Column(db.Integer, db.ForeignKey('song.id', ondelete='CASCADE'), nullable=True)

    __table_args__ = (
        CheckConstraint(
            activity.in_(['SongPlay']),
            name='check_valid_activity'
        ),
    )


class LoginActivity(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    datetime = db.Column(db.DateTime, default=datetime.now)
