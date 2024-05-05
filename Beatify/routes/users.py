from flask import Blueprint, jsonify
from Beatify import db, cache
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, url_for, render_template, redirect, flash
from flask_login import login_user, current_user, logout_user, login_required
from ..models import LoginActivity, User, Role, Song, Rating, Playlist, Album, PlaylistSong, UserActivity
from ..utilities import role_needed, avg_rating_for_song, creatorreport
from ..tasks import userreminders, sendreports
from ..forms import LoginForm, RegistrationForm, CreatePlaylistForm, EditPlaylistForm
from sqlalchemy import func
from datetime import datetime

users = Blueprint('users', __name__)


@users.route('/search', methods=["POST", "GET"])
@login_required
@role_needed(roles=['user'])
def search():
    search_query = request.args.get('search_query')
    songs = Song.query.filter(
        or_(
            Song.lyrics.ilike(f"%{search_query}%"),
            Song.title.ilike(f"%{search_query}%"),
            Song.genre.ilike(f"%{search_query}%"),
            Song.album.has(Album.title.ilike(f"%{search_query}%")),
            Song.artist.has(User.name.ilike(f"%{search_query}%"))
        )
    ).all()
    albums = Album.query.filter(
        or_(
            Album.title.ilike(f"%{search_query}%"),
            Album.artist.has(User.name.ilike(f"%{search_query}%"))
        )
    ).all()
    return render_template('search.html', search_query=search_query, songs=songs, albums=albums, title='Search')


@users.route('/home')
@login_required
@role_needed(roles=['user'])
@cache.cached(timeout=60, key_prefix='home_songs')
def home_page():
    songs = Song.query.all()
    albums = Album.query.all()
    genres = [song.genre for song in songs]
    current_date = datetime.now().date()
    quer = LoginActivity.query.filter(
        and_(
            func.date(LoginActivity.datetime) == current_date,
            LoginActivity.user == current_user.id
        )
    ).all()
    if len(quer) == 0:
        lgact = LoginActivity(user=current_user.id)
        db.session.add(lgact)
        db.session.commit()
    return render_template('home.html', songs=songs, title='Home', albums=albums, genres=genres)


@users.route('/sign_up', methods=["POST", "GET"])
def sign_up():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_role = Role.query.filter_by(name='user').first()
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pw, email=form.email.data)
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! Please login.', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', form=form, title='Sign Up')


@users.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            current_date = datetime.now().date()
            quer = LoginActivity.query.filter(
                and_(
                    func.date(LoginActivity.datetime) == current_date,
                    LoginActivity.user == current_user.id
                )
            ).all()
            if len(quer) == 0:
                lgact = LoginActivity(user=current_user.id)
                db.session.add(lgact)
                db.session.commit()
            return redirect(url_for('users.home_page'))
        else:
            flash('Invalid username and/or password. Please try again.', category='danger')
    return render_template('login.html', form=form, title='Login', heading='Login')


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.welcome'))


@users.route('/account')
@login_required
@role_needed(roles=['user'])
def account():
    return render_template('account.html', title='Account')


@users.route('/song/<int:song_id>')
@login_required
@role_needed(roles=['user'])
def song(song_id):
    song = Song.query.get(song_id)
    avg_rating = round(avg_rating_for_song(Rating, song_id), 2)
    num = len(Rating.query.filter_by(song_id=song_id).all())
    db.session.commit()
    return render_template('song.html', song=song, title=song.title, num=num, avg_rating=avg_rating)


@users.route('/rating/<int:song_id>/<int:value>')
@login_required
@role_needed(roles=['user'])
def rate(song_id, value):
    rating = Rating.query.filter_by(user_id=current_user.id, song_id=song_id).first()
    if rating is None:
        db.session.add(Rating(user_id=current_user.id, song_id=song_id, rating=value))
        db.session.commit()
    else:
        rating.rating = value
        db.session.commit()
    return redirect(url_for('users.song', song_id=song_id))


@users.route('/album/<int:album_id>')
@login_required
@role_needed(roles=['user'])
def album(album_id):
    album = Album.query.get(album_id)
    return render_template('album.html', album=album, title=album.title)


@users.route('/playlists')
@login_required
@role_needed(roles=['user'])
def playlists():
    playlists = current_user.playlists
    return render_template('playlists.html', title='Playlists', playlists=playlists)


@users.route('/playlist/<int:playlist_id>', methods=["POST", "GET"])
@login_required
@role_needed(roles=['user'])
def playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    return render_template('playlist.html', title='Playlist', playlist=playlist)


@users.route('/create_playlists', methods=["POST", "GET"])
@login_required
@role_needed(roles=['user'])
def create_playlists():
    form = CreatePlaylistForm()
    form.songs.query = [song for song in Song.query.all()]
    if form.validate_on_submit():
        selected_songs = form.songs.data
        playlist = Playlist(name=form.title.data, user_id=current_user.id)
        for song in selected_songs:
            playlist.songs.append(song)
        db.session.add(playlist)
        db.session.commit()
        return redirect(url_for('users.playlists'))
    return render_template('create_playlist.html', title='Create', form=form, Song=Song)


@users.route('/delete_playlist/<int:playlist_id>')
@login_required
@role_needed(roles=['user'])
def remove_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if current_user.id != playlist.user_id:
        return redirect(url_for('users.playlists'))
    PlaylistSong.query.filter_by(playlist_id=playlist_id).delete()
    Playlist.query.filter_by(id=playlist_id).delete()
    db.session.commit()
    return redirect(url_for('users.playlists'))


@users.route('/edit_playlist/<int:playlist_id>', methods=["POST", "GET"])
@login_required
@role_needed(roles=['user'])
def edit_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if current_user.id != playlist.user_id:
        return redirect('users.playlists')
    form = EditPlaylistForm()
    form.songs.query = [song for song in Song.query.all()]
    # initial values
    if request.method == 'GET':
        form.title.data = playlist.name
    if form.validate_on_submit():
        # values after editing
        playlist.title = form.title.data
        selected_songs = form.songs.data
        if selected_songs:
            playlist.songs = []
            for song in selected_songs:
                playlist.songs.append(song)
        db.session.commit()
        return redirect(url_for('users.playlists'))
    return render_template('edit_playlist.html', form=form, title="Edit Playlist")


@users.route('/song_played', methods=['POST'])
@login_required
@role_needed(roles=['user'])
def song_played():
    data = request.get_json()
    song_id = data.get('song_id')

    if song_id is not None:
        activity = UserActivity(user=current_user.id, activity='SongPlay', song=song_id)
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': 'Activity recorded'}), 200
    else:
        return jsonify({'message': 'Invalid request'}), 400