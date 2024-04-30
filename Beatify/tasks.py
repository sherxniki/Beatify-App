import os
from . import db, mail
from .models import User, LoginActivity,Role
from flask_mail import Message
from sqlalchemy import func
from datetime import datetime
from .utilities import creatorreport
from celery import shared_task

@shared_task(bind=True ,name='tasks.userreminders')
def userreminders(self):
    # Get the current date
    current_date = datetime.now().date()

    # Get the list of users who have logged in today
    logged_in_users = db.session.query(LoginActivity.user).filter(func.date(LoginActivity.datetime) == current_date).all()
    logged_in_users = [user[0] for user in logged_in_users]  # Convert list of tuples to list

    # Get all users
    all_users = User.query.all()
    all_users_ids = [user.id for user in all_users]

    # Find users who have not logged in today
    not_logged_in_users = [user for user in all_users_ids if user not in logged_in_users]
    # Email each user who has not logged in today
    for user in not_logged_in_users:
        try:
            user = User.query.get(user)
            msg = Message('Reminder to log in', recipients=[user.email],sender="admin@beatify.com")
            msg.body = 'You have not logged in today. Please log in soon.'
            mail.send(msg)
        except:
            pass




@shared_task(bind=True ,name='tasks.sendreports')
def sendreports(self):
    creators = User.query.join(User.roles).filter(Role.name == 'creator').all()

    for creator in creators:
        try:

            # Generate the report for the creator
            report_file = f"report_{creator.id}.pdf"
            creatorreport(creator.id, report_file)

            # Send an email to the creator with the report attached
            msg = Message('Your Monthly Report', recipients=[creator.email], sender="admin@beatify.com")
            msg.body = 'Your monthly report is attached.'
            with open(os.path.join(os.getcwd(),report_file), 'rb') as fh:
                msg.attach(report_file, disposition="attachment",content_type="application/pdf",data=fh.read())
            mail.send(msg)

            # Delete the report file
            os.remove(report_file)
        except:
            pass