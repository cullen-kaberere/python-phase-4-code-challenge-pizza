#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


# Route to get all restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():

    rest = []
    for restaurant in Restaurant.query.all():
        restaurant_dict = restaurant.to_dict(only=( "id", "name", "address"))
        rest.append(restaurant_dict)
    response = make_response(rest, 200)
    return response

@app.route("/restaurants/<int:id>", methods=["GET", "DELETE"])
def get_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if not restaurant:
        return make_response(jsonify({"error": "Restaurant not found"}), 404)
    
    if request.method == "GET":
        restaurant_data = restaurant.to_dict(only=("id", "name", "address"))

        restaurant_pizzas = []
        for restpizza in RestaurantPizza.query.filter_by(restaurant_id=id).all():
            pizza = Pizza.query.get(restpizza.pizza_id)
            restaurant_pizzas.append({
                "id": restpizza.id,
                "pizza_id": restpizza.pizza_id,
                "restaurant_id": restpizza.restaurant_id,
                "price": restpizza.price,
                "pizza": {
                    "id": pizza.id,
                    "name": pizza.name,
                    "ingredients": pizza.ingredients,
                }
            })

        restaurant_data["restaurant_pizzas"] = restaurant_pizzas

        return make_response(jsonify(restaurant_data), 200)
    
    if request.method == "DELETE":
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        RestaurantPizza.query.filter_by(restaurant_id=id).delete()
        
        db.session.delete(restaurant)
        db.session.commit()
        return make_response(" ", 204)
    
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = []
    for pizza in Pizza.query.all():
        pizza_dict = pizza.to_dict(only=("id", "name", "ingredients"))
        pizzas.append(pizza_dict)
    response = make_response(pizzas, 200)
    return response

@app.route("/restaurant_pizzas", methods=["POST"])
def post_pizza():
    try:
        data = request.get_json()

        required_inputs = ["price", "pizza_id", "restaurant_id"]
        for input in required_inputs:
            if input not in data:
                return make_response(jsonify({"errors": ["validation errors"]}), 400)

        price = data["price"]
        pizza_id = data["pizza_id"]
        restaurant_id = data["restaurant_id"]

        if not (1 <= price <= 30):
            return make_response(jsonify({"errors": ["validation errors"]}), 400)

        pizza = db.session.get(Pizza, pizza_id)
        restaurant = db.session.get(Restaurant, restaurant_id)

        if not pizza or not restaurant:
            return make_response(jsonify({"errors": ["Pizza or Restaurant not found"]}), 404)

        new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_restaurant_pizza)
        db.session.commit()

        response_data = {
            "id": new_restaurant_pizza.id,
            "price": new_restaurant_pizza.price,
            "pizza_id": pizza.id,
            "restaurant_id": restaurant.id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients,
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address,
            }
        }

        return make_response(jsonify(response_data), 201)

    except Exception as e:
        return make_response(jsonify({"errors": ["validation error"]}), 400)


if __name__ == "__main__":
    app.run(port=5555, debug=True)