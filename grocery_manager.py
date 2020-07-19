#!/usr/bin/env python3
#
# grocery transaction manager

from flask import Flask, request, jsonify
from models import Base, Product, Customer, Cart, PurchaseHistory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

engine = create_engine('postgres://utjmysjpzohqng:5b243341bd509414fc273bd3e46822f4f3d6dcb19533e007cd77b0b78810efbf@ec2-35-173-94-156.compute-1.amazonaws.com:5432/df9gvh2e5qpm0l')
Base.metadata.bind = create_engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


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
