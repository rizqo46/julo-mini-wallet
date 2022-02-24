from re import M
from flask import Flask

app = Flask("mini-wallet")


# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

from model import db 
db.init_app(app)