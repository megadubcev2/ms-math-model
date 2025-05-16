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

def test_move_left_magnetization(client):
    request_data, expected_response = get_test_data(
        'moveLeftMagnetizationRequest.json',
        'moveLeftMagnetizationResponse.json'
    )
    response = client.post('/find-first-for-moved-step', json=request_data)
    assert response.status_code == 200
    assert response.get_json() == expected_response

def test_move_single_step_between_steps(client):
    request_data, expected_response = get_test_data(
        'moveSingleStepBetweenStepsRequest.json',
        'moveSingleStepBetweenStepsResponse.json'
    )
    response = client.post('/find-first-for-moved-step', json=request_data)
    assert response.status_code == 200
    assert response.get_json() == expected_response

def test_move_single_step_without_overlapping(client):
    request_data, expected_response = get_test_data(
        'moveSingleStepWithoutOverlappingRequest.json',
        'moveSingleStepWithoutOverlappingResponse.json'
    )
    response = client.post('/find-first-for-moved-step', json=request_data)
    assert response.status_code == 200
    assert response.get_json() == expected_response

def test_move_step_with_step_order(client):
    request_data, expected_response = get_test_data(
        'moveStepWithStepOrderRequest.json',
        'moveStepWithStepOrderResponse.json'
    )
    response = client.post('/find-first-for-moved-step', json=request_data)
    assert response.status_code == 200
    assert response.get_json() == expected_response

def test_move_two_steps(client):
    request_data, expected_response = get_test_data(
        'moveTwoStepsRequest.json',
        'moveTwoStepsResponse.json'
    )
    response = client.post('/find-first-for-moved-step', json=request_data)
    assert response.status_code == 200
    assert response.get_json() == expected_response
