import sys

from sqlalchemy import Column, ForeignKey, Integer, String, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

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
    created_date = Column(Date, nullable=False)

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
            'created_date': self.created_date,
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

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
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

class PurchaseHistory(Base):
    """
    Customer's Purchase History
    """
    __tablename__ = 't_purchasehistory'
    id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    purchased_date = Column(Date, nullable=False)

    customer_id = Column(Integer, ForeignKey('t_customer.id'))
    customer = relationship(Customer)

    product_id = Column(Integer, ForeignKey('t_product.id'))
    product = relationship(Product)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'quantity': self.quantity,
            'purchased_date': self.purchased_date,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
        }

engine = create_engine('postgres://utjmysjpzohqng:5b243341bd509414fc273bd3e46822f4f3d6dcb19533e007cd77b0b78810efbf@ec2-35-173-94-156.compute-1.amazonaws.com:5432/df9gvh2e5qpm0l')
Base.metadata.create_all(engine)
