from psycopg2 import connect
from psycopg2.extras import RealDictCursor

from clcrypto import generate_salt, password_hash, check_password


def create_conenction(db_name='communications_server'):
    # Otwarcie połączenie do podanej bazy danych.
    db_connection = connect(
        user='postgres',
        password='coderslab',
        host='localhost',
        database=db_name
    )
    # Włączenie autocommit powoduje natychmiastowe wykonanie poleceń typu swtórz tabelę(transakcji)
    db_connection.autocommit = True
    # Zwrócenie połączenia.
    return db_connection


def get_cursor(db_connection):
    # Utworzenie kursora aby wykonać polecenie sql na bazie.
    return db_connection.cursor(cursor_factory=RealDictCursor)


class _Model:
    TABLE_NAME = None

    def __init__(self):
        self._id = -1

    @property
    def id(self):
        # Getter do odczytu ID
        return self._id

    def delete(self, cursor):
        # SQL do usunięcia wpisu w bazie danych poprzez ID
        sql = "DELETE FROM {TABLE_NAME} WHERE id={id}".format(TABLE_NAME=self.TABLE_NAME, id=self.id)
        cursor.execute(sql)  # wykonanie

    @classmethod
    def load_all(cls, cursor):
        # Pobranie danych z bazy danych
        sql = "SELECT * FROM {TABLE_NAME}".format(TABLE_NAME=cls.TABLE_NAME)
        cursor.execute(sql)
        data = []
        # Stworzenie listy obiektów na podstawie otrzymanych danych
        for record in cursor.fetchall():
            object = cls._create_object(
                **record)  # Stworzenie jednego obiektu reprezentującego jeden wpis w bazie danych
            data.append(object)  # Dodanie obiektu do listy
        return data  # Zwrócenie listy obiektów lub pustej

    @classmethod
    def load_by_id(cls, cursor, id):
        # SQL aby pobrać dokładnie jeden wpis z bazy danych poprzez ID
        sql = "SELECT * FROM {TABLE_NAME} WHERE id='{id}'".format(TABLE_NAME=cls.TABLE_NAME, id=id)
        cursor.execute(sql)
        record = cursor.fetchone()  # Wyciągnięcie danych z kursora
        if record:
            return cls._create_object(**record)  # Stworzenie obiektu jeśli baza zwróciła dane
        return None  # Zwrócenie non jeśli wpis z podanym ID nie istnieje

    @classmethod
    def _create_object(cls, *args, **kwargs):
        raise NotImplemented  # To trzeba napisać samemu ;)


class User(_Model):
    TABLE_NAME = 'users'

    def __init__(self):
        super(User, self).__init__()
        self.username = ''
        self.email = ''
        self._hashed_password = ''

    def save(self, cursor):
        if self.id == -1:
            # Jeśli ID = -1 to znaczy że obiekt jest stworzony poprzez kod i nie istnieje jego odpowiednik w bazie danych
            self._create_record_db(cursor)
            return True
        else:
            # Jeśli ID != -1 obiekt ma swój odpowiednik w bazie danych także go aktualizujemy
            self._update_record_in_db(cursor)
            return False

    def set_password(self, password, salt):
        # ustawia hasło od razu je szyfrując
        self._hashed_password = password_hash(password, salt)

    def check_password(self, password_to_check):
        # porównanie haseł
        return check_password(password_to_check, self._hashed_password)

    @classmethod
    def load_by_email(cls, cursor, email):
        # Wczytanie danych z bazy danych poprzez email
        sql = "SELECT * FROM users WHERE email=%s"
        cursor.execute(sql, (email,))
        record = cursor.fetchone()
        if record:
            return cls._create_object(**record)  # zwrócenie obiektu
        return None

    @classmethod
    def _create_object(cls, username, email, hashed_password, id=-1):
        user = User()
        user.username = username
        user.email = email
        user._id = id
        user._hashed_password = hashed_password
        return user

    def _create_record_db(self, cursor):
        # SQL aby dodać obiekt do bazy
        sql = "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s) RETURNING id"
        cursor.execute(sql, (self.username, self.email, self._hashed_password))
        user_id = cursor.fetchone()['id']  # Aktualizacna ID, przyznanego przez bazę
        self._id = user_id

    def _update_record_in_db(self, cursor):
        # Aktualizacja wpisu w bazie danych
        sql = "UPDATE Users SET email=%s, username=%s, hashed_password=%s WHERE id=%s"
        cursor.execute(sql, (self.email, self.username, self._hashed_password), self.id)


class Message(_Model):
    TABLE_NAME = 'messages'

    def __init__(self):
        super(Message, self).__init__()
        self.from_id = ""
        self.to_id = ""
        self.text = ""
        self.creation_date = ""

    @classmethod
    def _create_object(cls, from_id, to_id, text, creation_date, id=-1):
        message = Message()
        message.from_id = from_id
        message.to_id = to_id
        message.text = text
        message.creation_date = creation_date
        return message

    def save(self, cursor):
        if self._id == -1:
            sql = """INSERT INTO messages(from_id, to_id, text, creation_date) VALUES(%s, %s, %s, NOW()) RETURNING id"""
            values = (self.from_id, self.to_id, self.text)
            cursor.execute(sql, values)
            self._id = cursor.fetchone()[0]
            return True
        else:
            sql = """UPDATE messages SET from_id=%s, to_id=%s, text=%s WHERE id=%s"""
            values = (self.from_id, self.to_id, self.text, self._id)
            cursor.execute(sql, values)
            return True

    @classmethod
    def load_message_by_id(cls, cursor, message_id):
        sql = "SELECT id, from_id, to_id, text, creation_date FROM Messages WHERE id=%s"
        cursor.execute(sql, (message_id,))
        record = cursor.fetchone()
        if record:
            return cls._create_object(**record)
        return None

    @classmethod
    def load_all_messages(cls, cursor):
        sql = "SELECT id, from_id, to_id, text, creation_date FROM Messages"
        cursor.execiute(sql)
        messages = []
        for data in cursor.fetchall():
            loaded_message = Message()
            loaded_message.__id = data[0]
            loaded_message.from_id = data[1]
            loaded_message.to_id = data[2]
            loaded_message.text = data[3]
            loaded_message.creation_date = data[4]
            messages.append(loaded_message)
        return messages

    @classmethod
    def load_all_messages_for_user(cls, cursor, to_id):
        sql = "SELECT id, from_id, to_id, text, creation_date FROM Messages WHERE to_id=%s"
        cursor.execute(sql, (to_id, ))
        record = []
        for data in cursor.fetchall():
            loaded_msg = Message()
            loaded_msg.__id = data[0]
            loaded_msg.from_id = data[1]
            loaded_msg.to_id = data[2]
            loaded_msg.text = data[3]
            loaded_msg.creation_date = data[4]
            record.append(loaded_msg)
        return record


if __name__ == '__main__':
    salt = generate_salt()

    connection = create_conenction()
    cursor = get_cursor(connection)

    user1 = User()
    user1.username = 'User1'
    user1.email = 'user1@domain.com'
    user1.set_password('pass', salt)
    user1.save(cursor)

    user2 = User()
    user2.username = 'User2'
    user2.email = 'user2@domain.com'
    user2.set_password('pass', salt)
    user2.save(cursor)

    print(User.load_all(cursor))
    print(User.load_by_id(cursor, 6))
    print(User.load_by_email(cursor, 'user2@domain.com'))
    user2.delete(cursor)
    print('Usunięcie', user2)
    print(User.load_all(cursor))

    cursor.close()
    connection.close()
