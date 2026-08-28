import datetime
from timedelta import Timedelta

month = datetime.datetime.now().month
day = datetime.datetime.now()
year = datetime.datetime.now().year
last_day = (day - Timedelta(days=1)).day
today = datetime.datetime.now().day

