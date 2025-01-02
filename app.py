from flask import Flask, request, render_template, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, auth,firestore

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "secret"  # For session management

# Initialize Firebase Admin SDK
cred = credentials.Certificate("StayMateKeys.json")
firebase_admin.initialize_app(cred)
db=firestore.client()

@app.route('/')
def home():
    user = session.get('user')
    if user:
        return render_template("home.html", user=user)
    return redirect(url_for("login"))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = auth.get_user_by_email(email)
            session['user'] = email  

            return redirect(url_for("home"))
        except Exception as e:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            auth.create_user(email=email, password=password)
            return redirect(url_for("login"))
        except Exception as e:
            return render_template("signup.html", error="Could not create account")
    return render_template("signup.html")

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

def get_hostels(city=None, state=None, max_fees=None, for_type=None):
    hostels_ref = db.collection("Hostel")
    query = hostels_ref
    if city:
        query = query.where("City", "==", city)
    if state:
        query = query.where("State", "==", state)
    if max_fees:
        query = query.where("Fees", "<=", int(max_fees))
    if for_type:
        query = query.where("For", "==", for_type)
    docs = query.stream()
    hostels = []
    for doc in docs:
        data = doc.to_dict()
        images = [url_for('static', filename=f'/{img}') for img in data.get("Images", [])]
        data["image_urls"] = images
        data["id"] = doc.id
        hostels.append(data)
    return hostels


def get_hostel_by_id(hostel_id):
    doc_ref=db.collection("Hostel").document(hostel_id)
    doc=doc_ref.get()
    if doc.exists:
        # return doc.to_dict()
        data=doc.to_dict()
        images=[url_for('static',filename=f'/{img}') for img in data.get("Images",[])]
        data["image_urls"]=images
        return data
    else:
        return None
    
@app.route('/hostel_list')
def hostel_list():
    city = request.args.get('city')
    state = request.args.get('state')
    max_fees = request.args.get('max_fees')
    for_type = request.args.get('for')
    hostels = get_hostels(city=city, state=state, max_fees=max_fees, for_type=for_type)
    user = session.get('user')
    return render_template("hostels.html", hostels=hostels, user=user)


@app.route('/hostel/<string:hostel_id>')
def hostel_detail(hostel_id):
    hostel=get_hostel_by_id(hostel_id)
    user = session.get('user')
    if not hostel:
        return "Hostel not found",404
    return render_template("hostel_detail.html",hostel=hostel,user=user)

#NEW
@app.route('/interested/<hostel_name>', methods=['POST'])
def mark_interested(hostel_name):
    student_name = request.form['name']
    student_gmail = request.form['gmail']
    interested_ref = db.collection('Hostel').document(hostel_name).collection('Interested')
    interested_ref.document(student_name).set({
        'name': student_name,
        'gmail': student_gmail
    })
    return redirect(url_for('list_interested_students', hostel_name=hostel_name))

@app.route('/hostel/<hostel_name>/interested')
def list_interested_students(hostel_name):
    user = session.get('user')
    interested_ref = db.collection('Hostel').document(hostel_name).collection('Interested')
    students = interested_ref.stream()
    interested_students = [{'name': s.id, 'gmail': s.to_dict().get('gmail')} for s in students]
    return render_template('interested_students.html', students=interested_students, hostel_name=hostel_name,user=user)

@app.route('/book/<hostel_name>', methods=['GET'])
def booking_form(hostel_name):
    user = session.get('user')
    interested_ref = db.collection('Hostel').document(hostel_name).collection('Interested')
    students = interested_ref.stream()
    interested_students = [{'name': s.id, 'gmail': s.to_dict().get('gmail')} for s in students]
    return render_template('booking.html', hostel_name=hostel_name, students=interested_students,user=user)

@app.route('/book/<hostel_name>', methods=['POST'])
def book_hostel(hostel_name):
    student_name = request.form['student_name']
    student_gmail = request.form['student_gmail']
    roommates = request.form.getlist('roommates')
    booking_id = f"{hostel_name}_{student_gmail}"
    db.collection('Hostel').document(hostel_name).collection('Bookings').document(booking_id).set({
        'Hostel Name': hostel_name,
        'Student Details':{'Name':student_name,'Gmail':student_gmail},
        'Roommates':roommates
    })
    return "Booking successful!"


