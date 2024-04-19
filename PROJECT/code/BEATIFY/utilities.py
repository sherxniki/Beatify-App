from flask_login import current_user
from flask import current_app, abort
import os
from .models import *
import matplotlib.pyplot as plt
import secrets
from PIL import Image
from collections import Counter
from functools import wraps

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
    image=Image.open(form_picture)
    image.thumbnail((500,500))
    random=secrets.token_hex(8)
    _,ext=os.path.splitext(form_picture.filename)
    f_name=random+ext 
    picture_path=os.path.join(current_app.root_path,'static/images',f_name)
    image.save(picture_path)
    return f_name

def save_track(audio_url):
    random=secrets.token_hex(8)
    _,ext=os.path.splitext(audio_url.filename)
    f_name=random+ext
    file_path=os.path.join(current_app.root_path,'static/music',f_name)
    audio_url.save(file_path)
    return f_name

def avg_creator_rating(song_ids):
    try:
        ratings =  Rating.query.filter(Rating.song_id.in_(song_ids)).all()
        return sum([rating.rating for rating in ratings])/len(ratings)
    except: 
        return 0
    
def avg_rating_for_song(Rating,song_id):
    try:
        ratings = Rating.query.filter_by(song_id=song_id).all()
        return sum([rating.rating for rating in ratings])/len(ratings)
    except:
        return 0

from flask import current_app
import os
import matplotlib.pyplot as plt

def show_stats(songs, ratings):
    plt.switch_backend('agg')
    plt.bar([song.title for song in songs],ratings)
    plt.xlabel('Songs')
    plt.ylabel('Average Rating')
    plt.savefig(os.path.join(current_app.root_path,'static/stats','songs_statistics.png'))
    plt.close()

    plt.switch_backend('agg')
    song_genre = dict(Counter(song.genre for song in songs))
    plt.pie(song_genre.values(), labels=song_genre.keys(), autopct='%1.1f%%', startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.
    plt.savefig(os.path.join(current_app.root_path,'static/stats','genre_statistics.png'))
    plt.close()