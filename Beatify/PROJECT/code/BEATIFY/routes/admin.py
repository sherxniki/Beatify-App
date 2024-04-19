from flask import Blueprint, current_app, url_for, redirect, flash, render_template
from flask_login import login_user, login_required
from ..forms import AdminLoginForm
from ..models import User, Song, Album, Rating
from BEATIFY import db
from ..utilities import role_needed, avg_rating_for_song, avg_creator_rating, show_stats

admin=Blueprint('admin',__name__)

@admin.route('/admin_login', methods=['POST', 'GET'])
def admin_login():
    form=AdminLoginForm()
    if form.validate_on_submit():
        if form.username.data==current_app.config['ADMIN_USERNAME'] and form.password.data==current_app.config['ADMIN_PASS']:
            admin=User.query.filter_by(username=form.username.data).first()
            login_user(admin)
            flash('Logged In as admin.', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Login Unsuccessful. Please check Username and/or password',category='danger')
    return render_template('login.html', form=form, title='Admin Login', heading='Admin Login')

@admin.route('/admin_dashboard')
@login_required
@role_needed(roles=['admin'])
def admin_dashboard():
    users = User.query.all()
    creators = User.query.filter(User.roles.any(name='creator')).all()
    songs = Song.query.all()
    ratings = [avg_rating_for_song(Rating, song.id) for song in songs]
    albums = Album.query.all()
    show_stats(songs,ratings)
    return render_template('admin_page.html', title='Admin Dashboard', users=users, creators=creators, songs=songs, albums=albums)

@admin.route('/manage_data')
@login_required
@role_needed(roles=['admin'])
def manage_songs_albums():
    songs = Song.query.all()
    albums = Album.query.all()
    ratings = [avg_rating_for_song(Rating, song.id) for song in songs]
    return render_template('admin_songs_albums.html', title='Song and Albums', songs = songs, ratings=ratings, albums=albums)

@admin.route('/del_song_admin/<int:song_id>')
@login_required
@role_needed(roles=['admin'])
def delete_song_admin(song_id):
    Song.query.filter_by(id=song_id).delete()
    Rating.query.filter_by(song_id=song_id).delete()
    db.session.commit()
    return redirect(url_for('admin.manage_songs_albums'))

@admin.route('/del_album_admin/<int:album_id>')
@login_required
@role_needed(roles=['admin'])
def delete_album_admin(album_id):
    Album.query.filter_by(id=album_id).delete()
    db.session.commit()
    return redirect(url_for('admin.manage_songs_albums'))


@admin.route('/manage_creators')
@login_required
@role_needed(roles=['admin'])
def manage_creators():
    creators = User.query.filter(User.roles.any(name='creator')).all()
    song_id_list = [[song.id for song in creator.songs] for creator in creators]
    ratings = [avg_creator_rating(song_ids) for song_ids in song_id_list]
    return render_template('manage_creators.html', title='Manage Creators', creators=creators, ratings=ratings)

@admin.route('/blacklist_whitelist/<int:creator_id>')
@login_required
@role_needed(roles=['admin'])
def black_whitelist(creator_id):
    creator= User.query.get(creator_id)
    creator.is_blacklisted = not creator.is_blacklisted
    db.session.commit()
    return redirect(url_for('admin.manage_creators'))