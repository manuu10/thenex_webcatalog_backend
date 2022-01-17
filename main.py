import pymysql
from app import app
from config import mysql
from flask import jsonify
from flask import flash, request

pdf_creation_file_name = "request.pdf"


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
        idsJsonStr = request.args.get("productids", default='[]', type=str)
        ids = idsJsonStr.replace("[", "(")
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

        body = f"""New Request from {lastname},{firstname} (<b>{company}</b>)
        Contact data:
         - <i>{email}</i>
         - <i>{telephone}</i>

        <b>additional Information:</b>
        {additional}

        <b>PartNumbers</b>
        {ids}
        """
        idsJson = json.loads(idsJsonStr)
#         for product in products:
#             artikelnummer = product["Artikelnummer"].encode('ascii', 'ignore').decode('ascii')
#             bezeichnung = product["Bezeichnung"].encode('ascii', 'ignore').decode('ascii')
#             beschreibung = product["Beschreibung"].encode('ascii', 'ignore').decode('ascii')
#             countp = len(list(filter(lambda x: str(x) == str(artikelnummer), idsJson)))
#             body += f"""
# ({artikelnummer}){bezeichnung} ---- {countp}
# {beschreibung}

#             """
        cursor.execute("""INSERT INTO web_catalog_request
           (firstname,lastname,company,email,telephone,additional,products) VALUES(%s,%s,%s,%s,%s,%s,%s)
        """, (firstname, lastname, company, email, telephone, additional, idsJsonStr))
        conn.commit()
        insertedId = cursor.lastrowid
        wcString = str(insertedId)
        wcString = wcString.rjust(6, '0')
        wcString = "WC"+wcString
        subject += "  " + wcString

        create_pdf_file(lastname, firstname, company, email, telephone, additional, idsJson, products, wcString)
        body = body.replace("\n", "<br>")
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
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    from os.path import basename
    import email
    import email.mime.application

    FROM = user
    TO = recipient if isinstance(recipient, list) else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    # message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    # """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM
        msg['To'] = ", ".join(TO)

        # The MIME types for text/html
        HTML_Contents = MIMEText(body, 'html')

        # Adding pptx file attachment
        path_to_pdf = pdf_creation_file_name
        with open(path_to_pdf, "rb") as f:
            # attach = email.mime.application.MIMEApplication(f.read(),_subtype="pdf")
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename=str(path_to_pdf))
            msg.attach(attach)
        msg.attach(HTML_Contents)
        server.sendmail(FROM, TO, msg.as_string())
        server.close()
        print('successfully sent the mail')
        return True
    except Exception as e:
        print("failed to send mail")
        print(e)

    return False


def create_pdf_file(lastname, firstname, company, email, telephone, additional, idsJson, products, wcString):
    import pdfkit

    config = pdfkit.configuration(wkhtmltopdf=r"D:\Tools\wkhtmltox\bin\wkhtmltopdf.exe")
    # imgPath = "file:///D:/Development/thenex_webcatalog/thenex_webcatalog/assets/images/thenex_logo.png"
    imgPath = "https://thenex.com/wp-content/uploads/2015/09/Thenex_Logo_2015_AVADA_350_Transparent.png"
    additional = additional.replace("\n", "<br>")
    s = f"""<!DOCTYPE html>
            <html>
            <head>
            <style>
            *{{
                font-family:'Arial';
            }}
            .img_container{{
               text-align: right;
            }}
            table{{
                border-collapse:collapse;
            }}
            table tr:nth-child(even) td{{
                padding-top:5px;
                padding-bottom:5px;


            }}
            table tr th{{
                text-align:left;
                border-bottom: 2px solid black !important;
            }}
            table tr:nth-child(odd) td{{
                border-bottom:1px solid grey;
            }}
            </style>
            </head>
            <body>
            <div class='img_container'>
            <img src='{imgPath}' height=100>
            </div>
            <p>thenex GmbH - Robert-Bosch-Str. 42 - 46397 Bocholt (Germany)</p>
            <p>
                {company}<br>
                {firstname} {lastname}<br>
                {email}<br>
                Tel. {telephone}
            </p>
            <h2>{wcString}</h2>
            <h3>additional Information:</h3>
            {additional}
            <br><br>
            <table>
            <tr>
            <th>Pos</th>
            <th>PartNo.</th>
            <th>Description</th>
            <th>Qty</th>            
            </tr>
            """
    for index, product in enumerate(products):
        artikelnummer = product["Artikelnummer"].encode('ascii', 'ignore').decode('ascii')
        bezeichnung = product["Bezeichnung"].encode('ascii', 'ignore').decode('ascii')
        beschreibung = product["Beschreibung"].encode('ascii', 'ignore').decode('ascii')
        countp = len(list(filter(lambda x: str(x) == str(artikelnummer), idsJson)))
        s += f"""
        <tr>
            <td>{index}</td>
            <td>{artikelnummer}</td>
            <td></td>
            <td>{countp}</td>
        </tr>
        <tr>
            <td></td>
            <td colspan='2'><b>{bezeichnung}</b><br>{beschreibung}</td>
            <td></td>

        </tr>
            """
    s += "</table>"

    # s = """<h1><strong>Sample PDF file from HTML</strong></h1>
    #     <br></br>
    #     <p>First line...</p>
    #     <p>Second line...</p>
    #     <p>Third line...</p>"""
    pdfkit.from_string(s, output_path=pdf_creation_file_name, configuration=config)


if __name__ == "__main__":
    app.run(debug=True)
