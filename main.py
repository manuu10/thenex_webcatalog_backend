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


@app.route('/productsById')
def productsById():
    try:
        ids = request.args.get('ids', default='[]', type=str)
        ids = ids.replace("[", "(")
        ids = ids.replace("]", ")")
        print(ids)
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT *
              FROM thenexartikelstammclean
              WHERE artikelnummer IN
        """ + ids)
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


@app.route('/request')
def doRequest():
    import json
    try:
        # conn = mysql.connect()
        # cursor = conn.cursor(pymysql.cursors.DictCursor)
        # cursor.execute("""""", ())
        sender = "app.testing.manu@gmail.com"
        pw = "Qg2nXRyDvSXABkTG"
        receiver = "app.testing.manu@gmail.com"
        subject = "Request Received"
        company = request.args.get("company", default='', type=str)
        firstname = request.args.get("firstname", default='', type=str)
        lastname = request.args.get("lastname", default='', type=str)
        email = request.args.get("email", default='', type=str)
        telephone = request.args.get("telephone", default='', type=str)
        additional = request.args.get("additional", default='', type=str)
        # get product informations
        idsJson = request.args.get("productids", default='[]', type=str)
        ids = idsJson.replace("[", "(")
        ids = ids.replace("]", ")")
        print(ids)
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT *
              FROM thenexartikelstammclean
              WHERE artikelnummer IN
        """ + ids)
        products = cursor.fetchall()

        body = f"""New Request from {lastname},{firstname} ({company})
        Contact data:
         - {email}
         - {telephone}

        additional Information:
        {additional}

        productIds:
        {ids}
        """
        idsJson = json.loads(idsJson)
        for product in products:
            artikelnummer = product["Artikelnummer"].encode('ascii', 'ignore').decode('ascii')
            bezeichnung = product["Bezeichnung"].encode('ascii', 'ignore').decode('ascii')
            beschreibung = product["Beschreibung"].encode('ascii', 'ignore').decode('ascii')
            countp = len(list(filter(lambda x: str(x) == str(artikelnummer), idsJson)))
            body += f"""
({artikelnummer}){bezeichnung} ---- {countp}
{beschreibung}

            """
        # body = body.replace("\n", "<br>")
        if(send_email(sender, pw, receiver, subject, body)):
            msg = {
                'status': 200,
                'message': 'mail was sent successfully',
            }
            respone = jsonify(msg)
            respone.status_code = 200
            return respone
        else:
            msg = {
                'status': 200,
                'message': 'mail sent had error',
            }
            respone = jsonify(msg)
            respone.status_code = 200
            return respone

    except Exception as e:
        print(e)


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Record not found: ' + request.url,
    }
    respone = jsonify(message)
    respone.status_code = 404
    return respone


def send_email(user, pwd, recipient, subject, body):
    import smtplib

    FROM = user
    TO = recipient if isinstance(recipient, list) else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('successfully sent the mail')
        return True
    except Exception as e:
        print("failed to send mail")
        print(e)

    return False


if __name__ == "__main__":
    app.run(debug=True)
