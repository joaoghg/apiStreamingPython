import pytest
import requests
from run import app, db, Catalogo, HistoricoVisualizacao, ListaReproducao, ListaConteudo

@pytest.fixture
def base_url():
    return 'http://localhost:5000/api'

def test_sign_up(base_url):
    # Teste para o endpoint de cadastro de usuário
    response = requests.post(f'{base_url}/signup', json={'email': 'test@example.com', 'password': 'testpassword'})
    assert response.status_code == 200
    assert 'id' in response.json()
    return response.json()['id']

def test_login(base_url):
    # Teste para o endpoint de login
    response = requests.post(f'{base_url}/login', json={'email': 'test@example.com', 'password': 'testpassword'})
    assert response.status_code == 200
    assert 'token' in response.json()
    assert 'refreshToken' in response.json()

    # Teste para credenciais inválidas
    response = requests.post(f'{base_url}/login', json={'email': 'test@example.com', 'password': 'wrongpassword'})
    assert response.status_code == 401

def test_catalog(base_url):
    # Teste para o endpoint de listagem de catálogo
    response = requests.get(f'{base_url}/catalog')
    assert response.status_code == 200
    assert len(response.json()) == 2  # Supondo que existam dois itens no catálogo de exemplo

    # Teste para detalhes de conteúdo
    response = requests.get(f'{base_url}/catalog/1')
    assert response.status_code == 200
    assert 'titulo' in response.json()

    # Teste para conteúdo inexistente
    response = requests.get(f'{base_url}/catalog/1000')
    assert response.status_code == 404