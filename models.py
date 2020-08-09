import sys

from sqlalchemy import Column, ForeignKey, Integer, String, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import os
from decouple import config
from passlib.hash import bcrypt

Base = declarative_base()

class User(Base):
    """
    Registered user information
    """
    __tablename__ = 't_user'

    id = Column(Integer, primary_key=True)
    email = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)
    name = Column(String(250), nullable=False)
    picture = Column(String(250))

    def __init__(self, email, password, name, picture):
        self.email = email
        self.password = bcrypt.encrypt(password)
        self.name = name
        self.picture = picture

    def validate_password(self, password):
        return bcrypt.verify(password, self.password)

    def __repr__(self):
        return "<User(email ='%s', password='%s', name='%s')>" % (self.email, self.password, self.name)

class Category(Base):
    """
    Category to group products
    """
    __tablename__ = 't_category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)

    user_id = Column(Integer, ForeignKey('t_user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
        }

class Product(Base):
    """
    Product information
    """
    __tablename__ = 't_product'

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    detail = Column(String(2000), nullable=False)
    brand = Column(String(500))
    price = Column(Numeric(), nullable=False)
    image_url = Column(String(1000))
    size = Column(Numeric())
    weight = Column(Numeric())
    unit = Column(String(100))
    last_updated_date = Column(Date, nullable=False)

    cat_id = Column(
                Integer, ForeignKey(
                    't_category.id', ondelete='CASCADE'), nullable=False)
    category = relationship(Category)

    user_id = Column(Integer, ForeignKey('t_user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'detail': self.detail,
            'brand': self.brand,
            'price': self.price,
            'image_url': self.image_url,
            'size': self.size,
            'weight': self.weight,
            'unit': self.unit,
            'last_updated_date': self.last_updated_date,
            'cat_id': self.cat_id,
            'user_id': self.user_id,
        }

class Customer(Base):
    """
    Customer information
    """
    __tablename__ = 't_customer'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False, unique=True)
    phone = Column(String(250))
    address = Column(String(2500), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
        }

class Cart(Base):
    """
    Customer's Cart
    """
    __tablename__ = 't_cart'
    id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    added_date = Column(Date, nullable=False)

    customer_id = Column(Integer, ForeignKey('t_customer.id'))
    customer = relationship(Customer)

    product_id = Column(Integer, ForeignKey('t_product.id'))
    product = relationship(Product)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'quantity': self.quantity,
            'added_date': self.added_date,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
        }

class OrderStatus(Base):
    """
    Status of each order
    """
    __tablename__ = 't_orderstatus'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }

class Order(Base):
    """
    Customer's Order
    """
    __tablename__ = 't_order'
    id = Column(Integer, primary_key=True)
    ref_number = Column(String(100), nullable=False)
    purchased_date = Column(Date, nullable=False)
    completed_date = Column(Date)
    total_amount = Column(Numeric(), nullable=False)


    customer_id = Column(Integer, ForeignKey('t_customer.id'))
    customer = relationship(Customer)

    status_id = Column(Integer, ForeignKey('t_orderstatus.id'))
    status = relationship(OrderStatus)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'ref_number': self.ref_number,
            'purchased_date': self.purchased_date,
            'completed_date': self.completed_date,
            'customer_id': self.customer_id,
            'status_id': self.status_id,
            'total_amount': self.total_amount,
        }

class OrderItem(Base):
    """
    Item included in each order
    """
    __tablename__ = 't_orderitem'
    id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(), nullable=False)

    product_id = Column(Integer, ForeignKey('t_product.id'))
    product = relationship(Product)

    order_id = Column(Integer, ForeignKey('t_order.id'))
    order = relationship(Order)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'quantity': self.quantity,
            'total_amount': self.total_amount,
            'product_id': self.product_id,
            'order_id': self.order_id,
        }

db_url = ''
try:
    db_url = os.environ['DATABASE_URL']
except KeyError as e:
    db_url = config('DATABASE_URL')

engine = create_engine(db_url)
Base.metadata.create_all(engine)
