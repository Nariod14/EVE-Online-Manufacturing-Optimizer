# tests/test_routes.py
import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models import db, Blueprint, Material

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def client(app):
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()  # Ensure a clean slate before each test
            db.create_all()
            yield client
            db.session.remove()
@pytest.fixture
def sample_data(app):
    with app.app_context():
        blueprint1 = Blueprint(name="Item1", materials={"Category1": {"Material1": 2, "Material2": 1}}, sell_price=100, material_cost=50, max=5)
        blueprint2 = Blueprint(name="Item2", materials={"Category2": {"Material2": 3, "Material3": 2}}, sell_price=150, material_cost=70)
        
        material1 = Material(name="Material1", quantity=10)
        material2 = Material(name="Material2", quantity=15)
        material3 = Material(name="Material3", quantity=8)
        
        db.session.add_all([blueprint1, blueprint2, material1, material2, material3])
        db.session.commit()

def test_optimize_route_success(client, sample_data):
    response = client.get('/optimize')
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['status'] == 'Optimal'
    assert 'total_profit' in data
    assert 'what_to_produce' in data
    assert 'material_usage' in data
    assert 'true_profit' in data

def test_optimize_route_no_data(client):
    with client.application.app_context():
        response = client.get('/optimize')
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'No optimal solution found'
    pass

def test_optimize_route_unbounded(client, sample_data):
    with client.application.app_context():
        blueprint = Blueprint.query.filter_by(name="Item1").first()
        blueprint.sell_price = 1000000  # Unrealistically high sell price
        blueprint.material_cost = 0
        blueprint.max = None  # Remove max constraint
        db.session.commit()

    response = client.get('/optimize')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'unbounded' in data['error'].lower()

def test_optimize_route_exception(client, sample_data, monkeypatch):
    def mock_query_all(*args, **kwargs):
        raise Exception("Database error")

    monkeypatch.setattr(Blueprint.query, 'all', mock_query_all)

    response = client.get('/optimize')
    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'An error occurred during optimization'

def test_material_categories(client, sample_data):
    response = client.get('/optimize')
    assert response.status_code == 200
    data = response.get_json()
    
    material_usage = data['material_usage']
    assert material_usage['Material1']['category'] == 'Category1'
    assert material_usage['Material2']['category'] in ['Category1', 'Category2']
    assert material_usage['Material3']['category'] == 'Category2'

def test_max_constraint(client, sample_data):
    response = client.get('/optimize')
    assert response.status_code == 200
    data = response.get_json()
    
    what_to_produce = data['what_to_produce']
    assert what_to_produce['Item1'] <= 5

def test_material_usage(client, sample_data, app):
    response = client.get('/optimize')
    assert response.status_code == 200
    data = response.get_json()
    
    material_usage = data['material_usage']
    with app.app_context():
        for material, usage in material_usage.items():
            assert usage['used'] <= Material.query.filter_by(name=material).first().quantity

def test_profit_calculation(client, sample_data):
    response = client.get('/optimize')
    assert response.status_code == 200
    data = response.get_json()
    
    total_profit = data['total_profit']
    true_profit = data['true_profit']
    assert true_profit <= total_profit



if __name__ == '__main__':
    pytest.main([__file__])