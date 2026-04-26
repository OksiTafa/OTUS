import json


def phone_book():
    # читаем содержимое файла
    with open('contacts.json', 'r', encoding='utf-8') as file:
        contacts = json.load(file)
    file.close()

    # меню
    print('''Список команд:
    1 - Добавить новый контакт
    2 - Найти контакт
    3 - Изменить контакт
    4 - Удалить контакт
    5 - Посмотреть все контакты 
    6 - Выход 
    ''')
    user_cmd = input('Введите команду 1-6: ').strip()
    flag_correct = False

    # пока пользователь не введет подходящую команду
    while not flag_correct:
        if user_cmd == '1':
            flag_correct = True
            add_contact(contacts)
        elif user_cmd == '2':
            flag_correct = True
            search_contact(contacts)
        elif user_cmd == '3':
            flag_correct = True
            edit_contact(contacts)
        elif user_cmd == '4':
            flag_correct = True
            del_contact(contacts)
        elif user_cmd == '5':
            flag_correct = True
            show_all_contacts(contacts)
        elif user_cmd == '6':
            break
        else:
            user_cmd = input('Неизвестная команда! Введите значение от 1 до 6').strip()

    return


def add_contact(contacts):
    # поля "Имя" и "Номер телефона" обязательны для заполнения и не могут быть пустой строкой
    name = input("Введите имя: ").strip()
    while not name:
        name = input("Поле обязательно для заполнения. Введите имя: ").strip()

    phone = input("Введите номер телефона: ")
    while not phone:
        phone = input("Поле обязательно для заполнения. Введите номер телефона: ").strip()

    note = input("Введите заметку: ")
    # попробуем присвоить id как max значение + 1
    c_id = 0
    for i in contacts:
        c_id = max(i["id"], c_id)
    c_id += 1

    # здесь еще можно было бы проверить, что введенный номер тел не был сохранен ранее
    res_list = find_contact(contacts, phone)
    if len(res_list) == 0:
        contacts.append({'id': c_id,
                         'name': name.title(),
                         'phone': phone,
                         'note': note})
        save_file(contacts)
    else:
        print("Контакт с таким номером телефона уже существует.")
        if input(f'Хотите найти и изменить контакт (да/нет)? ').lower() == 'да':
            edit_contact(contacts)

    return


def search_contact(contacts):
    str_find = input("Введите данные для поиска: ").strip()
    str_find = str_find.lower()
    res_list = find_contact(contacts, str_find)

    for i in res_list:
        print(f'{i["name"]} ({i["note"]}): {i["phone"]}')

    return


def find_contact(contacts, str_find):
    res_list = []
    for i in contacts:
        if str_find in i["name"].lower() or str_find in i["phone"].lower() or str_find in i["note"].lower():
            res_list.append({"id": i["id"],
                             "name": i["name"],
                             "note": i["note"],
                             "phone": i["phone"]})

    return res_list


def edit_contact(contacts):
    # чтобы что-то отредактировать, сначала надо что-то найти
    # тут напрашивается использование ф-ции search_contact, но результатом выполнения нужен не print, return
    # может ее надо было задекорировать, но меня не озарило :(

    res_list = []
    while len(res_list) != 1:
        str_find = (input("Какой контакт хотите изменить? ").strip()).lower()
        res_list = find_contact(contacts, str_find)

        if len(res_list) == 0:
            print("Поиск не дал результата.")
            if (input(f'Хотите прекратить поиск (да/нет)? ').strip()).lower() == 'да':
                break
        if len(res_list) > 1:
            print("Найдено более 1 контакта. Уточните данные для поиска")

    c_id = 0
    # можно было бы перебрать res_list в цикле и предложить пользаку отредактировать каждый найденный контакт.
    # но будем редактировать только если нашли точное соответствие
    if len(res_list) == 1:
        for i in contacts:
            if res_list[0]["id"] == i["id"]:
                c_id = contacts.index(i)
                break

        if input(f'Хотите изменить имя для контакта {res_list[0]["name"]} (да/нет)? ').lower() == 'да':
            res_list[0]["name"] = input("Введите новое имя ").strip().lower()

        if input(f'Хотите изменить номер телефона (да/нет)? ').lower() == 'да':
            res_list[0]["phone"] = input("Введите новый номер телефона ").strip().lower()

        if input(f'Хотите изменить заметку (да/нет)? ').lower() == 'да':
            res_list[0]["note"] = input("Введите новою заметку ").strip().lower()

        contacts[c_id].update(res_list[0])
        save_file(contacts)

    return


def del_contact(contacts):
    res_list = []
    while len(res_list) != 1:
        str_find = input("Какой контакт хотите удалить? ").strip().lower()
        res_list = find_contact(contacts, str_find)

        if len(res_list) == 0:
            print("Поиск не дал результата.")
            if input(f'Хотите прекратить поиск (да/нет)? ').strip().lower() == 'да':
                break

    c_id = 0
    if len(res_list) == 1:
        for i in contacts:
            if res_list[0]["id"] == i["id"]:
                c_id = contacts.index(i)
                break

    del contacts[c_id]
    save_file(contacts)

    return


def show_all_contacts(contacts):
    print("Список контактов: ")
    for i in contacts:
        print(f'{i["name"]} ({i["note"]}): {i["phone"]}')
    return


def save_file(contacts):
    # наверное было бы неплохо проверить, не устарел ли файл с которым работаем

    with open('contacts.json', 'w', encoding='utf-8') as file:
        json.dump(contacts, file, indent=4, ensure_ascii=False)
    file.close()

    print("Изменения в файле сохранены!")
    return


phone_book()
