from flask_mysqldb import MySQL
from flask import Flask

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Nadiya@321'
app.config['MYSQL_DB'] = 'store_db'

mysql = MySQL(app)