from flask_login import current_user
from flask import abort
from .models import *
import secrets
from PIL import Image
from collections import Counter
from functools import wraps
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime, timedelta
from .models import Song, Album, UserActivity, User


def role_needed(roles):
    def helper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated:
                if set(roles).issubset({role.name for role in current_user.roles}):
                    return func(*args, **kwargs)
            return abort(403)

        return wrapper

    return helper


def save_picture(form_picture):
    image = Image.open(form_picture)
    image.thumbnail((500, 500))
    random = secrets.token_hex(8)
    _, ext = os.path.splitext(form_picture.filename)
    f_name = random + ext
    picture_path = os.path.join(current_app.root_path, 'static/images', f_name)
    image.save(picture_path)
    return f_name


def save_track(audio_url):
    random = secrets.token_hex(8)
    _, ext = os.path.splitext(audio_url.filename)
    f_name = random + ext
    file_path = os.path.join(current_app.root_path, 'static/music', f_name)
    audio_url.save(file_path)
    return f_name


def avg_creator_rating(song_ids):
    try:
        ratings = Rating.query.filter(Rating.song_id.in_(song_ids)).all()
        return sum([rating.rating for rating in ratings]) / len(ratings)
    except:
        return 0


def avg_rating_for_song(Rating, song_id):
    try:
        ratings = Rating.query.filter_by(song_id=song_id).all()
        return sum([rating.rating for rating in ratings]) / len(ratings)
    except:
        return 0


from flask import current_app
import os
import matplotlib.pyplot as plt


def show_stats(songs, ratings):
    plt.switch_backend('agg')
    plt.bar([song.title for song in songs], ratings)
    plt.xlabel('Songs')
    plt.ylabel('Average Rating')
    plt.savefig(os.path.join(current_app.root_path, 'static/stats', 'songs_statistics.png'))
    plt.close()

    plt.switch_backend('agg')
    song_genre = dict(Counter(song.genre for song in songs))
    plt.pie(song_genre.values(), labels=song_genre.keys(), autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.
    plt.savefig(os.path.join(current_app.root_path, 'static/stats', 'genre_statistics.png'))
    plt.close()


def creatorreport(user_id, report_file):
    user = User.query.get(user_id)

    # Check if the user has the 'creator' role
    if 'creator' not in [role.name for role in user.roles]:
        return

    # Get the current date and the date a month ago
    current_date = datetime.now()
    month_ago = current_date - timedelta(days=30)

    # Get the new songs added by the user in the last month
    new_songs = Song.query.filter(Song.creator_id == user_id, Song.date_uploaded >= month_ago).all()

    new_song = []
    for i in range(len(new_songs)):
        song = new_songs[i]
        new_song.append((i + 1, song.title))

    # Get the new albums created by the user in the last month
    new_albums = Album.query.filter(Album.artist_id == user_id, Album.date_uploaded >= month_ago).all()

    new_album = []
    for i in range(len(new_albums)):
        album = new_albums[i]
        new_album.append((i + 1, album.title))
    # Get all the songs uploaded by the user and the number of times each song was played in the last month
    all_songs = Song.query.filter(Song.creator_id == user_id).all()
    song_plays = []
    for i in range(len(all_songs)):
        song = all_songs[i]
        plays_last_month = UserActivity.query.filter(UserActivity.song == song.id, UserActivity.datetime >= month_ago,
                                                     UserActivity.activity == 'SongPlay').count()
        total_plays = UserActivity.query.filter(UserActivity.song == song.id,
                                                UserActivity.activity == 'SongPlay').count()
        avg_rating = song.avg_rating()
        song_plays.append((i + 1, song.title, plays_last_month, total_plays, avg_rating))

    # Create a new PDF with Reportlab
    doc = SimpleDocTemplate(report_file, pagesize=A4)

    # Create the table data
    new_songs_data = [["S. no.", "Title"]] + new_song if new_song else [["No new songs added in the last month"]]
    new_albums_data = [["S. no.", "Title"]] + new_album if new_album else [["No new albums created in the last month"]]
    song_plays_data = [["S. no.", "Title", "Plays Last Month", "Total Plays",
                        "Average Rating"]] + song_plays if song_plays else [["No songs uploaded "]]

    # Create the tables
    new_songs_table = Table(new_songs_data, hAlign='LEFT')
    new_albums_table = Table(new_albums_data, hAlign='LEFT')
    song_plays_table = Table(song_plays_data, hAlign='LEFT')

    # Add style to the tables
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),

        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    new_songs_table.setStyle(style)
    new_albums_table.setStyle(style)
    song_plays_table.setStyle(style)

    # Create the user details and timestamp
    styles = getSampleStyleSheet()
    user_details = Paragraph(
        f"User ID: {user.id}<br/>User Name: {user.name}<br/>User Email: {user.email}<br/>Report Duration: {month_ago.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}",
        styles['Normal'])

    # Build the PDF
    elements = [user_details, Spacer(1, 0.5 * inch), new_songs_table, Spacer(1, 0.5 * inch), new_albums_table,
                Spacer(1, 0.5 * inch),
                song_plays_table]
    doc.build(elements)
