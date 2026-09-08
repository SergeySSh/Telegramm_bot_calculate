# import datetime
import logging
import re
import sqlite3


def _safe_table_name(name: str) -> str:
    """Защищает имя таблицы от SQL-инъекции, удаляя опасные символы."""
    name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9_]', '_', name)
    return name


class DataBase:
    def __init__(self):
        self.base = sqlite3.connect('data_base/telegram.db')
        self.cur = self.base.cursor()

    def start_data(self, name_id):
        safe_name = _safe_table_name(name_id)
        self.cur.execute(
            f'CREATE TABLE IF NOT EXISTS {safe_name} (coast text, price real, date)'
        )
        self.base.commit()

    def insert_data(self, name_user, coast, price, date):
        data = ()
        my_coast, my_price = '', ''
        if coast.isalpha() and price.isdigit():
            data = (
                coast.lower(),
                price.lower(),
                date
            )
            my_coast, my_price = coast, price
        elif coast.isdigit() and price.isalpha():
            data = (
                price.lower(),
                coast.lower(),
                date
            )
            my_coast, my_price = price, coast
        else:
            logging.warning('Некорректный ввод: coast или price не являются строкой/числом')
            return my_coast, my_price
        safe_name = _safe_table_name(name_user)
        self.cur.execute(
            f'INSERT INTO {safe_name} VALUES(?, ?, ?)', data
        )
        self.base.commit()
        return my_coast, my_price

    def get_data(self, name_user, val_date):
        safe_name = _safe_table_name(name_user)
        self.cur.execute(
            f"""SELECT coast, SUM(price) as all_price
               FROM {safe_name}
               WHERE 
               CASE 
	               WHEN length('{val_date}') == 10 THEN strftime('%Y-%m-%d', date) == '{val_date}'
	               WHEN length('{val_date}') == 7 THEN strftime('%Y-%m', date) == '{val_date}'
	               ELSE strftime('%Y', date) == '{val_date}'
	               END 
               GROUP BY coast"""
        )

        name_price = []
        for rep in self.cur.fetchall():
            product = 'на ' + rep[0].lower() + ': ' + str(int(rep[1])) + ' руб.'
            name_price.append(product)

        cur2 = self.base.cursor()
        cur2.execute(
            f"""SELECT coast, SUM(price) as all_price
               FROM {safe_name}
               WHERE 
               CASE 
	               WHEN length('{val_date}') == 10 THEN strftime('%Y-%m-%d', date) == '{val_date}'
	               WHEN length('{val_date}') == 7 THEN strftime('%Y-%m', date) == '{val_date}'
	               ELSE strftime('%Y', date) == '{val_date}'
	               END 
            """
        )
        report = cur2.fetchone()
        cur2.close()
        self.base.commit()
        return '\n'.join(name_price), (int(report[1]) if report[1] is not None else None)

    def del_data(self, name_user):
        safe_name = _safe_table_name(name_user)
        self.cur.execute(
            f"""SELECT coast, price 
            FROM {safe_name} 
            WHERE date == (SELECT MAX(date) as time FROM {safe_name})"""
        )
        last_record = self.cur.fetchone()
        if last_record is None:
            raise ValueError('Нет записей для удаления')
        self.cur.execute(
            f"""DELETE FROM {safe_name} 
            WHERE date == (SELECT MAX(date) as time FROM {safe_name})"""
        )
        self.base.commit()
        return last_record[0].lower() + ' ' + str(int(last_record[1]))

    def del_data_all(self, name_user):
        safe_name = _safe_table_name(name_user)
        safe_dup = safe_name + '_DUPLICATE'
        self.cur.execute(
            f'CREATE TABLE IF NOT EXISTS {safe_dup} (coast text, price real, date)'
        )
        self.cur.execute(
            f'INSERT INTO {safe_dup} SELECT coast, price, date FROM {safe_name}'
        )
        self.cur.execute(
            f'DELETE FROM {safe_name}'
        )

        self.base.commit()

    def close(self):
        self.cur.close()
        self.base.close()
