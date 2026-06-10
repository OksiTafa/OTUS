from src.phonebook import PhoneBook


def main():
    phonebook = PhoneBook()

    while True:
        print('''Список команд:
                1 - Добавить новый контакт
                2 - Найти контакт
                3 - Изменить контакт
                4 - Удалить контакт
                5 - Посмотреть все контакты 
                6 - Выход 
              ''')

        user_cmd = input('Введите команду 1-6: ').strip()
        if user_cmd == '1':
            # Добавление контакта
            name = input("Введите имя: ").strip().title()
            while not name:
                name = input("Поле обязательно для заполнения. Введите имя: ").strip().title()

            phone = input("Введите номер телефона: ")
            while not phone:
                phone = input("Поле обязательно для заполнения. Введите номер телефона: ").strip()

            note = input("Введите заметку: ")

            try:
                phonebook.add_contact(name, phone, note)
                print(f"Контакт {name} добавлен")
            except ValueError as e:
                print(f"Ошибка: {e}")

        elif user_cmd == '2':
            # Поиск контакта по имени или номеру телефона
            query = input("Введите данные для поиска: ").strip().lower()
            res_list = phonebook.search_contact(query)

            for i in res_list:
                print(f'{i["name"]} ({i["note"]}): {i["phone"]}')

        elif user_cmd == '3':
            # Редактирование контакта
            query = input("Какой контакт хотите изменить? ").strip().lower()
            if phonebook.edit_contact(query):
                print("Контакт обновлён")
            else:
                print("Контакт не найден")

        elif user_cmd == '4':
            # Удаление контакта
            query = input("Какой контакт хотите удалить? ").strip().lower()
            if phonebook.delete_contact(query):
                print("Контакт удалён")
            else:
                print("Контакт не найден")

        elif user_cmd == '5':
            # Показать все контакты
            phonebook.show_all_contacts()

        elif user_cmd == '6':
            break
        else:
            print('Неизвестная команда! Введите число от 1 до 6')


main()