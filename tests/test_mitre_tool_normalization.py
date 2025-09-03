import pytest
from unittest.mock import patch
from src.tools.mitre_tool import _mitre_attack_query_tool

@pytest.mark.parametrize("input_query,expected_substr", [
    ("Credential Stuffing", "Credential Stuffing"),
    ({"description": "lateral movement"}, "lateral movement"),
    ({"description": {"description": "nested string"}}, "nested string"),
    ({"description": None}, ""),
    (123, "123"),
    ({"description": 456}, "456"),
    ({"description": {"description": {}}}, ""),
])
def test_mitre_attack_query_tool_normalizes_query(input_query, expected_substr):
    class DummyAttack:
        def get_techniques_by_content(self, kw):
            # Devuelve resultados solo si hay texto
            if kw:
                return [{"id": "T0000", "name": kw, "description": f"Desc {kw}"}]
            return []
    with patch("src.tools.mitre_tool.get_attack_client", return_value=DummyAttack()):
        result = _mitre_attack_query_tool(input_query)
        assert expected_substr in result or expected_substr in str(result)
