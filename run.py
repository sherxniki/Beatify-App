from Beatify import application,db
from Beatify.models import *


app = application()
celery_app = app.extensions["celery"]
app.app_context().push()
@app.shell_context_processor
def make_shell_context():
 return dict(db=db, User=User, Song= Song, Album=Album)

def add_roles():
    roles =["user", "admin", "creator"]
    for r in roles:
        role = Role.query.filter_by(name=r).first()
        if role is None:
            role = Role(name=r)
            db.session.add(role)
            db.session.commit()

def add_admin():
    add_roles()
    if db.session.query(User).filter_by(username='admin').first() is None:
        admin_user = User(username=app.config['ADMIN_USERNAME'], name="Admin", email='admin007@gmail.com', password=app.config['ADMIN_PASS'], 
                           roles=[Role.query.filter_by(name='admin').first()])
        db.session.add(admin_user)
        db.session.commit()


if __name__=='__main__':
    with app.app_context():
        add_admin()
        add_roles()
    app.run(debug=True)