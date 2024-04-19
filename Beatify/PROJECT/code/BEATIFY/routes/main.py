from flask import Blueprint, render_template, make_response
from ..models import Song, User, Album


main=Blueprint('main',__name__)


@main.app_errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html", title='Page Not Found'), 404

@main.app_errorhandler(500)
def Internal_server_error(error):
    return render_template("errors/500.html", title='Internal Server Error'), 500

@main.app_errorhandler(403)
def unauthorized(error):
    return render_template("errors/403.html", title='Access Denied'), 403

@main.route('/')
def welcome():
    return render_template('welcome.html',title='Home')

@main.route('/display/user/<int:image_id>')
def load_user_image(image_id):
    user = User.query.get_or_404(image_id)
    response = make_response(user.profile)
    response.headers['Content-Type'] = 'image/jpeg' 
    return response

@main.route('/display/song/<int:song_id>')
def load_song(song_id):
    song = Song.query.get_or_404(song_id)
    response = make_response(song.song_file)
    response.headers['Content-Type'] = 'audio/mp3' 
    return response

@main.route('/display/song/image/<int:song_id>')
def load_song_image(song_id):
    song = Song.query.get_or_404(song_id)
    response = make_response(song.cover_file)
    response.headers['Content-Type'] = 'image/jpeg' 
    return response

@main.route('/display/album/image/<int:album_id>')
def load_album_image(album_id):
    album = Album.query.get_or_404(album_id)
    response = make_response(album.cover_file)
    response.headers['Content-Type'] = 'image/jpeg' 
    return response

