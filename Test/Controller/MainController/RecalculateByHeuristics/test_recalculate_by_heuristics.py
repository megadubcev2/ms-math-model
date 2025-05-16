import os
import json

import pytest
from Controller.MainController import app

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def get_test_data(request_filename, response_filename):
    base_dir = os.path.dirname(__file__)
    request_path = os.path.join(base_dir, 'Jsons', 'Requests', request_filename)
    response_path = os.path.join(base_dir, 'Jsons', 'Responses', response_filename)
    with open(request_path, encoding='utf-8') as f:
        request_data = json.load(f)
    with open(response_path, encoding='utf-8') as f:
        expected_response = json.load(f)
    return request_data, expected_response

def test_recalculate_impossible_deadline(client):
    request_data, expected_response = get_test_data(
        'recalculateImpossibleDeadlineRequest.json',
        'recalculateImpossibleDeadlineResponse.json'
    )
    response = client.post('/recalculate-by-heuristics', json=request_data)
    assert response.status_code == 200
    assert response.get_json() == expected_response



