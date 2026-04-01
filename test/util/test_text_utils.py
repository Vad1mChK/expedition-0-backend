import pytest
from time import perf_counter as timer

from app.util.text_utils import clear_text


@pytest.mark.parametrize("text, to_lowercase, expected_result", [
    ("Жил-был на свете  Антон Городецкий", True, "жил-был на свете антон городецкий"),
    ("Lorem ipsum,  dolor sit amet...",False, "Lorem ipsum dolor sit amet"),
    (" Песчаный карьер, два человека!..", True, "песчаный карьер два человека"),
    ("Сестра. Включи телевизор погромче.", True, "сестра включи телевизор погромче")
])
def test_text_utils(text: str, to_lowercase: bool, expected_result: str):
    t0 = timer()
    actual_result = clear_text(text, to_lowercase=to_lowercase)
    print(f"Execution time: {timer() - t0:.6f} seconds")
    assert actual_result == expected_result
