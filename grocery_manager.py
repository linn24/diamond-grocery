#!/usr/bin/env python3
#
# grocery transaction manager

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from flask import session as login_session
from flask_talisman import Talisman
from models import Base, User, Category, Product, Customer, Cart, Order, OrderStatus, OrderItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from decouple import config
from functools import wraps
import random
import string
from datetime import date

app = Flask(__name__)
csp = {
    'default-src': [
        '\'self\'',
        'data:',
        'unsafe-inline'
    ],
    'img-src': [
        '\'self\'',
        'https://source.unsplash.com',
        'https://images.unsplash.com'
    ],
    'style-src-elem': [
        '\'self\'',
        'https://fonts.googleapis.com',
        'unsafe-inline'
    ],
    'style-src': [
        '\'self\'',
        'https://fonts.googleapis.com',
        'unsafe-inline'
    ],
    'font-src': [
        '\'self\'',
        'https://fonts.gstatic.com'
    ]
}
talisman = Talisman(app, content_security_policy=csp)
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
            #flash("You are not allowed to access there")
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
    products = session.query(Product).order_by(Product.id.asc())
    return render_template(
        'products.html', products=products)

@app.route('/customer', methods=['GET'])
@login_required
def viewCustomers():
    customers = session.query(Customer).order_by(Customer.name.asc())
    return render_template(
        'customers.html', customers=customers)

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def searchCart():
    customers = session.query(Customer).order_by(Customer.name.asc())
    products = session.query(Product).order_by(Product.id.asc())
    cart = None
    customer = None
    total_amount = 0
    if request.method == 'POST':
        customer_id = request.form['strCustomer']
        customer = session.query(Customer).filter_by(id=customer_id).one_or_none()
        cart = session.query(Cart).filter_by(customer_id=customer_id).order_by(Cart.added_date.desc())
        for item in cart:
            total_amount += item.product.price * item.quantity
    return render_template(
        'cart.html', customers=customers, products=products, cart=cart, total_amount=total_amount, customer=customer)

@app.route('/order_status', methods=['GET'])
@login_required
def viewOrderStatuses():
    order_statuses = session.query(OrderStatus).order_by(OrderStatus.id.asc())
    return render_template(
        'order_statuses.html', order_statuses=order_statuses)

@app.route('/order', methods=['GET'])
@login_required
def viewOrders():
    orders = session.query(Order).order_by(Order.purchased_date.desc())
    return render_template('orders.html', orders=orders)

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

@app.route('/product/create', methods=['GET', 'POST'])
@login_required
def createProduct():
    """
    method/class name: create a new product with given details
    Args:
        no argument
    Returns:
        redirect to view all products page after saving
        redirect to create new product page otherwise
    """
    if request.method == 'POST':
        product = Product(
            cat_id=request.form['strProductCategory'],
            title=request.form['strProductTitle'],
            detail=request.form['strProductDetail'],
            brand=request.form['strProductBrand'],
            price=request.form['strProductPrice'],
            image_url=request.form['strProductImageUrl'],
            size=None if request.form['strProductSize'] == "" else request.form['strProductSize'],
            weight=None if request.form['strProductWeight'] == "" else request.form['strProductWeight'],
            unit=request.form['strProductUnit'],
            last_updated_date=date.today(),
            user_id=login_session['user_id'])

        session.add(product)
        session.commit()
        return redirect(url_for('viewProducts'))
    else:
        categories = session.query(Category).order_by(Category.id.asc())
        return render_template('create_product.html', categories=categories)

@app.route('/customer/create', methods=['GET', 'POST'])
@login_required
def createCustomer():
    """
    method/class name: create a new customer with given details
    Args:
        no argument
    Returns:
        redirect to view all customers page after saving
        redirect to create new customer page otherwise
    """
    if request.method == 'POST':
        customer = Customer(
            name=request.form['strCustomerName'],
            email=request.form['strCustomerEmail'],
            phone=request.form['strCustomerPhone'],
            address=request.form['strCustomerAddress'])

        session.add(customer)
        session.commit()
        return redirect(url_for('viewCustomers'))
    else:
        return render_template('create_customer.html')

@app.route('/add_to_cart', methods=['POST'])
@login_required
def addToCart():
    customers = session.query(Customer).order_by(Customer.name.asc())
    products = session.query(Product).order_by(Product.id.asc())
    customer_id = request.form['strCustomer']
    product_id = request.form['strProduct']
    quantity = int(request.form['strQuantity'])
    customer = session.query(Customer).filter_by(id=customer_id).one_or_none()
    total_amount = 0


    cart_item = session.query(Cart).filter_by(customer_id=customer_id, product_id=product_id).one_or_none()
    if cart_item is None:
        cart_item = Cart(
            product_id=product_id,
            customer_id=customer_id,
            quantity=quantity,
            added_date=date.today()
        )
    else:
        cart_item.quantity += quantity
        cart_item.added_date = date.today()
    session.add(cart_item)
    session.commit()

    cart = session.query(Cart).filter_by(customer_id=customer_id).order_by(Cart.added_date.desc())
    for item in cart:
        total_amount += item.product.price * item.quantity
    return render_template(
        'cart.html', customers=customers, products=products, cart=cart, total_amount=total_amount, customer=customer)

