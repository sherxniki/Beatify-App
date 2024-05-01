from flask import Blueprint, render_template, request, redirect, url_for, make_response
from flask_login import current_user, login_required
from Beatify import db
from Beatify.models import Role, Song, Album, Rating, User
from ..forms import RegisterAsCreator, PublishSongForm, PublishAlbumForm, EditSongForm, EditAlbumForm, SearchForm
from ..utilities import role_needed, save_picture, save_track, avg_creator_rating

creators = Blueprint('creators', __name__)


@creators.context_processor
def base():
    form = SearchForm()
    return dict(search_form=form)


@creators.route('/register_as_creator', methods=["POST", "GET"])
@login_required
@role_needed(roles=['user'])
def upgarde_to_creator():
    if 'creator' in [role.name for role in current_user.roles]:
        return redirect(url_for('creators.profile'))

    form = RegisterAsCreator()
    if form.validate_on_submit():
        file = form.profile_picture.data
        if file:
            image = file.read()
            current_user.profile = image
        current_user.name = form.name.data
        current_user.description = form.description.data
        role = Role.query.filter_by(name="creator").first()
        current_user.roles.append(role)
        db.session.commit()
        return redirect(url_for('creators.create_songs'))
    return render_template('upgrade_to_creator.html', title='Upgrade to `Creator`', form=form)


@creators.route('/create_songs', methods=["POST", "GET"])
@login_required
@role_needed(roles=['creator'])
def create_songs():
    form = PublishSongForm()
    if form.validate_on_submit():
        song_file = form.song_file.data.read()
        song = Song(title=form.title.data, lyrics=form.lyrics.data, genre=form.genre.data, song_file=song_file)
        if form.picture_file.data:
            picture_file = form.picture_file.data.read()
            song.cover_file = picture_file
        db.session.add(song)
        current_user.songs.append(song)
        db.session.commit()
        return redirect(url_for('users.home_page'))
    return render_template('create_songs.html', title='Create', form=form)


@creators.route('/create_album', methods=["POST", "GET"])
@login_required
@role_needed(roles=['creator'])
def create_album():
    form = PublishAlbumForm()
    form.songs.query = [song for song in current_user.songs]
    if form.validate_on_submit():
        selected_songs = form.songs.data
        album = Album(title=form.title.data, artist_id=current_user.id)
        for song in selected_songs:
            album.songs.append(song)
        if form.picture_file.data:
            picture_file = form.picture_file.data.read()
            album.cover_file = picture_file
        db.session.add(album)
        db.session.commit()
        return redirect(url_for('creators.profile'))
    return render_template('create_album.html', title='Create', form=form, Song=Song)


@creators.route('/creator_profile', methods=["POST", "GET"])
@login_required
@role_needed(roles=['creator'])
def profile():
    song_ids = [song.id for song in current_user.songs]
    avg_rating = avg_creator_rating(song_ids)
    return render_template('creator_profile.html', title="Profile", avg=avg_rating
                           )


@creators.route('/del_song/<int:song_id>')
@login_required
@role_needed(roles=['creator'])
def delete_song(song_id):
    song = Song.query.get(song_id)
    if current_user.id != song.creator_id:
        return redirect(url_for('users.home_page'))
    Song.query.filter_by(id=song_id).delete()
    Rating.query.filter_by(song_id=song_id).delete()
    db.session.commit()
    return redirect(url_for('creators.profile'))


@creators.route('/edit_song/<int:song_id>', methods=["POST", "GET"])
@login_required
@role_needed(roles=['creator'])
def edit_song(song_id):
    song = Song.query.get(song_id)
    if current_user != song.artist:
        return redirect('creators.profile')
    form = EditSongForm()
    # initial values
    if request.method == 'GET':
        form.title.data = song.title
        form.genre.data = song.genre
        form.lyrics.data = song.lyrics
    if form.validate_on_submit():
        # values after editing
        song.title = form.title.data
        song.lyrics = form.lyrics.data
        song.genre = form.genre.data

        if form.picture_file.data:
            picture_file = form.picture_file.data.read()
            song.cover_file = picture_file
        db.session.commit()
        return redirect(url_for('creators.profile'))
    return render_template('edit_song.html', form=form, title="Edit Song")


@creators.route('/edit_album/<int:album_id>', methods=["POST", "GET"])
@login_required
@role_needed(roles=['creator'])
def edit_album(album_id):
    album = Album.query.get(album_id)
    if current_user != album.artist:
        return redirect('creators.profile')
    form = EditAlbumForm()
    form.songs.query = [song for song in current_user.songs]

    if request.method == 'GET':
        form.title.data = album.title
    if form.validate_on_submit():
        # values after editing
        album.title = form.title.data
        selected_songs = form.songs.data
        if form.picture_file.data:
            picture_file = form.picture_file.data.read()
            album.cover_file = picture_file

        if selected_songs:
            album.songs = []
            for song in selected_songs:
                album.songs.append(song)
        db.session.commit()
        return redirect(url_for('creators.profile'))
    return render_template('edit_album.html', form=form, title="Edit Album")


@creators.route('/delete_album/<int:album_id>')
@login_required
@role_needed(roles=['creator'])
def delete_album(album_id):
    album = Album.query.filter_by(id=album_id).first()
    if current_user.id != album.artist_id:
        return redirect(url_for('users.home_page'))
    Album.query.filter_by(id=album_id).delete()
    db.session.commit()
    return redirect(url_for('creators.profile'))

