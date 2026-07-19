import pytest
from jwrag.sanitizer import DataSanitizer

@pytest.fixture
def sanitizer() -> DataSanitizer:
    return DataSanitizer()

def test_anonymize_removes_pii(sanitizer: DataSanitizer) -> None:
    text = "My name is John Doe and my phone number is 555-010-9999. Email me at john.doe@example.com."
    anon_text, mapping = sanitizer.anonymize(text)
    
    # Assert PII is removed
    assert "John Doe" not in anon_text
    assert "555-010-9999" not in anon_text
    assert "john.doe@example.com" not in anon_text
    
    # Assert placeholders exist in the mapping
    original_values = list(mapping.values())
    assert "John Doe" in original_values
    assert "555-010-9999" in original_values
    assert "john.doe@example.com" in original_values

def test_deanonymize_restores_pii(sanitizer: DataSanitizer) -> None:
    text = "Contact <PERSON_1> at <EMAIL_ADDRESS_1>."
    mapping = {"<PERSON_1>": "Jane Doe", "<EMAIL_ADDRESS_1>": "jane@example.com"}
    
    restored = sanitizer.deanonymize(text, mapping)
    assert restored == "Contact Jane Doe at jane@example.com."

def test_anonymize_no_pii(sanitizer: DataSanitizer) -> None:
    text = "This is a generic sentence about software architecture."
    anon_text, mapping = sanitizer.anonymize(text)
    assert anon_text == text
    assert len(mapping) == 0
