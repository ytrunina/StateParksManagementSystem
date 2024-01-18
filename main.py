from flask import Flask, render_template, request, session, redirect, url_for, flash, make_response
from flask_session import Session
from jinja2 import Environment, FileSystemLoader
import mysql.connector, hashlib
import random
import datetime
import qrcode  # QR code generation
import io  # Saves QR as a file
import base64  # Encodes QR as a string
import json
from datetime import datetime as dt  # using for reports
import io
# stuff for report formatting
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=10)
app.secret_key = 'your_secret_key'
Session(app)

env = Environment(loader=FileSystemLoader('templates'))

mydb = mysql.connector.connect(
    host="db-stateparks.c50qqk98cxr9.us-east-1.rds.amazonaws.com",
    user="connectadmin",
    password="EWCfglgz9",
    database="StateParks_TEST"
)


def is_admin(username):
    isItAdmin = False
    try:
        cur = mydb.cursor()
        cur.execute("SELECT isAdmin FROM Users WHERE username = %s", (username,))

        data = cur.fetchone()

        isItAdmin = data[0]

        cur.close()
    except:
        print("An error occurred")
    finally:
        print("finally")
        cur.close()

    if isItAdmin == 1:
        return True
    else:
        return False


@app.route('/')
def landing():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        # If not logged in, redirect to login page
        return redirect(url_for('login'))
    # If logged in, redirect to user's dashboard 
    return render_template('dashboard.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = mydb.cursor()
    cur.execute("SELECT * FROM Users")
    for entry in cur:
        print(entry)

    cur.close()

    if request.method == 'POST':
        uname = request.form.get('username')
        pword = request.form.get('password')

        pword = hashlib.sha256(pword.encode()).hexdigest()

        try:
            print("trying")
            cur = mydb.cursor()
            cur.execute("SELECT id, isAdmin FROM Users WHERE password = %s AND username = %s", (pword, uname))

            data = cur.fetchone()

            session['username'] = uname
            session['id'] = data[0]
            session['admin'] = data[1]

            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(minutes=10)

            cur.close()
            return redirect(url_for('dashboard'))
        except:
            print("excepting")
            session.pop('username', None)
            session.pop('id', None)
            session.pop('admin', None)
            return render_template('login.html', failed=True)
        finally:
            print("finallying")
            cur.close()

    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('id', None)
    session.pop('admin', None)
    return redirect(url_for('landing'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        isAdmin = False
        uname = request.form.get('username')
        pword = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone_num')

        pword = hashlib.sha256(pword.encode()).hexdigest()

        if not uname:
            return render_template('register.html', failed=True)
        elif not pword:
            return render_template('register.html', failed=True)
        else:
            try:
                cur = mydb.cursor()

                # NEED TO PASS FALSE FOR REGULAR USER
                cur.execute("CALL CreateUser (%s, %s, %s, %s, %s, %s, %s)",
                            (uname, pword, first_name, last_name, email, phone, isAdmin))

                mydb.commit()

                flash("User created successfully!")
                return redirect(url_for('login'))
            except Exception as e:
                # if exception, roll back
                mydb.rollback()

                print(e)

                flash("User creation failed!")

                return render_template('register.html', failed=True)
            finally:
                cur.close()
    return render_template('register.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # get the user's details from the database
    cur = mydb.cursor()
    cur.execute("SELECT firstName FROM UserDetails WHERE userID = %s", (session.get('id'),))
    first_name = cur.fetchone()[0]
    cur.execute("SELECT lastName FROM UserDetails WHERE userID = %s", (session.get('id'),))
    last_name = cur.fetchone()[0]
    cur.execute("SELECT email FROM UserDetails WHERE userID = %s", (session.get('id'),))
    email = cur.fetchone()[0]
    cur.execute("SELECT phoneNumber FROM UserDetails WHERE userID = %s", (session.get('id'),))
    phone = cur.fetchone()[0]

    if request.method == 'POST':
        user_id = session.get('id')
        cur.execute("SELECT password FROM Users WHERE id = %s", (session.get('id'),))
        pass0 = cur.fetchone()[0]
        current_pass = request.form.get("regpassword")
        current_pass = hashlib.sha256(current_pass.encode()).hexdigest()
        pass9 = str(pass0)
        pass0fixed = pass9[3:-4]
        if (current_pass == pass0):
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phoneNum = request.form.get('phone_num')
            cur = mydb.cursor()
            cur.execute("UPDATE UserDetails SET firstName = %s WHERE userid = %s", (first_name, user_id))
            cur.execute("UPDATE UserDetails SET lastName = %s WHERE userid = %s", (last_name, user_id))
            cur.execute("UPDATE UserDetails SET email = %s WHERE userid = %s", (email, user_id))
            cur.execute("UPDATE UserDetails SET phoneNumber = %s WHERE userid = %s", (phoneNum, user_id))
            mydb.commit()

            print("Email and/or phone number updated successfully!")
        else:
            print("Could not change information, is the password correct?")
        cur.close()
    return render_template('profile.html', first_name=first_name, last_name=last_name, email=email, phone_num=phone)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == "GET":
        return render_template('changepassword.html')
    elif request.method == "POST":
        failToChange = 0
        cur = mydb.cursor()
        cur.execute("SELECT password FROM Users WHERE id = %s", (session.get('id'),))
        pass0 = cur.fetchall()
        current_pass = request.form.get("currentpass")
        current_pass = hashlib.sha256(current_pass.encode()).hexdigest()
        pass9 = str(pass0)
        pass0fixed = pass9[3:-4]

        pass1 = request.form.get("newpass")
        pass2 = request.form.get("newpass2")
        if (current_pass != pass0fixed):
            msg = "Error: The current password is incorrect"
            failToChange = 1
        if pass1 != pass2:
            msg = "Error: The new passwords must match"
            failToChange = 1
        elif pass0 == pass1:
            msg = "Error: The new password cannot be the same as the old one"
            failToChange = 1
        if failToChange == 0:
            new_pword = hashlib.sha256(pass1.encode()).hexdigest()
            cur = mydb.cursor()
            cur.execute("UPDATE Users SET password = %s WHERE id = %s", (new_pword, session.get('id')))
            mydb.commit()
            msg = "Password changed successfully!"

        return render_template('changepassword.html', message=msg)


@app.route('/check_qr_code', methods=['POST', 'GET'])
def check_qr_code():
    if request.method == "GET":
        # Renders the check_pass.html page that reads the QR code
        return render_template('check_pass.html')
    elif request.method == "POST":
        # Gets the QR code, which is the order item id
        qr_code = request.form['qr_code']

        cur = mydb.cursor()
        # Based on the scanned QR code, get pass details
        cur.execute("""SELECT sp.name, concat(u.firstName, ' ', u.lastName), date(cp.endDate) FROM OrderItems oi
                    JOIN UserDetails u ON oi.userId = u.userID
                    JOIN StateParks sp ON sp.id = oi.stateParkId
                    JOIN CustomerPasses cp ON oi.orderId = cp.orderId AND cp.stateParkId = oi.stateParkId
                    WHERE oi.orderItemId = %s""", (qr_code,))

        result = cur.fetchone()
        print("date qr:", result)

        # Checks pass expiration date
        if (result[2] >= datetime.date.today()):
            message = "%s's Pass %s for %s is valid until %s" % (result[1], qr_code, result[0], result[2])
        else:
            message = "Pass is invalid"
        return render_template('result.html', message=message)


@app.route('/my_parks', methods=['GET', 'POST'])
def my_parks():
    if is_admin(session.get('username')):
        # If the user is an admin, redirect them 
        return render_template("no_permissions_admin.html")
    if request.method == "POST":
        return render_template("my_parks.html")
    elif request.method == "GET":
        try:
            cur = mydb.cursor()
            # Get the park's id and expiration date from user's passes
            cur.execute("SELECT stateParkId, endDate FROM CustomerPasses WHERE userid = %s ORDER BY endDate DESC",
                        (session.get('id'),))
            raw = cur.fetchall()
            parks = []
            from_park = []

            for park in raw:
                temp_park = []  # Create a temporary list for each park

                # Get the park's name, description, url, and address using the park's id
                cur.execute("SELECT Name, description, url, address FROM StateParks WHERE id = %s", (park[0],))
                from_park = cur.fetchall()
                temp_park.append(from_park[0][0])  # Name
                temp_park.append(from_park[0][1])  # Description
                temp_park.append(from_park[0][2])  # URL
                temp_park.append(from_park[0][3])  # Address
                temp_park.append(park[1])  # Date Added

                if (park[1] >= datetime.date.today()):  # If the pass is still valid
                    temp_park.append(True)
                else:
                    temp_park.append(False)

                # Get the order item id for the QR code
                cur.execute(
                    "SELECT orderitemid FROM OrderItems WHERE stateParkId = %s AND userId = %s ORDER BY orderItemId DESC LIMIT 1",
                    (park[0], session.get('id')))

                pass_id_holder = cur.fetchone()[0]
                qr_img = generate_qr_code(pass_id_holder) # Generate the QR Code as a base64 string
                temp_park.append(qr_img) 

                parks.append(temp_park)  # Add the temporary park list to the parks list

            return render_template("my_parks.html", parks=parks) # Render the template with the parks list
        except Exception as e:
            print(e)
        finally:
            cur.close()


def generate_qr_code(integer_value):
    # Uses the qrcode, io, and base64 libraries to generate a QR code as a base64 string
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(integer_value)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}" # Return the base64 string


@app.route('/catalog', methods=['GET', 'POST'])
def catalog():
    if is_admin(session.get('username')):
        # If the user is an admin, redirect them
        return render_template("no_permissions_admin.html")
    if request.method == "POST":
        # If the user has selected parks, redirect them to the checkout page
        selected_parks = request.form.getlist("parks")
        print(selected_parks)
        return redirect(url_for('checkout', parks=selected_parks))

    elif request.method == "GET":
        cur = mydb.cursor()
        # Get all the parks that the user does not have a pass for
        cur.execute("""SELECT id, name, description, url, address, price FROM StateParks sp 
                       WHERE sp.isActive = 1 AND sp.id NOT IN (
                       SELECT stateParkId FROM CustomerPasses 
                       WHERE (endDate > NOW() OR endDate = NOW()) AND userId = %s )""",
                    (session.get('id'),))
        raw_state_parks = cur.fetchall()
        parks = []

        for park in raw_state_parks:
            temp_park = []  
            temp_park.append(park[0])  # ID
            temp_park.append(park[1])  # Name
            temp_park.append(park[2])  # Description
            temp_park.append(park[3])  # URL
            temp_park.append(park[4])  # Address
            temp_park.append(park[5])  # Fee

            parks.append(temp_park)  

        cur.close()

        return render_template("catalog.html", parks=parks)


@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    if is_admin(session.get('username')):
        # If the user is an admin, redirect them
        return render_template("no_permissions_admin.html")
    if request.method == 'GET':
        # Get the park's ids that the user has selected on the catalog page
        parks = request.args.getlist("parks")

        # connect to the database and set up a row factory
        cur = mydb.cursor()
        parkList = ','.join(str(park) for park in parks)
        # Get more information about the parks based on the park's id
        cur.execute(f"SELECT ID, name, description, price FROM StateParks WHERE ID IN ({parkList})")
        RawPark = cur.fetchall()

        temp_quantity = 1                       # At the moment, the user can only select one pass per park
        total_price = 0
        all_parks = []  
        for park in RawPark:
            temp_park = []  
            temp_park.append(park[0])           # ID
            temp_park.append(park[1])           # Name
            temp_park.append(park[2])           # Description
            temp_park.append(park[3])           # Fee
            temp_park.append(temp_quantity)     # Total price
            temp_price = park[3]
            total_price += temp_price * temp_quantity  # Calculate the total price

            all_parks.append(temp_park)  

        return render_template("checkout.html", parks=all_parks, total_price=total_price)
    elif request.method == 'POST':
        print("PURCHASED")
        # Get the park's ids that the user has purchased, as well as the total price
        parks = request.form.getlist('park_ids[]')
        parks_string = ','.join(str(park) for park in parks)
        total_price = request.form.get('total_price', None)
        card_number = request.form.get('cardNum', None)
        cvv = request.form.get('cvv', None)
        expiration_date = request.form.get('cardEx', None)

        # "Payment processing"
        print(parks_string)
        print(total_price)
        print(card_number)
        print(cvv)
        print(expiration_date)

        cur = mydb.cursor()
        cur.execute('CALL CreateOrder(%s, %s, %s)', (total_price, session.get('id'), parks_string))

        return redirect(url_for('dashboard'))


@app.route('/add_admin', methods=['GET', 'POST'])
def add_admin():
    if not is_admin(session.get('username')):
        # If the user is not an admin, redirect them
        return render_template("no_permissions.html")
    if request.method == 'POST':
        # Get data for the new admin
        uname = request.form.get('username')
        pword = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone_num')

        pword = hashlib.sha256(pword.encode()).hexdigest()

        if not uname or not pword:
            return render_template('register.html', failed=True)
        else:
            try:
                cur = mydb.cursor()
                isAdmin = True
                cur.execute("CALL CreateUser (%s, %s, %s, %s, %s, %s, %s)",
                            (uname, pword, first_name, last_name, email, phone, isAdmin))

                mydb.commit()

                flash("Admin created successfully!")
                return redirect(url_for('dashboard'))
            except Exception as e:
                # if exception, roll back
                mydb.rollback()

                print(e)

                flash("User creation failed!")

                return render_template('add_admin.html', failed=True)
            finally:
                cur.close()
    return render_template('add_admin.html')


@app.route('/revenue_reports', methods=['GET'])
def revenue_reports():
    if not is_admin(session.get('username')):
        return render_template("no_permissions.html")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date and end_date:
        start_date = dt.strptime(start_date, '%Y-%m-%d')
        end_date = dt.strptime(end_date, '%Y-%m-%d')

    cur = mydb.cursor()

    cur.execute("""WITH park_revenue AS (
                SELECT p.id, p.name, SUM(oi.itemfee) as total_revenue
                FROM StateParks p
                INNER JOIN OrderItems oi ON p.id = oi.stateParkId
                INNER JOIN Orders o ON oi.orderId = o.orderId
                WHERE (o.orderDate BETWEEN %s AND %s)
                GROUP BY p.id, p.name
                ),
                park_passes AS (
                    SELECT p.id, p.name, COUNT(cp.id) as total_park_passes
                    FROM StateParks p
                    INNER JOIN CustomerPasses cp ON p.id = cp.stateParkId
                    INNER JOIN Orders o ON cp.orderId = o.orderId
                    WHERE (o.orderDate BETWEEN %s AND %s)
                    GROUP BY p.id, p.name
                )
                SELECT pr.name, pr.total_revenue, pp.total_park_passes
                FROM park_revenue pr
                INNER JOIN park_passes pp ON pr.id = pp.id
                ORDER BY pr.name""", (start_date, end_date, start_date, end_date))

    raw_parks_data = cur.fetchall()
    parks = []

    for park_data in raw_parks_data:
        temp_park = {
            'name': park_data[0],
            'total_revenue': park_data[1],
            'total_park_passes': park_data[2]
        }
        parks.append(temp_park)

    total_revenue = sum([park['total_revenue'] for park in parks])

    cur.close()

    return render_template("revenue_reports.html", parks=parks, total_revenue=total_revenue, start_date=start_date,
                           end_date=end_date)


@app.route('/parkpasses_report', methods=['GET'])
def parkpasses_report():
    if not is_admin(session.get('username')):
        return render_template("no_permissions.html")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    park_name = request.args.get('park_name')

    cur = mydb.cursor()

    # Fetch all park names for the dropdown
    cur.execute("SELECT name FROM StateParks")
    park_names = [name[0] for name in cur.fetchall()]

    if start_date and end_date and park_name:
        start_date = dt.strptime(start_date, '%Y-%m-%d')
        end_date = dt.strptime(end_date, '%Y-%m-%d')

        cur.execute("""SELECT concat(u.firstName, ' ', u.lastName), p.name, cp.startDate, cp.endDate
                       FROM CustomerPasses cp
                       INNER JOIN StateParks p ON cp.stateParkId = p.id
                       INNER JOIN UserDetails u ON cp.userId = u.userid
                       WHERE p.name like %s AND cp.startDate >= %s AND cp.startDate <= %s
                    """, (park_name, start_date, end_date))

        raw_pass_data = cur.fetchall()
        passes = []

        for pass_data in raw_pass_data:
            temp_pass = {
                'user_name': pass_data[0],
                'park_name': pass_data[1],
                'start_date': pass_data[2],
                'end_date': pass_data[3]
            }
            passes.append(temp_pass)
    else:
        passes = []

    cur.close()

    return render_template("parkpasses_report.html", park_names=park_names, passes=passes)


@app.route('/downloadpdf')
def downloadpdf():
    if not is_admin(session.get('username')):
        return render_template("no_permissions.html")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    print('end_date', end_date)
    cur = mydb.cursor()
    cur.execute("""WITH park_revenue AS (
                SELECT p.id, p.name, SUM(oi.itemfee) as total_revenue
                FROM StateParks p
                INNER JOIN OrderItems oi ON p.id = oi.stateParkId
                INNER JOIN Orders o ON oi.orderId = o.orderId
                WHERE (o.orderDate BETWEEN %s AND %s)
                GROUP BY p.id, p.name
                ),
                park_passes AS (
                    SELECT p.id, p.name, COUNT(cp.id) as total_park_passes
                    FROM StateParks p
                    INNER JOIN CustomerPasses cp ON p.id = cp.stateParkId
                    INNER JOIN Orders o ON cp.orderId = o.orderId
                    WHERE (o.orderDate BETWEEN %s AND %s)
                    GROUP BY p.id, p.name
                )
                SELECT pr.name, pr.total_revenue, pp.total_park_passes
                FROM park_revenue pr
                INNER JOIN park_passes pp ON pr.id = pp.id
                ORDER BY pr.name""", (start_date, end_date, start_date, end_date))

    # Fetch the results and store them in a list
    results = cur.fetchall()

    # Close the cursor and database connection
    cur.close()

    # Generate a PDF document with the data
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add title to PDF
    elements.append(Paragraph("Park Revenue Report", styles['Title']))

    # Add subtitle to PDF with date range
    elements.append(Paragraph(f"Date Range: {start_date} - {end_date}", styles['Heading2']))

    # Create table data from MySQL results
    table_data = [['Park Name', 'Total Revenue', 'Total Park Passes Purchased']]
    for result in results:
        table_data.append(result)

    # Create table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    # Create table and add it to elements list
    table = Table(table_data)
    table.setStyle(table_style)
    elements.append(table)

    # build PDF document and return
    doc.build(elements)
    pdf = pdf_buffer.getvalue()
    pdf_buffer.close()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=park_data.pdf'
    return response


@app.route('/reports', methods=['GET'])
def reports():
    if not is_admin(session.get('username')):
        return render_template("no_permissions.html")
    else:
        failed = False  # Set to True if access to reports has failed
        return render_template("reports.html", failed=failed)


if __name__ == '__main__':
    app.run()