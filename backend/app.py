from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking
app.config['SECRET_KEY'] = 'supersecretkey'  # Secret key for session management

# Initialize extensions
db = SQLAlchemy(app)  # Database ORM
bcrypt = Bcrypt(app)  # Password hashing

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year_published = db.Column(db.Integer, nullable=False)
    loan_type = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    actual_return_date = db.Column(db.DateTime, nullable=True)

class LateLoan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    late_days = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Helper function to get return date based on loan type
def get_return_date(loan_type):
    if loan_type == 1:
        return datetime.utcnow() + timedelta(days=10)
    elif loan_type == 2:
        return datetime.utcnow() + timedelta(days=5)
    elif loan_type == 3:
        return datetime.utcnow() + timedelta(days=2)
    elif loan_type == 4:
        return datetime.utcnow() + timedelta(minutes=5)

# Helper function to serialize User objects
def user_to_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'loans': [loan_to_dict(loan) for loan in user.loans]
    }

# Helper function to serialize Book objects
def book_to_dict(book):
    return {
        'id': book.id,
        'name': book.name,
        'author': book.author,
        'year_published': book.year_published,
        'loan_type': book.loan_type,
        'status': book.status
    }

# Helper function to serialize Loan objects
def loan_to_dict(loan):
    return {
        'id': loan.id,
        'book_id': loan.book_id,
        'user_id': loan.user_id,
        'loan_date': loan.loan_date.isoformat(),
        'return_date': loan.return_date.isoformat() if loan.return_date else None,
        'actual_return_date': loan.actual_return_date.isoformat() if loan.actual_return_date else None
    }

@app.route('/')
def hello():
    return 'Let the library testing begin!!!!!'

# Route for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password, role=data['role'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(user_to_dict(new_user))

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({"message": "Logged in successfully", "role": user.role})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Route for user logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return jsonify({"message": "Logged out successfully"})

# Route for admin to add a user
@app.route('/add_user', methods=['POST'])
def add_user():
    if 'role' in session and session['role'] == 'admin':
        data = request.get_json()
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], password=hashed_password, role=data['role'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify(user_to_dict(new_user))
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for admin to add a book
@app.route('/add_book', methods=['POST'])
def add_book():
    if 'role' in session and session['role'] == 'admin':
        data = request.get_json()
        new_book = Book(name=data['name'], author=data['author'], year_published=data['year_published'], loan_type=data['loan_type'])
        db.session.add(new_book)
        db.session.commit()
        return jsonify(book_to_dict(new_book))
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route to get all books
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([book_to_dict(book) for book in books])

# Route for admin to get all customers
@app.route('/customers', methods=['GET'])
def get_customers():
    if 'role' in session and session['role'] == 'admin':
        users = User.query.all()
        return jsonify([user_to_dict(user) for user in users])
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for customer to loan a book
@app.route('/loan_book', methods=['POST'])
def loan_book():
    if 'role' in session and session['role'] == 'customer':
        data = request.get_json()
        book = Book.query.get(data['book_id']) #isnt that shuold be "id" and not "book_id"?
        if book and book.status == 'available':
            return_date = get_return_date(book.loan_type)
            new_loan = Loan(book_id=book.id, user_id=session['user_id'], return_date=return_date)
            book.status = 'loaned'
            db.session.add(new_loan)
            db.session.commit()
            return jsonify(loan_to_dict(new_loan))
        else:
            return jsonify({"message": "Book not available"}), 400
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for customer to return a book
@app.route('/return_book', methods=['POST'])
def return_book():
    if 'role' in session and session['role'] == 'customer':
        data = request.get_json()
        loan = Loan.query.filter_by(book_id=data['book_id'], user_id=session['user_id'], actual_return_date=None).first()
        if loan:
            loan.actual_return_date = datetime.utcnow()
            book = Book.query.get(loan.book_id)
            book.status = 'available'
            db.session.commit()
            return jsonify(loan_to_dict(loan))
        else:
            return jsonify({"message": "Loan not found"}), 404
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for admin to get all loans
@app.route('/loans', methods=['GET'])
def get_loans():
    if 'role' in session and session['role'] == 'admin':
        loans = Loan.query.all()
        return jsonify([loan_to_dict(loan) for loan in loans])
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for admin to get late loans
@app.route('/late_loans', methods=['GET'])
def get_late_loans():
    if 'role' in session and session['role'] == 'admin':
        loans = Loan.query.filter(Loan.return_date < datetime.utcnow(), Loan.actual_return_date == None).all()
        return jsonify([loan_to_dict(loan) for loan in loans])
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for admin to delete a customer
@app.route('/delete_customer/<int:id>', methods=['DELETE'])
def delete_customer(id):
    if 'role' in session and session['role'] == 'admin':
        user = User.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify(user_to_dict(user))
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for admin to update a customer
@app.route('/update_customer/<int:id>', methods=['PUT'])
def update_customer(id):
    if 'role' in session and session['role'] == 'admin':
        user = User.query.get(id)
        if user:
            data = request.get_json()
            user.username = data.get('username', user.username)
            if 'password' in data:
                user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
            user.role = data.get('role', user.role)
            db.session.commit()
            return jsonify(user_to_dict(user))
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for admin to delete a book
@app.route('/delete_book/<int:id>', methods=['DELETE'])
def delete_book(id):
    if 'role' in session and session['role'] == 'admin':
        book = Book.query.get(id)
        if book:
            db.session.delete(book)
            db.session.commit()
            return jsonify(book_to_dict(book))
        else:
            return jsonify({"message": "Book not found"}), 404
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Route for admin to update a book
@app.route('/update_book/<int:id>', methods=['PUT'])
def update_book(id):
    if 'role' in session and session['role'] == 'admin':
        book = Book.query.get(id)
        if book:
            data = request.get_json()
            book.name = data.get('name', book.name)
            book.author = data.get('author', book.author)
            book.year_published = data.get('year_published', book.year_published)
            book.loan_type = data.get('loan_type', book.loan_type)
            db.session.commit()
            return jsonify(book_to_dict(book))
        else:
            return jsonify({"message": "Book not found"}), 404
    else:
        return jsonify({"message": "Unauthorized"}), 403

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)