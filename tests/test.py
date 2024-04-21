import pytest
from run import app, ListaReproducao, Catalogo, ListaConteudo

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_route(client):
    response = client.post('/api/login', json={'email': 'test@example.com', 'password': 'password'})
    assert response.status_code == 200

def test_catalog_route(client):
    response = client.get('/api/catalog')
    assert response.status_code == 200
    assert len(response.json) == 2  

def test_authentication(client):
    response = client.get('/api/lists')
    assert response.status_code == 401

    login_response = client.post('/api/login', json={'email': 'test@example.com', 'password': 'password'})
    token = login_response.json['token']

    response = client.get('/api/lists', headers={'Authorization': token})
    assert response.status_code == 200

def test_criar_lista_reproducao(client):
    response = client.post('/api/lists', json={'nome': 'Minha Lista'})
    assert response.status_code == 201

    lista = ListaReproducao.query.filter_by(nome='Minha Lista').first()
    assert lista is not None

def test_adicionar_conteudo_lista(client):
    client.post('/api/lists', json={'nome': 'Minha Lista'})

    primeiro_filme = Catalogo.query.first()
    filme_id = primeiro_filme.id

    response = client.post('/api/lists/1/add', json={'catalogo_id': filme_id})
    assert response.status_code == 201

    associacao = ListaConteudo.query.filter_by(lista_id=1, catalogo_id=filme_id).first()
    assert associacao is not None

def test_remover_conteudo_lista(client):
    client.post('/api/lists', json={'nome': 'Minha Lista'})
    primeiro_filme = Catalogo.query.first()
    filme_id = primeiro_filme.id
    client.post('/api/lists/1/add', json={'catalogo_id': filme_id})

    response = client.delete('/api/lists/1/remove/{}'.format(filme_id))
    assert response.status_code == 200

    associacao = ListaConteudo.query.filter_by(lista_id=1, catalogo_id=filme_id).first()
    assert associacao is None