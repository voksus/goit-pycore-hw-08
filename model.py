import re
import pickle   # Додано імпорт pickle
from collections import UserDict
from datetime import datetime, date, timedelta
from enum import Enum

# ============================= ENUMS ТА КОНСТАНТИ =============================

class ModelError(Enum):
    """Перелік кодів помилок для моделі."""
    INVALID_COMMAND        = "invalid_command"
    INVALID_CONTACT_NAME   = "invalid_contact_name"
    INVALID_PHONE          = "invalid_phone"
    INVALID_EMAIL          = "invalid_email"
    INVALID_BIRTHDAY       = "invalid_birthday"
    CONTACT_EXISTS         = "contact_exists"
    CONTACT_NOT_FOUND      = "contact_not_found"
    DUPLICATE_PHONE        = "duplicate_phone"
    DUPLICATE_EMAIL        = "duplicate_email"
    PHONE_NOT_FOUND        = "phone_not_found"
    EMAIL_NOT_FOUND        = "email_not_found"
    BIRTHDAY_NOT_SET       = "birthday_not_set"
    EMPTY_CONTACTS         = "empty_contacts"
    INVALID_INDEX          = "invalid_index"
    EMPTY_CONTACT_FIELDS   = "empty_contact_fields"


# ============================= КЛАСИ ВИКЛЮЧЕНЬ =============================

class CommandException(Exception):
    """Базовий клас для винятків, пов'язаних з командами."""
    def __init__(self, error_code: ModelError, message="Помилка команди", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class ContactException(Exception):
    """Базовий клас для винятків, пов'язаних з контактами."""
    def __init__(self, error_code: ModelError, message="Помилка контакту", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class PhoneException(Exception):
    """Базовий клас для винятків, пов'язаних з телефонами."""
    def __init__(self, error_code: ModelError, message="Помилка телефону", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class EmailException(Exception):
    """Базовий клас для винятків, пов'язаних з email."""
    def __init__(self, error_code: ModelError, message="Помилка email", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class BirthdayException(Exception):
    """Базовий клас для винятків, пов'язаних з датою народження."""
    def __init__(self, error_code: ModelError, message="Помилка дати народження", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)


# ============================= КЛАСИ ДАНИХ =============================

# (Field, Name, Phone, Email - без змін)
class Field:
    """Базовий клас для полів запису."""
    def __init__(self, value: str) -> None:
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self._value}')"

class Name(Field):
    """Клас для зберігання та валідації імені контакту."""
    def __init__(self, value: str) -> None:
        if not self.validate(value):
             # Передаємо name
             raise ContactException(ModelError.INVALID_CONTACT_NAME, name=value)
        super().__init__(value)

    @staticmethod
    def validate(name: str) -> bool:
        """Перевіряє коректність імені."""
        return bool(re.fullmatch(r"[A-Za-zА-Яа-яІіЇїЄєҐґ' -]{1,50}", name)) # Додав пробіл та дефіс

class Phone(Field):
    """Клас для зберігання та валідації номера телефону."""
    def __init__(self, value: str) -> None:
        if not self.validate(value):
             # Передаємо phone
             raise PhoneException(ModelError.INVALID_PHONE, phone=value)
        super().__init__(value)

    @staticmethod
    def validate(phone: str) -> bool:
        """Перевіряє, чи телефон складається рівно з 10 цифр."""
        return bool(re.fullmatch(r"\d{10}", phone))

class Email(Field):
    """Клас для зберігання та валідації email."""
    def __init__(self, value: str) -> None:
        if not self.validate(value):
             # Передаємо email
             raise EmailException(ModelError.INVALID_EMAIL, email=value)
        super().__init__(value)

    @staticmethod
    def validate(email: str) -> bool:
        """Перевіряє базовий формат email."""
        return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", email))

# --- Необхідні зміни в Birthday для сумісності з Pickle ---
class Birthday(Field):
    """Клас для зберігання та валідації дати народження."""
    # Ініціалізатор має приймати або рядок (для створення) або date (при завантаженні pickle)
    def __init__(self, value: str | date) -> None:
        parsed_date = None
        error_value = value
        if isinstance(value, date): # Якщо pickle завантажив готовий об'єкт date
            parsed_date = value
        elif isinstance(value, str): # Якщо створюємо з рядка
             error_value = value
             try:
                 parsed_date = datetime.strptime(value, '%d.%m.%Y').date()
             except ValueError:
                 # Передаємо рядок, що спричинив помилку
                 raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=error_value)
        else: # Обробка інших непередбачуваних типів
            raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=str(error_value))

        # Перевірка на майбутню дату
        if parsed_date and parsed_date > date.today():
             raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=str(error_value))
        # Зберігаємо саме об'єкт date
        super().__init__(parsed_date) # Викликаємо __init__ базового класу Field

    # Property повертає саме об'єкт date
    @property
    def value(self) -> date:
        return self._value

    # Сетер також має приймати або рядок, або date
    @value.setter
    def value(self, new_value: str | date) -> None:
        parsed_date = None
        error_value = new_value
        if isinstance(new_value, date):
            parsed_date = new_value
        elif isinstance(new_value, str):
             error_value = new_value
             try:
                 parsed_date = datetime.strptime(new_value, '%d.%m.%Y').date()
             except ValueError:
                 raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=error_value)
        else:
            raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=str(error_value))

        # Перевірка на майбутню дату
        if parsed_date and parsed_date > date.today():
            raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=str(error_value))
        # Зберігаємо саме об'єкт date
        self._value = parsed_date

    def __str__(self) -> str:
        """Повертає дату у форматі DD.MM.YYYY або 'Не вказано'."""
        # _value може бути None, якщо поле не встановлено або видалено
        return self._value.strftime('%d.%m.%Y') if self._value else "Не вказано"


