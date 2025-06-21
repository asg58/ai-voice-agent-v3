import pytest

class MockDatabase:
    def query(self, input):
        if "' OR '1'='1" in input:
            return "error: potential SQL injection detected"
        return "query executed successfully"

database = MockDatabase()

@pytest.mark.security
def test_sql_injection():
    """
    Test SQL-injectie kwetsbaarheid.
    """
    malicious_input = "' OR '1'='1"
    response = database.query(malicious_input)
    assert "error" in response.lower()
