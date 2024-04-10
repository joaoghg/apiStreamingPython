from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(20), nullable=False)


class EnqueteOpcoes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opcao = db.Column(db.String(100), unique=True, nullable=False)
    enquete_id = db.Column(db.Integer, db.ForeignKey('enquete.id'), nullable=False)
    votos = db.relationship('Votos', backref='author', lazy=True, cascade='all,delete')


class Votos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, nullable=False, default=datetime.now)
    enquete_opcoes_id = db.Column(db.Integer, db.ForeignKey('enquete_opcoes.id'), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)