# ============================= ЗАПИС КОНТАКТУ =============================

class Record:
    """Клас для представлення запису контакту в адресній книзі."""
    def __init__(self, name: str) -> None:
        """Ініціалізує запис з іменем та порожніми списками полів."""
        # Ім'я валідується при створенні об'єкта Name
        self.name: Name = Name(name)
        # Використовуємо списки для легшого керування індексами
        self.phones: list[Phone] = []
        self.emails: list[Email] = []
        self.birthday: Birthday | None = None

    # --- Робота з телефонами ---
    def add_phone(self, phone_str: str) -> None:
        """Додає телефон до контакту. Кидає PhoneException при помилках."""
        if any(p.value == phone_str for p in self.phones):
            # Передаємо name та phone для форматування
            raise PhoneException(ModelError.DUPLICATE_PHONE, name=self.name.value, phone=phone_str)
        # Валідація відбудеться при створенні Phone
        self.phones.append(Phone(phone_str))

    def edit_phone(self, index: int, new_phone_str: str) -> None:
        """Редагує телефон за індексом. Кидає PhoneException при помилках."""
        try:
            self.phones[index] = Phone(new_phone_str)
        except IndexError:
            # Передаємо name та index для форматування
            raise PhoneException(ModelError.PHONE_NOT_FOUND, name=self.name.value, index=index)
        except PhoneException as e: # Якщо Phone() кинув помилку формату
             e.kwargs['name'] = self.name.value # Додамо ім'я до існуючих kwargs
             raise e

    def remove_phone(self, index: int) -> None:
        """Видаляє телефон за індексом. Кидає PhoneException при помилці."""
        try:
            del self.phones[index]
        except IndexError:
            # Передаємо name та index
            raise PhoneException(ModelError.PHONE_NOT_FOUND, name=self.name.value, index=index)

    # --- Робота з email (аналогічно) ---
    def add_email(self, email_str: str) -> None:
        if any(e.value == email_str for e in self.emails):
            # Передаємо name та email
            raise EmailException(ModelError.DUPLICATE_EMAIL, name=self.name.value, email=email_str)
        self.emails.append(Email(email_str))

    def edit_email(self, index: int, new_email_str: str) -> None:
        try:
            self.emails[index] = Email(new_email_str)
        except IndexError:
            # Передаємо name та index
            raise EmailException(ModelError.EMAIL_NOT_FOUND, name=self.name.value, index=index)
        except EmailException as e: # Якщо Email() кинув помилку формату
             e.kwargs['name'] = self.name.value # Додамо ім'я
             raise e

    def remove_email(self, index: int) -> None:
        try:
            del self.emails[index]
        except IndexError:
            # Передаємо name та index
            raise EmailException(ModelError.EMAIL_NOT_FOUND, name=self.name.value, index=index)

    # --- Робота з днем народження  ---
    # Дозволяємо передавати str або date для гнучкості
    def add_birthday(self, birthday_input: str | date) -> None:
        """Додає або оновлює день народження."""
        try:
            if self.birthday:
                # Якщо день народження вже існує, оновлюємо через сетер
                self.birthday.value = birthday_input
            else:
                # Якщо ні, створюємо новий об'єкт Birthday
                self.birthday = Birthday(birthday_input)
        except BirthdayException as e:
             # Додаємо ім'я до контексту помилки, якщо його там ще немає
             if 'name' not in e.kwargs:
                e.kwargs['name'] = self.name.value
             # Якщо помилка виникла при парсингу рядка, додаємо цей рядок до контексту
             if isinstance(birthday_input, str) and 'birthday' not in e.kwargs:
                e.kwargs['birthday'] = birthday_input
             raise e # Перекидаємо виняток з доповненими kwargs

    def remove_birthday(self) -> None:
         if self.birthday is None:
             raise BirthdayException(ModelError.BIRTHDAY_NOT_SET, name=self.name.value)
         self.birthday = None

    def __str__(self) -> str:
        """Повертає рядкове представлення запису."""
        phones_str = "; ".join(f"[{i}] {p.value}" for i, p in enumerate(self.phones)) or "Немає"
        emails_str = "; ".join(f"[{i}] {e.value}" for i, e in enumerate(self.emails)) or "Немає"
        # Використовуємо __str__ об'єкта Birthday, який коректно обробляє None
        birthday_str = str(self.birthday) if self.birthday else "Не вказано"
        return (f"Ім'я: {self.name.value}\n"
                f"  Телефони: {phones_str}\n"
                f"  Emails: {emails_str}\n"
                f"  День народження: {birthday_str}")


