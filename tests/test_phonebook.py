import pytest
from unittest.mock import patch
from src.phonebook import PhoneBook

def test_add_contact():
    phonebook = PhoneBook()
    assert phonebook.add_contact("Оксана", "1234567890", "Друг детства") == True
    assert phonebook.add_contact("Алексей", "234567890", "") == True
    assert phonebook.add_contact("Анфиса Иванова", "34567890", "") == True

    with pytest.raises(ValueError, match="Имя не может быть пустым"):
        phonebook.add_contact("", "234567890", "номер")
    with pytest.raises(ValueError, match="Номер телефона не может быть пустым"):
        phonebook.add_contact("Оксана", "")
    with pytest.raises(ValueError, match="Контакт с таким номером телефона уже существует"):
        phonebook.add_contact("Юля", "+7 912 012 34 56")

def test_search_contact():
    phonebook = PhoneBook()
    result = phonebook.search_contact("Оксана")
    assert result[0]["name"] == "Оксана" and result[0]["phone"] == "1234567890" and result[0]["note"] == "Друг детства"

    result = phonebook.search_contact("+79123451234")
    assert result[0]["name"] == "Алексей Смирнов" and result[0]["phone"] == "+7 912 345 12 34" and result[0]["note"] == "Коллега по работе"

    result = phonebook.search_contact("+7 912 345 12 34")
    assert result[0]["name"] == "Алексей Смирнов" and result[0]["phone"] == "+7 912 345 12 34" and result[0]["note"] == "Коллега по работе"

    result = phonebook.search_contact("+7911")
    assert result == []

    result = phonebook.search_contact("John Doe")
    assert result == []

def test_delete_contact():
    phonebook = PhoneBook()
    assert phonebook.delete_contact("Оксана") == True
    assert phonebook.delete_contact("Анфиса Иванова") == True
    assert phonebook.delete_contact("234567890") == True
    assert phonebook.delete_contact("John Doe") == False
    assert phonebook.delete_contact("Александр") == False
    assert phonebook.delete_contact("") == False

def test_edit_contact():
    phonebook = PhoneBook()

    with patch('builtins.input', side_effect=["", "", "Старый деревенский друг"]):
        # Проверяем, что метод возвращает корректный результат
        result = phonebook.edit_contact("Александр Тихонов")
        assert result == (True, "Контакт успешно изменен")

    with patch('builtins.input', side_effect=["Екатерина Синицина", "+7 912 901 23 45", ""]):
        result = phonebook.edit_contact("Екатерина Соколова")
        assert result == (False, "Контакт с таким номером уже существует")

    with patch('builtins.input', side_effect=["Алексей Смирнов", "+7 920 123 44 69", "Клиент"]):
        result = phonebook.edit_contact("Алексей Смирнов")
        assert result == (False, "Не удалось установить точное соответствие. Проверьте введённые данные и попробуйте ещё раз.")