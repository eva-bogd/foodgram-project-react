import configparser
import csv

import psycopg2

config = configparser.ConfigParser()
config.read('config.ini')

try:
    conn = psycopg2.connect(
        database=config['postgresql']['database'],
        user=config['postgresql']['user'],
        password=config['postgresql']['password'],
        host=config['postgresql']['host'],
        port=config['postgresql']['port'])
    cur = conn.cursor()

    with open('../../data/ingredients.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            cur.execute(f"INSERT INTO recipes_ingredient"
                        f"(name, measurement_unit) VALUES ({row}, {row})")
except Exception as e:
    print(f'Error: {e}')
    conn.rollback()

conn.commit()
cur.close()
conn.close()
