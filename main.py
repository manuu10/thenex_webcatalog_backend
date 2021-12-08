import pymysql
from app import app
from config import mysql
from flask import jsonify
from flask import flash, request


@app.route('/products')
def product():
    try:
        search = request.args.get('search', default='', type=str)
        cat = request.args.get('category', default='', type=str)
        search = "%"+search+"%"
        cat = "%"+cat+"%"
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT *
              FROM thenexartikelstammclean
              WHERE artikelgruppe like %s 
              AND Bezeichnung <> '' AND
              (
                  Bezeichnung like %s OR
                  Beschreibung like %s OR
                  Beschreibung_2 like %s OR
                  Beschreibung_3 like %s
              )
        """, (cat, search, search, search, search))
        empRows = cursor.fetchall()
        respone = jsonify(empRows)
        respone.status_code = 200

        return respone
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/products/<string:id>')
def productById(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM thenexartikelstammclean WHERE artikelnummer=%s", id)
        empRow = cursor.fetchone()
        respone = jsonify(empRow)
        respone.status_code = 200

        return respone
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/categories')
def categories():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(""" 
            SELECT artikelgruppe as name,COUNT(*) as count
              FROM thenexartikelstammclean
              WHERE artikelgruppe REGEXP '^[0-9]'
              GROUP BY artikelgruppe 
        """)
        empRow = cursor.fetchall()
        respone = jsonify(empRow)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/categories/<string:query>')
def categoriesSearch(query):
    query = "%"+query+"%"
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
        SELECT artikelgruppe as name,COUNT(*) as count
            FROM thenexartikelstammclean
            WHERE artikelgruppe REGEXP '^[0-9]' AND
            (
                Bezeichnung like %s OR
                Beschreibung like %s OR
                Beschreibung_2 like %s OR
                Beschreibung_3 like %s
            )
            GROUP BY name
            ORDER BY count DESC
            LIMIT 10
        """, (query, query, query, query))
        empRow = cursor.fetchall()
        respone = jsonify(empRow)
        respone.status_code = 200

        return respone
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Record not found: ' + request.url,
    }
    respone = jsonify(message)
    respone.status_code = 404
    return respone


if __name__ == "__main__":
    app.run(debug=True)
