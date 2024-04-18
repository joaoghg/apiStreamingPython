from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from firebase_admin import auth, credentials
from dotenv import load_dotenv
import firebase_admin
import json
import requests
import os

cred_path = os.path.join(os.path.dirname(__file__), 'auth-firebase.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
load_dotenv()


class Catalogo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    sinopse = db.Column(db.Text, nullable=False)
    elenco = db.Column(db.Text, nullable=False)
    diretor = db.Column(db.String(50), nullable=False)
    lancamento = db.Column(db.Integer, nullable=False)
    genero = db.Column(db.String(50), nullable=False)
    nota = db.Column(db.Float)


class HistoricoVisualizacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    catalogo_id = db.Column(db.Integer, db.ForeignKey('catalogo.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)


class ListaReproducao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(100), nullable=False)


class ListaConteudo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    catalogo_id = db.Column(db.Integer, db.ForeignKey('catalogo.id'), nullable=False)
    lista_id = db.Column(db.Integer, db.ForeignKey('lista_reproducao.id'), nullable=False)


def verify_token():
    id_token = request.headers.get('Authorization')
    if not id_token:
        return jsonify({'msg': 'Token não fornecido'}), 401

    try:
        decoded_token = auth.verify_id_token(id_token)
        request.uid = decoded_token['uid']
    except auth.InvalidIdTokenError:
        return jsonify({'msg': 'Token inválido'}), 401
    except auth.ExpiredIdTokenError:
        return jsonify({'msg': 'Token expirado'}), 401


def is_catalogo_vazio():
    return db.session.query(db.exists().where(Catalogo.id != None)).scalar()


def insert_catalogo_padrao():
    initial_content = [
        {
            'titulo': 'Filme 1',
            'sinopse': 'Sinopse do Filme 1',
            'elenco': 'Elenco do Filme 1',
            'diretor': 'Diretor 1',
            'lancamento': 2020,
            'genero': 'Ação',
            'nota': 7.5
        },
        {
            'titulo': 'Filme 2',
            'sinopse': 'Sinopse do Filme 2',
            'elenco': 'Elenco do Filme 2',
            'diretor': 'Diretor 2',
            'lancamento': 2019,
            'genero': 'Comédia',
            'nota': 8.0
        }
    ]

    for content in initial_content:
        new_content = Catalogo(**content)
        db.session.add(new_content)

    db.session.commit()


@app.before_request
def before_request_func():
    if request.endpoint not in ['login', 'sign_up']:
        return verify_token()


@app.route('/api/signup', methods=['POST'])
def sign_up():
    dados = request.json

    if 'email' not in dados or 'password' not in dados:
        return jsonify({'msg': 'Campos "email" e "password" são obrigatórios.'}), 400

    email = dados['email']
    password = dados['password']

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        return jsonify({'msg': 'Usuário registrado!', 'id': user.uid})
    except Exception as e:
        return jsonify({'msg': str(e)}), 400


@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json

    if 'email' not in dados or 'password' not in dados:
        return jsonify({'msg': 'Campos "email" e "password" são obrigatórios.'}), 400

    email = dados['email']
    password = dados['password']

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={os.getenv('FIREBASE_API_KEY')}"

    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code != 200:
        return jsonify({'msg': 'Credenciais inválidas'}), 401
    json_response = json.loads(response.text)
    return jsonify({
        'msg': 'Login realizado com sucesso',
        'token': json_response['idToken'],
        'refreshToken': json_response['refreshToken']
    }), 200


@app.route('/api/catalog', methods=['GET'])
def catalog():
    content = Catalogo.query.all()
    catalog_data = [
        {'id': c.id, 'titulo': c.titulo, 'lancamento': c.lancamento, 'sinopse': c.sinopse, 'elenco': c.elenco,
         'diretor': c.diretor, 'genero': c.genero, 'nota': c.nota} for c in content]
    return jsonify(catalog_data), 200


@app.route('/api/catalog/<int:id>', methods=['GET'])
def content_detail(id):
    content = Catalogo.query.get(id)
    if not content:
        return jsonify({'msg': 'Conteúdo não encontrado!'}), 404

    content_data = {
        'id': content.id,
        'titulo': content.titulo,
        'lancamento': content.lancamento,
        'sinopse': content.sinopse,
        'elenco': content.elenco,
        'diretor': content.diretor,
        'genero': content.genero,
        'nota': content.nota
    }

    return jsonify(content_data), 200


@app.route('/api/play-video/<int:id>', methods=['GET'])
def play_video(id):
    video = Catalogo.query.get(id)
    if not video:
        return jsonify({'msg': 'Vídeo não encontrado!'}), 404
    
    uid = request.uid

    novo_historico = HistoricoVisualizacao(user_id=uid, catalogo_id=id)
    db.session.add(novo_historico)
    db.session.commit()

    return jsonify({'msg': f'Reproduzindo {video.titulo}'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not is_catalogo_vazio():
            insert_catalogo_padrao()

    app.run(debug=True)
