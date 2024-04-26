import pytest
import json
from run import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def login(client):
    response = client.post('/api/login', json={'email': 'teste@exemplo.com', 'password': 'senha123'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'msg' in data
    assert 'token' in data
    return data['token']

def test_signup(client):
    response = client.post('/api/signup', json={'email': 'teste@exemplo.com', 'password': 'senha123'}) #Credenciais devem ser trocadas para cada teste
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'msg' in data
    assert 'id' in data

def test_login(client):
    login(client)

def test_catalog(client):
    token = login(client)
    response = client.get('/api/catalog', headers={'Authorization': token})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_content_detail(client):
    token = login(client)
    response = client.get('/api/catalog/9999', headers={'Authorization': token})
    assert response.status_code == 404 

def test_play_video(client):
    token = login(client)
    response = client.get('/api/play-video/9999', headers={'Authorization': token})
    assert response.status_code == 404

def test_historic(client):
    token = login(client)
    response = client.get('/api/historic', headers={'Authorization': token})
    assert response.status_code == 200

def test_buscar_catalogo(client):
    token = login(client)
    response = client.post('/api/catalog', json={}, headers={'Authorization': token})
    assert response.status_code == 200

def test_listar_listas(client):
    token = login(client)
    response = client.get('/api/lists', headers={'Authorization': token})
    assert response.status_code == 200

def test_listar_lista(client):
    token = login(client)
    response = client.get('/api/lists/9999', headers={'Authorization': token})
    assert response.status_code == 404

def test_criar_lista(client):
    token = login(client)
    response = client.post('/api/lists', json={'nome': 'Lista teste'}, headers={'Authorization': token})
    assert response.status_code == 201

def test_deletar_lista(client):
    token = login(client)
    response = client.delete('/api/lists/9999', headers={'Authorization': token})
    assert response.status_code == 404  

def test_adicionar_conteudo_lista(client):
    token = login(client)
    response = client.post('/api/lists/1/add', json={'catalogo_id': 9999}, headers={'Authorization': token})
    assert response.status_code == 404  

def test_remover_conteudo_lista(client):
    token = login(client)
    response = client.delete('/api/lists/1/remove/9999', headers={'Authorization': token})
    assert response.status_code == 404  