# ============================= АДРЕСНА КНИГА =============================

class AddressBook(UserDict):
    """Клас для представлення адресної книги."""

    def add_record(self, record: Record) -> None:
        if record.name.value in self.data:
            # Передаємо name
            raise ContactException(ModelError.CONTACT_EXISTS, name=record.name.value)
        self.data[record.name.value] = record

    def find(self, name: str) -> Record:
        record = self.data.get(name)
        if record is None:
            # Передаємо name
            raise ContactException(ModelError.CONTACT_NOT_FOUND, name=name)
        return record

    def delete(self, name: str) -> None:
        if name not in self.data:
            # Передаємо name
            raise ContactException(ModelError.CONTACT_NOT_FOUND, name=name)
        del self.data[name]

    def get_upcoming_birthdays(self, days: int = 7) -> list[dict[str, str]]:
        """
        Повертає список користувачів, яких потрібно привітати на наступному тижні.

        Args:
            days (int): Кількість днів наперед для перевірки (за замовчуванням 7).

        Returns:
            list[dict[str, str]]: Список словників з ім'ям та датою привітання.
                                   Приклад: [{'name': 'Ім'я', 'congratulation_date': 'DD.MM.YYYY'}]
        """
        upcoming_birthdays = []
        today = date.today()
        for record in self.data.values():
            # Перевіряємо наявність birthday та його значення (value повертає date)
            if record.birthday and record.birthday.value:
                bday: date = record.birthday.value
                # Переносимо дату народження на поточний рік
                birthday_this_year = bday.replace(year=today.year)

                # Якщо день народження вже минув цього року, розглядаємо наступний рік
                if birthday_this_year < today:
                    birthday_this_year = bday.replace(year=today.year + 1)

                # Порівнюємо з сьогоднішньою датою та інтервалом 'days'
                days_to_birthday = (birthday_this_year - today).days
                if 0 <= days_to_birthday < days:
                    # Визначаємо день тижня
                    weekday = birthday_this_year.weekday() # Пн=0..Нд=6

                    # Визначаємо дату привітання (переносимо з вихідних на Пн)
                    congratulation_date = birthday_this_year
                    if weekday >= 5: # Сб або Нд
                        days_to_monday = 7 - weekday
                        congratulation_date += timedelta(days=days_to_monday)
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime('%d.%m.%Y'),
                        "birthday_date": bday.strftime('%d.%m.%Y'), # Додамо реальну дату для інформації
                        "original_weekday": birthday_this_year.weekday() # Для можливого відображення дня тижня
                    })
        # Сортуємо за датою привітання
        upcoming_birthdays.sort(key=lambda x: datetime.strptime(x['congratulation_date'], '%d.%m.%Y').date())
        return upcoming_birthdays


# ============================= СЕРІАЛІЗАЦІЯ (з використанням Pickle) =============================

# Змінено ім'я файлу за замовчуванням на відповідне для pickle
DEFAULT_FILENAME = "contacts.pkl"

def save_contacts(book: AddressBook, filename: str = DEFAULT_FILENAME) -> None:
    """Зберігає адресну книгу у файл за допомогою pickle."""
    try:
        # Відкриваємо файл для бінарного запису ('wb')
        with open(filename, "wb") as file:
            # Використовуємо pickle.dump для серіалізації всього об'єкта book
            pickle.dump(book, file)
    except (IOError, pickle.PicklingError) as e:
        # Обробляємо можливі помилки запису або серіалізації pickle
        print(f"Помилка збереження файлу '{filename}': {e}")


def load_contacts(filename: str = DEFAULT_FILENAME) -> AddressBook:
    """Завантажує адресну книгу з файлу за допомогою pickle."""
    try:
        # Відкриваємо файл для бінарного читання ('rb')
        with open(filename, "rb") as file:
            # Використовуємо pickle.load для десеріалізації об'єкта
            book = pickle.load(file)
            # Додаткова перевірка типу завантаженого об'єкта
            if isinstance(book, AddressBook):
                return book
            else:
                print(f"Помилка: Файл '{filename}' містить не об'єкт AddressBook.")
                return AddressBook() # Повертаємо порожню книгу
    except FileNotFoundError:
        # Це нормально, якщо файл ще не створено
        print(f"Файл контактів '{filename}' не знайдено. Буде створено новий при збереженні.")
        return AddressBook() # Повертаємо нову порожню книгу
    except (pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError, IOError, TypeError) as e:
        # Ловимо ширший спектр можливих помилок при завантаженні pickle
        # TypeError може виникнути, якщо структура класів змінилась несумісно
        print(f"Помилка завантаження даних з файлу '{filename}': {e}. Створення нової адресної книги.")
        return AddressBook() # Повертаємо порожню книгу у разі помилки