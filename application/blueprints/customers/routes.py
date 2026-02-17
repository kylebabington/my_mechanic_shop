# application/blueprints/customers/routes.py

from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select

from application.extensions import db
from application.models.customer import Customer
from application.models.service_ticket import ServiceTicket
from application.schemas.customer_schema import customer_schema, customers_schema, login_schema
from application.utils.util import encode_token, token_required
from application.blueprints.customers import customers_bp

@customers_bp.route("/", methods=["POST"])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    query = select(Customer).where(Customer.email == customer_data["email"])
    existing_customer = db.session.execute(query).scalars().first()

    if existing_customer:
        return jsonify({"error": "Email already associated with an account."}), 400

    new_customer = Customer(
        name=customer_data["name"],
        email=customer_data["email"],
        phone=customer_data.get("phone"),

        password_hash="TEMP"
    )

    new_customer.set_password(customer_data["password"])

    db.session.add(new_customer)
    db.session.commit()

    return customer_schema.jsonify(new_customer), 201

@customers_bp.route("/login", methods=["POST"])
def login_customer():
    try:
        credentials = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    email = credentials["email"]
    password = credentials["password"]

    query = select(Customer).where(Customer.email == email)
    customer = db.session.execute(query).scalars().first()

    if customer and customer.check_password(password):
        auth_token = encode_token(customer.id)

        return jsonify({
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token
        }), 200

    return jsonify({"message": "Invalid email or password."}), 401

@customers_bp.route("/my-tickets", methods=["GET"])
@token_required
def get_my_tickets(customer_id: int):
    """
    Protected route:
    - requires Authorization: Bearer <token>
    - customer_id comes from token_required decorator
    - returns tickets belonging only to this customer
    """
    query = select(ServiceTicket).where(ServiceTicket.customer_id == customer_id)
    tickets = db.session.execute(query).scalars().all()

    from application.blueprints.tickets.schemas import tickets_schema

    return tickets_schema.jsonify(tickets), 200

@customers_bp.route("/", methods=["GET"])
def get_customers():
    """
    Paginated customer list.

    Query params:
    - limit: how many records to return (default: 10
    - offset: how many records to skip (default: 0)

    Example:
    /customers?limit=10&offset=20
    """
    limit = request.args.get("limit", default=10, type=int)
    offset = request.args.get("offset", default=0, type=int)

    if limit < 1:
        return jsonify({"error": "Limit must be at least 1."}), 400

    if limit > 100:
        return jsonify({"error": "Limit cannot be greater than 100."}), 400

    if offset < 0:
        return jsonify({"error": "Offset cannot be negative."}), 400

    query = select(Customer).limit(limit).offset(offset)
    customers = db.session.execute(query).scalars().all()

    return jsonify({
        "limit": limit,
        "offset": offset,
        "count": len(customers),
        "customers": customers_schema.dump(customers)
    }), 200


@customers_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id: int):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    return customer_schema.jsonify(customer), 200

@customers_bp.route("/me", methods=["PUT"])
@token_required
def update_me(customer_id: int):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    customer.name = customer_data["name"]
    customer.email = customer_data["email"]
    customer.phone = customer_data.get("phone")

    if "password" in customer_data and customer_data["password"]:
        customer.set_password(customer_data["password"])

    db.session.commit()
    return customer_schema.jsonify(customer), 200

@customers_bp.route("/me", methods=["DELETE"])
@token_required
def delete_me(customer_id: int):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    db.session.delete(customer)
    db.session.commit()

    return jsonify({"message": f"Customer: {customer_id} deleted successfully."}), 200