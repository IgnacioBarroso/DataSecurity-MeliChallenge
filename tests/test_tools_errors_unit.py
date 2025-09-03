from src.tools.mitre_tool import get_attack_client


def test_get_attack_client_singleton():
    import src.tools.mitre_tool as mitre_mod
    mitre_mod._attack = None
    class DummyAttack:
        pass
    mitre_mod.attack_client = lambda: DummyAttack()
    client1 = get_attack_client()
    client2 = get_attack_client()
    assert client1 is client2