@app.route('/checkout', methods=['POST'])
@login_required
def checkoutCart():
    customer_id = request.form['strCustomer']
    total_amount = int(request.form['strTotalAmount'])

    cart = session.query(Cart).filter_by(customer_id=customer_id)
    today = date.today()

    order = Order(
        ref_number='ORD-{}{}{}-{}-{}{}'.format(today.year, today.month, today.day, customer_id, total_amount, cart.count()),
        purchased_date=today,
        total_amount=total_amount,
        customer_id=customer_id,
        status_id=1
    )
    session.add(order)
    session.flush()

    for item in cart:
        order_item = OrderItem(
            quantity=item.quantity,
            total_amount=item.product.price * item.quantity,
            product_id=item.product.id,
            order_id=order.id
        )
        session.add(order_item)

    cart.delete()
    session.commit()
    flash("Successfully placed order.")
    return redirect(url_for('viewOrder', order_id=order.id))

@app.route('/order/<string:order_id>', methods=['GET'])
@login_required
def viewOrder(order_id):
    order = session.query(Order).filter_by(id=order_id).one_or_none()
    order_items = session.query(OrderItem).filter_by(order_id=order_id)
    return render_template(
        'view_order.html', order=order, order_items=order_items
    )

@app.route('/order_status/create', methods=['GET', 'POST'])
@login_required
def createOrderStatus():
    """
    method/class name: create a new order status with given name
    Args:
        no argument
    Returns:
        redirect to view all order statuses page after saving
        redirect to create new order status page otherwise
    """
    if request.method == 'POST':
        order_status = OrderStatus(
            name=request.form['strOrderStatusName'])

        session.add(order_status)
        session.commit()
        return redirect(url_for('viewOrderStatuses'))
    else:
        return render_template('create_order_status.html')

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

@app.route('/product/<string:product_id>', methods=['GET', 'POST'])
@login_required
def editProduct(product_id):
    """
    method/class name: edit an existing product with given details
    Args:
        no argument
    Returns:
        redirect to view all products page after saving
        redirect to edit product page otherwise
    """
    product = session.query(Product).filter_by(id=product_id).one_or_none()

    if request.method == 'POST':
        if request.form['strProductCategory']:
            product.cat_id = request.form['strProductCategory']
        if request.form['strProductTitle']:
            product.title = request.form['strProductTitle']
            product.last_updated_date = date.today()
            product.user_id = login_session['user_id']
        if request.form['strProductDetail']:
            product.detail = request.form['strProductDetail']
        if request.form['strProductBrand']:
            product.brand = request.form['strProductBrand']
        if request.form['strProductPrice']:
            product.price = request.form['strProductPrice']
        if request.form['strProductImageUrl']:
            product.image_url = request.form['strProductImageUrl']
        if request.form['strProductSize']:
            product.size = request.form['strProductSize']
        else:
            product.size = None
        if request.form['strProductWeight']:
            product.weight = request.form['strProductWeight']
        else:
            product.weight = None
        if request.form['strProductUnit']:
            product.address = request.form['strProductUnit']

        session.add(product)
        session.commit()
        return redirect(url_for('viewProducts'))
    else:
        categories = session.query(Category).order_by(Category.id.asc())
        return render_template('edit_product.html', product=product, categories=categories)

@app.route('/customer/<string:customer_id>', methods=['GET', 'POST'])
@login_required
def editCustomer(customer_id):
    """
    method/class name: edit an existing customer with given name
    Args:
        no argument
    Returns:
        redirect to view all customers page after saving
        redirect to edit customer page otherwise
    """
    customer = session.query(Customer).filter_by(id=customer_id).one_or_none()

    if request.method == 'POST':
        if request.form['strCustomerName']:
            customer.name = request.form['strCustomerName']
        if request.form['strCustomerEmail']:
            customer.email = request.form['strCustomerEmail']
        if request.form['strCustomerPhone']:
            customer.phone = request.form['strCustomerPhone']
        if request.form['strCustomerAddress']:
            customer.address = request.form['strCustomerAddress']

        session.add(customer)
        session.commit()
        return redirect(url_for('viewCustomers'))
    else:
        return render_template('edit_customer.html', customer=customer)

@app.route('/order_status/<string:order_status_id>', methods=['GET', 'POST'])
@login_required
def editOrderStatus(order_status_id):
    """
    method/class name: edit an existing order status with given name
    Args:
        no argument
    Returns:
        redirect to view all order statuses page after saving
        redirect to edit order status page otherwise
    """
    order_status = session.query(OrderStatus).filter_by(id=order_status_id).one_or_none()

    if request.method == 'POST':
        if request.form['strOrderStatusName']:
            order_status.name = request.form['strOrderStatusName']

        session.add(order_status)
        session.commit()
        return redirect(url_for('viewOrderStatuses'))
    else:
        return render_template('edit_order_status.html', order_status=order_status)

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