#PG
def get_PGs(city=None, state=None, max_rent=None, for_type=None):
    PGs_ref = db.collection("PG")
    query = PGs_ref
    if city:
        query = query.where("City", "==", city)
    if state:
        query = query.where("State", "==", state)
    if max_rent:
        query = query.where("Rent", "<=", int(max_rent))
    if for_type:
        query = query.where("For", "==", for_type)
    docs = query.stream()
    PGs = []
    for doc in docs:
        data = doc.to_dict()
        images = [url_for('static', filename=f'/{img}') for img in data.get("Images", [])]
        data["image_urls"] = images
        data["id"] = doc.id
        PGs.append(data)
    return PGs

def get_PG_by_id(PG_id):
    doc_ref=db.collection("PG").document(PG_id)
    doc=doc_ref.get()
    if doc.exists:
        data=doc.to_dict()
        images=[url_for('static',filename=f'/{img}') for img in data.get("Images",[])]
        data["image_urls"]=images
        return data
    else:
        return None
    
@app.route('/PG_list')
def PG_list():
    city = request.args.get('city')
    state = request.args.get('state')
    max_rent = request.args.get('max_rent')
    for_type = request.args.get('for')
    PGs = get_PGs(city=city, state=state, max_rent=max_rent, for_type=for_type)
    user = session.get('user')
    return render_template("PGs.html", PGs=PGs, user=user)

@app.route('/PG/<string:PG_id>')
def PG_detail(PG_id):
    PG=get_PG_by_id(PG_id)
    user = session.get('user')
    if not PG:
        return "PG not found",404
    return render_template("PG_detail.html",PG=PG,user=user)

#Interested in PG
@app.route('/interested_PG/<PG_name>', methods=['POST'])
def mark_interested_PG(PG_name):
    student_name = request.form['name']
    student_gmail = request.form['gmail']
    interested_ref = db.collection('PG').document(PG_name).collection('Interested')
    interested_ref.document(student_name).set({
        'name': student_name,
        'gmail': student_gmail
    })
    return redirect(url_for('list_interested_students_PG', PG_name=PG_name))

@app.route('/PG/<PG_name>/interested_PG')
def list_interested_students_PG(PG_name):
    user = session.get('user')
    interested_ref = db.collection('PG').document(PG_name).collection('Interested')
    students = interested_ref.stream()
    interested_students = [{'name': s.id, 'gmail': s.to_dict().get('gmail')} for s in students]
    return render_template('interested_students_PG.html', students=interested_students, PG_name=PG_name,user=user)

@app.route('/book_PG/<PG_name>', methods=['GET'])
def booking_form_PG(PG_name):
    user = session.get('user')
    interested_ref = db.collection('PG').document(PG_name).collection('Interested')
    students = interested_ref.stream()
    interested_students = [{'name': s.id, 'gmail': s.to_dict().get('gmail')} for s in students]
    return render_template('booking_PG.html', PG_name=PG_name, students=interested_students,user=user)

@app.route('/book_PG/<PG_name>', methods=['POST'])
def book_PG(PG_name):
    student_name = request.form['student_name']
    student_gmail = request.form['student_gmail']
    roommates = request.form.getlist('roommates')
    booking_id = f"{PG_name}_{student_gmail}"
    db.collection('PG').document(PG_name).collection('Bookings').document(booking_id).set({
        'PG Name': PG_name,
        'Student Details':{'Name':student_name,'Gmail':student_gmail},
        'Roommates':roommates
    })
    return "Booking successful!"

#Extra
@app.route('/call.html')
def call():
    user = session.get('user')
    return render_template("call.html",user=user)

@app.route('/whatsapp.html')
def whatsapp():
    user = session.get('user')
    return render_template("whatsapp.html",user=user)

@app.route('/gmail.html')
def gmail():
    user = session.get('user')
    return render_template("gmail.html",user=user)

@app.route('/instagram.html')
def instagram():
    user = session.get('user')
    return render_template("instagram.html",user=user)

if __name__ == '__main__':
    app.run(debug=True)

