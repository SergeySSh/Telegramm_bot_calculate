# План исправлений TelegrammBot

## 🔴 P0 — Критические (ломает функциональность)

### 01. Исправить формат даты в insert_data и get_data

**Проблема:** Даты сохраняются как Unix-timestamp (int), а в SQL-запросах сравниваются как строки `'%Y-%m-%d'`. Все отчёты всегда пустые.

**Где:** `data_base/requests_sql.py` → `insert_data()`, `my_costs.py` → `get_data_month_or_day()`, `send_report()`, `enter_expenditure()`

**Действия:**
- [ ] В `insert_data` параметр `date` приводить к строке `datetime.fromtimestamp(date).strftime('%Y-%m-%d')`
- [ ] В `my_costs.py` — везде, где передаётся дата (`message.date`), использовать `datetime.fromtimestamp(message.date).strftime('%Y-%m-%d')`
- [ ] Убрать `.date()` у `message.date` (это `int`, у него нет метода `.date()`)

**Пример:**
```python
# my_costs.py — вместо message.date.date():
date_str = datetime.fromtimestamp(message.date).strftime('%Y-%m-%d')
```

---

### 02. Защита от SQL-инъекции через name_user/name_id

**Проблема:** Имена пользователей подставляются в SQL через f-string без валидации. Злоумышленник может выполнить произвольный SQL.

**Где:** `data_base/requests_sql.py` — все методы: `start_data`, `insert_data`, `get_data`, `del_data`, `del_data_all`

**Действия:**
- [ ] Добавить функцию валидации имени таблицы:
  ```python
  import re

  def _safe_table_name(name: str) -> str:
      name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9_ ]', '', name)
      return name.replace(' ', '_')
  ```
- [ ] В каждом методе заменить f-string вставки имени на вызов `_safe_table_name(name_user)`
- [ ] Заменить `f'INSERT INTO {name_user} ...'` на `'INSERT INTO ' + _safe_table_name(name_user) + ' ...'`

---

## 🟡 P1 — Средние (архитектура, стабильность)

### 03. Перенести connection/cursor из класса в __init__

**Проблема:** `base` и `cur` — атрибуты класса, а не экземпляра. Все инстансы `DataBase` делят одно соединение → гонки при конкурентном polling'е.

**Где:** `data_base/requests_sql.py` → строки 4-5

**Действия:**
- [x] Убрать `base = ...` и `cur = ...` из body класса
- [x] Добавить `__init__`:
  ```python
  def __init__(self):
      self.base = sqlite3.connect('data_base/telegram.db')
      self.cur = self.base.cursor()
  ```
- [x] Проверить что все методы обращаются к `self.base` и `self.cur`

---

### 04. Закрытие соединения БД

**Проблема:** Каждый новый `DataBase()` создаёт соединение, но `close()` никогда не вызывается. Утечка соединений.

**Где:** `data_base/requests_sql.py`

**Действия:**
- [x] Добавить метод `close()`:
  ```python
  def close(self):
      self.cur.close()
      self.base.close()
  ```
- [x] Вызывать `close()` при завершении работы бота (в `main()` — после `dp.start_polling()`)

---

### 05. Исправить дублирование cursor в get_data

**Проблема:** Второй `execute` на том же буферизованном курсоре возвращает результат первого запроса.

**Где:** `data_base/requests_sql.py` → `get_data()`, строки 40-52

**Действия:**
- [x] Использовать `self.base.cursor()` для второй выборки:
  ```python
  cur2 = self.base.cursor()
  cur2.execute(...)
  report = cur2.fetchone()
  cur2.close()
  ```
- [x] Либо переписать как один запрос для итога:
  ```python
  self.cur.execute(f'SELECT SUM(all_price) as total FROM ({first_query})')
  ```

---

## 🟢 P2 — Низкие (надёжность, чистота кода)

### 06. Защита del_data от пустой таблицы

**Проблема:** `fetchone()` возвращает `None` на пустой таблице → `NoneIndexError`.

**Где:** `data_base/requests_sql.py` → `del_data()`, строка 57

**Действия:**
- [x] Добавить проверку:
  ```python
  last_record = self.cur.fetchone()
  if last_record is None:
      raise ValueError('Нет записей для удаления')
  ```

---

### 07. Добавить логирование вместо print()

**Проблема:** `print(ex)` скрывает ошибки от разработчика.

**Где:** `my_costs.py` → `del_last_record()`, `enter_expenditure()`, `requests_sql.py` → `insert_data()`

**Действия:**
- [x] Добавить `import logging`
- [x] Заменить `print(ex)` на `logging.exception(ex)`
- [x] Настроить basicConfig в `main()`

---

### 08. Опечатка в имени файла requirements.txt

**Проблема:** `requrements.txt` вместо `requirements.txt`

**Действия:**
- [x] Переименовать файл в `requirements.txt`

---

### 09. Добавить .gitignore для telegram.db

**Проблема:** Файл БД `telegram.db` может попасть в репозиторий.

**Действия:**
- [x] Добавить в `.gitignore`:
  ```
  data_base/telegram.db
  .env
  __pycache__/
  *.pyc
  ```

---

### 10. Добавить __init__.py в data_base/

**Действия:**
- [ ] Создать пустой файл `data_base/__init__.py`

---

## Порядок выполнения

1. **P0-02** (SQL-инъекция) — критично для безопасности, сделать в первую очередь
2. **P0-01** (дата) — без этого бот не показывает отчёты
3. **P1-03** (connection в __init__) — без этого гонки при multi-user
4. **P1-05** (cursor duplication) — сломанные отчёты
5. **P1-04** (close БД) — утечка соединений
6. **P2-06**... **P2-10** — мелкая надёжность и чистота
