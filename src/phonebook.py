import json

class Contact:
    def __init__(self, cid: int, name: str, phone: str, note: str = ""):
        self.id = cid
        self.name = name
        self.phone = phone
        self.note = note

#    def __getitem__(self, index):
#        return self[index]

    #валидация имени
    @staticmethod
    def _validate_name(name: str) -> str:
        if not name:
            raise ValueError("Имя не может быть пустым")
        return name.strip().title()

    #валидация номера телефона
    @staticmethod
    def _validate_phone(phone: str) -> str:
        if not phone:
            raise ValueError("Номер телефона не может быть пустым")
        return phone.strip()

class PhoneBook:
    def __init__(self, filename: str = "contacts.json"):
        self.filename: str = filename
        self.contacts: list[Contact] = self.__load_contacts()

    #def __getitem__(self, index):
    #    return self.contacts[index]

    #загрузка контактов из файла
    def __load_contacts(self) -> list[Contact]:
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                contacts = json.load(file)
            file.close()
            return contacts

        except FileNotFoundError:
            # Создаем пустой файл и возвращаем пустой список
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump([], file)
                file.close()
            return []

    def __update_contacts(self, contact: list[Contact]):
        c_id = self.__search_index(contact[0]["id"])

        self.contacts[c_id].update(contact[0])
        return

    def __save_contacts_in_file(self):
        try:
            with open('contacts.json', 'w', encoding='utf-8') as file:
                json.dump(self.contacts, file, indent=4, ensure_ascii=False)
            file.close()
            return True
        except PermissionError as e:
            print(f"Ошибка прав доступа: {e}")
            return False

    def __search_index(self, query: int) -> int:
        for i in self.contacts:
            if query == i["id"]:
                return self.contacts.index(i)
        return -1

    def add_contact(self, name: str, phone: str, note: str=""):
        # реализация добавления нового контакта
        # Валидация данных
        validated_name = Contact._validate_name(name)
        validated_phone = Contact._validate_phone(phone)

        # Проверка на существующий контакт с таким же номером
        for contact in self.contacts:
            if contact["phone"] == validated_phone:
                raise ValueError("Контакт с таким номером телефона уже существует")

        # Генерация нового ID
        new_id = max((c["id"] for c in self.contacts), default=0) + 1

        # Создание нового контакта
        new_contact = Contact(new_id, validated_name, validated_phone, note)

        # Преобразуем объект Contact в словарь и добавляем в список контактов
        self.contacts.append({
            "id": new_contact.id,
            "name": new_contact.name,
            "phone": new_contact.phone,
            "note": new_contact.note
        })
        self.__save_contacts_in_file()
        return True

    def edit_contact(self, query: str) -> tuple[bool, str]:
        # реализация редактирования
        contact = self.search_contact(query)
        if len(contact) == 1:
            # Запрашиваем новые значения
            new_name = input(f"Введите новое имя (оставьте пустым для сохранения '{contact[0]["name"]}'): ").strip()
            if new_name:
                contact[0]["name"] = new_name.title()

            new_phone = input(f"Введите новый телефон (оставьте пустым для сохранения '{contact[0]["phone"]}'): ").strip()
            if new_phone:
                # Проверяем, что новый телефон не повторяется
                for c in self.contacts:
                    if c["id"] != contact[0]["id"] and c["phone"] == new_phone:
                        return (False, "Контакт с таким номером уже существует")
                contact[0]["phone"] = new_phone

            new_note = input(f"Введите новую заметку (оставьте пустым для сохранения '{contact[0]["note"]}'): ").strip()
            if new_note:
                contact[0]["note"] = new_note
            #обновим данные в словаре
            self.__update_contacts(contact)
            # Сохраняем изменения в файле
            self.__save_contacts_in_file()
            return (True, "Контакт успешно изменен")
        else:
            return (False, "Не удалось установить точное соответствие. Проверьте введённые данные и попробуйте ещё раз.")

    def search_contact(self, query: str) -> list[Contact]:
        # реализация поиска
        query = query.lower()
        res_list = []
        for i in self.contacts:
            if (query in i["name"].lower() or
                query.replace(" ", "") in i["phone"].lower().replace(" ", "") or
                query in i["note"].lower()):
                res_list.append({"id": i["id"],
                                 "name": i["name"],
                                 "note": i["note"],
                                 "phone": i["phone"]})

        return res_list

    def delete_contact(self, query: str):
        # реализация удаления
        contact = self.search_contact(query)
        # удалим только если найден только один контакт
        if len(contact) == 1:
            c_id = self.__search_index(contact[0]["id"])
            # удаляем данные в словаре
            del self.contacts[c_id]
            # Сохраняем изменения в файле
            self.__save_contacts_in_file()
            return True
        else:
            return False

    def show_all_contacts(self):
        # реализация вывода всех контактов
        for i in self.contacts:
            print(f'{i["name"]} ({i["note"]}): {i["phone"]}')

        return