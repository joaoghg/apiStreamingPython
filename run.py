from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pyrebase

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

firebaseConfig = {
    "apiKey": "AIzaSyDf7-zZBPnYromKqga6tBZDVsLMwNCpaoY",
    "authDomain": "apistreamingpython.firebaseapp.com",
    "projectId": "apistreamingpython",
    "storageBucket": "apistreamingpython.appspot.com",
    "messagingSenderId": "583422505017",
    "databaseURL": "sqlite:///database.db",
    "appId": "1:583422505017:web:15a1abc590682ac3fddde8"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()


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


def getUser(token):
    if not token:
        return {'msg': 'Token inexistente!', 'erro': '1'}

    try:
        user = auth.get_account_info(token)
        uid = user['users'][0]['localId']
        return {'uid': uid, 'erro': '0'}
    except Exception as e:
        return {'msg': 'Token inválido ou expirado!', 'erro': '1'}
    

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


@app.route('/api/signUp', methods=['POST'])
def signUp():
    dados = request.json

    if 'email' not in dados or 'password' not in dados:
        return jsonify({'msg': 'Campos "email" e "password" são obrigatórios.'}), 400

    email = dados['email']
    password = dados['password']

    try:
        user = auth.create_user_with_email_and_password(email, password)
        return jsonify(user)
    except:
        return jsonify({'msg': 'Já existe um usuário com esse email!'}), 400


@app.route('/api/signIn', methods=['POST'])
def signIn():
    dados = request.json

    if 'email' not in dados or 'password' not in dados:
        return jsonify({'msg': 'Campos "email" e "password" são obrigatórios.'}), 400

    email = dados['email']
    password = dados['password']

    try:
        login = auth.sign_in_with_email_and_password(email, password)
        return jsonify(login)
    except:
        return jsonify({'msg': 'Email ou senha inválida!'}), 400
    

@app.route('/api/catalog', methods=['GET'])
def catalog():
    token = request.headers.get('Authorization')
    user = getUser(token)
    if user['erro'] == '1':
        return jsonify({'msg': user['msg']}), 401
    
    content = Catalogo.query.all()
    catalog_data = [{'id': c.id, 'titulo': c.titulo, 'lancamento': c.lancamento, 'sinopse': c.sinopse, 'elenco': c.elenco, 'diretor': c.diretor, 'genero': c.genero, 'nota': c.nota} for c in content]
    return jsonify(catalog_data), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not is_catalogo_vazio():
            insert_catalogo_padrao()

    app.run(debug=True)