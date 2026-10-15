import pytest
from typing import Any
from dataclasses import dataclass

# The function to test
def _get_element(list_data: list, key: str, by: str = "id") -> Any:
    for el in list_data:
        if getattr(el, by) == key:
            return el
    raise ValueError(f'No element of {by} "{key}"!')

@dataclass
class MockElement:
    id: str
    name: str = ""
    category: str = ""

class TestGetElement:
    
    def test_get_by_default_id_success(self):
        """Should find an element by the default 'id' attribute."""
        el1 = MockElement(id="123", name="First")
        el2 = MockElement(id="456", name="Second")
        data = [el1, el2]
        
        result = _get_element(data, "456")
        assert result == el2
        assert result.name == "Second"

    def test_get_by_custom_attribute_success(self):
        """Should find an element using a specified attribute (e.g., 'name')."""
        el1 = MockElement(id="1", name="apple")
        el2 = MockElement(id="2", name="banana")
        data = [el1, el2]
        
        result = _get_element(data, "banana", by="name")
        assert result == el2
        assert result.id == "2"

    def test_raises_value_error_if_not_found(self):
        """Should raise ValueError with a specific message when key doesn't exist."""
        el1 = MockElement(id="1")
        data = [el1]
        
        with pytest.raises(ValueError, match='No element of id "missing"!'):
            _get_element(data, "missing")

    def test_raises_attribute_error_if_attr_missing(self):
        """Should raise AttributeError if the objects don't have the 'by' attribute."""
        el1 = MockElement(id="1")
        data = [el1]
        
        # 'color' attribute does not exist on MockElement
        with pytest.raises(AttributeError):
            _get_element(data, "red", by="color")

    def test_empty_list_raises_value_error(self):
        """Should raise ValueError immediately if the list is empty."""
        with pytest.raises(ValueError):
            _get_element([], "any_key")