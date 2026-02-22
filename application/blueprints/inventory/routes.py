# application/blueprints/inventory/routes.py
# CRUD enpoints for inventory parts.

from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select

from application.extensions import db
from application.models.inventory import Inventory
from application.schemas.inventory_schema import inventory_schema, inventories_schema
from application.blueprints.inventory import inventory_bp

@inventory_bp.route("/", methods=["POST"])
def create_part():
    """
    Create a new inventory part.
    POST /inventory
    JSON: {"name": "Oil Filter", "price": 12.99}
    """

    try:
        part_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    existing = db.session.execute(
        select(Inventory).where(Inventory.name == part_data["name"])
    ).scalars().first()

    if existing:
        return jsonify({"error": "Part name already exists."}), 400

    new_part = Inventory(**part_data)
    db.session.add(new_part)
    db.session.commit()

    return inventory_schema.jsonify(new_part), 201

@inventory_bp.route("/", methods=["GET"])
def list_parts():
    """
    List all inventory parts.
    GET /inventory
    """
    parts = db.session.execute(select(Inventory)).scalars().all()
    return inventories_schema.jsonify(parts), 200

@inventory_bp.route("/<int:part_id>", methods=["GET"])
def get_part(part_id: int):
    """
    Get a specific inventory part by ID.

    Path parameter:
    - part_id (int, required): Unique inventory part ID.
    """
    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"error": "Part not found."}), 404
    return inventory_schema.jsonify(part), 200

@inventory_bp.route("/<int:part_id>", methods=["PUT"])
def update_part(part_id: int):
    """
    Update a specific inventory part by ID.

    Path parameter:
    - part_id (int, required): Unique inventory part ID.
    Body: {"name": str, "price": float}.
    """
    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"error": "Part not found."}), 404

    try:
        part_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    part.name = part_data["name"]
    part.price = part_data["price"]

    db.session.commit()
    return inventory_schema.jsonify(part), 200

@inventory_bp.route("/<int:part_id>", methods=["DELETE"])
def delete_part(part_id: int):
    """
    Delete a specific inventory part by ID.

    Path parameter:
    - part_id (int, required): Unique inventory part ID.
    """
    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"error": "Part not found."}), 404

    db.session.delete(part)
    db.session.commit()

    return jsonify({"message": "Part deleted successfully."}), 200