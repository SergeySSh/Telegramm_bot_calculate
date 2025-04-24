# import datetime
import sqlite3


class DataBase:
    base = sqlite3.connect('data_base/telegram.db')
    cur = base.cursor()

    def start_data(self, name_id):
        self.cur.execute(
            f'CREATE TABLE IF NOT EXISTS {name_id} (coast text, price real, date)'
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
            print('Ошибка ввода статьи затрат!')
        self.cur.execute(
            f'INSERT INTO {name_user} VALUES(?, ?, ?)', data
        )
        self.base.commit()
        return my_coast, my_price

    def get_data(self, name_user, val_date):
        self.cur.execute(
            f"""SELECT coast, SUM(price) as all_price
               FROM {name_user}
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
        self.cur.execute(
            f"""SELECT coast, SUM(price) as all_price
               FROM {name_user}
               WHERE 
               CASE 
	               	WHEN length('{val_date}') == 10 THEN strftime('%Y-%m-%d', date) == '{val_date}'
               		WHEN length('{val_date}') == 7 THEN strftime('%Y-%m', date) == '{val_date}'
               		ELSE strftime('%Y', date) == '{val_date}'
               		END 
            """
        )
        report = self.cur.fetchone()
        self.base.commit()
        return '\n'.join(name_price), (int(report[1]) if report[1] is not None else None)

    def del_data(self, name_user):
        self.cur.execute(
            """
            SELECT coast, price 
            FROM {} 
            WHERE date == (SELECT MAX(date) as time 
                           FROM {})""".format(name_user, name_user)
        )
        last_record = self.cur.fetchone()
        self.cur.execute(
            """
            DELETE FROM {} 
            WHERE date == (SELECT MAX(date) as time 
                           FROM {})""".format(name_user, name_user)
        )
        self.base.commit()
        return last_record[0].lower() + ' ' + str(int(last_record[1]))

    def del_data_all(self, name_user):
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS {}_DUPLICATE(coast text, price real, date)""".format(name_user)
        )
        self.cur.execute(
            """
            INSERT INTO {}_DUPLICATE
                    SELECT coast, price, date
                    FROM {}""".format(name_user, name_user)
        )
        self.cur.execute(
            """
            DELETE FROM {}""".format(name_user)
        )

        self.base.commit()
