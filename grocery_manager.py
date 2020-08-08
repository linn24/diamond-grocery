#!/usr/bin/env python3
#
# grocery transaction manager

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from flask import session as login_session
from models import Base, User, Category, Product, Customer, Cart, Order, OrderStatus, OrderItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from decouple import config
from functools import wraps
import random
import string

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

db_url = ''
try:
    db_url = os.environ['DATABASE_URL']
except KeyError as e:
    db_url = config('DATABASE_URL')

engine = create_engine(db_url)
Base.metadata.bind = create_engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.errorhandler(404)
def pageNotFound(e):
    return render_template('page_not_found.html'), 404

def login_required(f):
    """
    method/class name: check whether user has logged in
    Args:
        no argument
    Returns:
        proceed to requested page if already logged in
        redirect to login page if not logged in yet
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


def getUser(email, password):
    """
    method/class name: retrieve user using email address and verify password
    Args:
        email address and password
    Returns:
        return user
    """
    try:
        user = session.query(User).filter_by(email=email).one_or_none()
        if user.validate_password(password):
            return user
        else:
            return None
    except Exception:
        return None

@app.route('/login', methods=['GET', 'POST'])
def userLogin():
    """
    method/class name:
        GET -> generate a random string and store as STATE in session
        POST -> authenticate user's login details
    Args:
        GET -> no argument
        POST -> email, password and STATE
    Returns:
        GET -> redirect to login page
        POST -> redirect to home page if successful; otherwise, login page
    """
    if request.method == 'GET':
        state = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for x in range(32))
        login_session['state'] = state
    else:
        print("state:{}".format(request.form['state']))
        if request.form['state'] != login_session['state']:
            flash("Invalid state parameter")
        else:
            email = request.form['strEmail']
            password = request.form['strPassword']

            user = getUser(email, password)
            if user is None:
                flash("Incorrect email or password")
            else:
                login_session['user_id'] = user.id
                login_session['username'] = user.name
                login_session['picture'] = user.picture
                login_session['email'] = user.email
                return redirect(url_for('showHome'))

    return render_template('login.html', STATE=login_session['state'])

@app.route('/logout')
def userLogout():
    del login_session['user_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    flash('Successfully logged out.')
    return redirect(url_for('userLogin'))

@app.route('/', methods=['GET'])
@login_required
def showHome():
    return render_template('index.html')

@app.route('/category', methods=['GET'])
@login_required
def viewCategories():
    categories = session.query(Category).order_by(Category.id.asc())
    return render_template(
        'categories.html', categories=categories)

@app.route('/product', methods=['GET'])
@login_required
def viewProducts():
    return render_template('index.html')


@app.route('/category/create', methods=['GET', 'POST'])
@login_required
def createCategory():
    """
    method/class name: create a new category with given name
    Args:
        no argument
    Returns:
        redirect to view all categories page after saving
        redirect to create new category page otherwise
    """
    if request.method == 'POST':
        category = Category(
            name=request.form['strCatName'],
            user_id=login_session['user_id'])

        session.add(category)
        session.commit()
        return redirect(url_for('viewCategories'))
    else:
        return render_template('create_category.html')

@app.route('/product/create', methods=['GET'])
@login_required
def createProduct():
    return render_template('index.html')

@app.route('/category/<string:cat_id>', methods=['GET', 'POST'])
@login_required
def editCategory(cat_id):
    """
    method/class name: edit an existing category with given name
    Args:
        no argument
    Returns:
        redirect to view all categories page after saving
        redirect to edit category page otherwise
    """
    category = session.query(Category).filter_by(id=cat_id).one_or_none()

    if request.method == 'POST':
        if request.form['strCatName']:
            category.name = request.form['strCatName']
            category.user_id = login_session['user_id']

        session.add(category)
        session.commit()
        return redirect(url_for('viewCategories'))
    else:
        return render_template('edit_category.html', category=category)

@app.route('/test', methods=['POST'])
def test():
    data = request.get_json(silent=True)
    selected_product = data['selected_product']
    order_quantity = data['order_quantity']

    messages = []
    text = '{} packet(s) of {} has been added to cart.'.format(order_quantity, selected_product)
    messages.append({"text": text})
    output = {
        "messages": messages
        }
    return jsonify(output)

@app.route('/load', methods=['GET'])
def loadProducts():
    products = session.query(Product)
    elements = []
    for product in products:
        element = {
            "title": "{}".format(product.title),
            "image_url": "{}".format(product.image_url),
            "subtitle": "{} ({} {})".format(product.detail, product.weight, product.unit),
            "buttons": [
                {
                    "set_attributes": {
                        "selected_product": "{}".format(product.title),
                        "selected_product_id": product.id,
                    },
                    "block_names": ["Cart"],
                    "type": "show_block",
                    "title": "Add to Cart"
                }
            ]
        }
        elements.append(element)
    output = {
        "messages": [
            {
                "attachment": {
                    "type":"template",
                    "payload":{
                        "template_type":"generic",
                        "image_aspect_ratio": "square",
                        "elements":elements
                    }
                }
            }
        ]
    }
    return jsonify(output)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))   # Use PORT if it's there.
    server_address = ('', port)
    print("server:", server_address)

    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=port)
