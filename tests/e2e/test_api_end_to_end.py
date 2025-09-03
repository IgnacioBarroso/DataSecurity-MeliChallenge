import os
import pytest
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/api/analyze")
INPUTS_DIR = os.path.join(os.path.dirname(__file__), "../../data/custom_inputs")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "../../reports")

INPUT_FILES = [
    "input_example_1.txt",
    "input_example_2.txt",
    "input_example_3.txt",
    "input_example_4.txt",
    "input_example_5.txt",
]

def save_report(input_file, report_json):
    base = os.path.splitext(os.path.basename(input_file))[0]
    out_path = os.path.join(REPORTS_DIR, f"{base}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_json)

@pytest.mark.parametrize("input_file", INPUT_FILES)
def test_api_end_to_end(input_file):
    input_path = os.path.join(INPUTS_DIR, input_file)
    with open(input_path, "r", encoding="utf-8") as f:
        user_input = f.read()
    payload = {"user_input": user_input}
    response = requests.post(API_URL, json=payload, timeout=120)
    assert response.status_code == 200, f"Status: {response.status_code}, Body: {response.text}"
    data = response.json()
    assert "report_json" in data, f"No report_json in response: {data}"
    # Guardar output
    report_json = data.get("report_json") or "{}"
    save_report(input_file, report_json)
    # Validación mínima
    assert report_json.strip().startswith("{"), "El reporte JSON debe ser un objeto."
pytestmark = pytest.mark.skipif(os.getenv("RUN_E2E") != "1", reason="E2E disabled by default")
