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


@app.route('/api/historic', methods=['GET'])
def historic():
    uid = request.uid
    historico = HistoricoVisualizacao.query.filter_by(user_id=uid).all()
    if not historico:
        return jsonify({'msg': 'Usuário não reproduziu nenhum vídeo'}), 200

    historico_data = []
    for item in historico:
        catalogo_item = Catalogo.query.get(item.catalogo_id)
        historico_data.append({
            'titulo': catalogo_item.titulo,
            'data': item.timestamp
        })

    return jsonify(historico_data), 200


@app.route('/api/catalog', methods=['POST'])
def buscar_catalogo():
    dados = request.json
    query = Catalogo.query

    if 'titulo' in dados:
        query = query.filter(Catalogo.titulo.like('%{}%'.format(dados['titulo'])))

    if 'genero' in dados:
        query = query.filter_by(genero=dados['genero'])

    if 'lancamento' in dados:
        query = query.filter_by(lancamento=dados['lancamento'])

    if 'nota' in dados:
        query = query.filter_by(nota=dados['nota'])

    if 'elenco' in dados:
        query = query.filter(Catalogo.elenco.like('%{}%'.format(dados['elenco'])))

    if 'diretor' in dados:
        query = query.filter_by(diretor=dados['diretor'])

    catalogo = query.all()
    catalogo_data = [
        {'id': c.id, 'titulo': c.titulo, 'lancamento': c.lancamento, 'sinopse': c.sinopse, 'elenco': c.elenco, 'diretor': c.diretor, 'genero': c.genero, 'nota': c.nota} 
        for c in catalogo
    ]
    return jsonify(catalogo_data), 200


@app.route('/api/lists', methods=['GET'])
def listar_listas():
    uid = request.uid
    listas = ListaReproducao.query.filter_by(user_id=uid).all()
    listas_data = [{'id': l.id, 'nome': l.nome} for l in listas]
    return jsonify(listas_data), 200


@app.route('/api/lists/<int:lista_id>', methods=['GET'])
def listar_lista(lista_id):
    uid = request.uid
    lista = ListaReproducao.query.filter_by(user_id=uid, id=lista_id).first()
    if not lista:
        return jsonify({'msg': 'Lista não encontrada'}), 404

    conteudo = ListaConteudo.query.filter_by(lista_id=lista_id).all()
    if not conteudo:
        return jsonify({'msg' : f'A lista "{lista.nome}" está vazia'})

    conteudo_data = [{'id': c.id, 'titulo': Catalogo.query.get(c.catalogo_id).titulo} for c in conteudo]
    return jsonify({'id': lista.id, 'nome': lista.nome, 'conteudo': conteudo_data}), 200

@app.route('/api/lists', methods=['POST'])
def criar_lista():
    uid = request.uid
    dados = request.json

    if 'nome' not in dados:
        return jsonify({'msg' : 'O campo "nome" é obrigatório!'}), 400

    nome = dados['nome']

    nova_lista = ListaReproducao(nome=nome, user_id=uid)
    db.session.add(nova_lista)
    db.session.commit()

    return jsonify({'msg': 'Lista criada com sucesso'}), 201

@app.route('/api/lists/<int:lista_id>', methods=['DELETE'])
def deletar_lista(lista_id):
    uid = request.uid
    lista = ListaReproducao.query.filter_by(user_id=uid, id=lista_id).first()
    if not lista:
        return jsonify({'msg': 'Lista não encontrada!'}), 404

    db.session.delete(lista)
    db.session.commit()

    return jsonify({'msg': 'Lista deletada com sucesso'}), 200

@app.route('/api/lists/<int:lista_id>/add', methods=['POST'])
def adicionar_conteudo_lista(lista_id):
    dados = request.json
    if 'catalogo_id' not in dados:
        return jsonify(({'msg' : 'O campo "catalogo_id" é obrigatório!'})), 400

    catalogo_id = dados['catalogo_id']

    video = Catalogo.query.get(catalogo_id)
    if not video:
        return jsonify({'msg': 'Vídeo não encontrado!'}), 404

    nova_associacao = ListaConteudo(catalogo_id=catalogo_id, lista_id=lista_id)
    db.session.add(nova_associacao)
    db.session.commit()

    return jsonify({'msg': 'Conteúdo adicionado à lista com sucesso'}), 201

@app.route('/api/lists/<int:lista_id>/remove/<int:conteudo_id>', methods=['DELETE'])
def remover_conteudo_lista(lista_id, conteudo_id):
    associacao = ListaConteudo.query.filter_by(lista_id=lista_id, catalogo_id=conteudo_id).first()
    if not associacao:
        return jsonify({'msg': 'Vídeo não encontrado!'}), 404

    db.session.delete(associacao)
    db.session.commit()

    return jsonify({'msg': 'Vídeo removido da lista com sucesso'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not is_catalogo_vazio():
            insert_catalogo_padrao()

    app.run(debug=True)
