from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select

from application.extensions import db
from application.models.mechanic import Mechanic
from application.blueprints.mechanics.schemas import mechanic_schema, mechanics_schema
from application.blueprints.mechanics import mechanics_bp

@mechanics_bp.route("/", methods=["POST"])
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
        
    query = select(Mechanic).where(Mechanic.email == mechanic_data["email"])
    existing = db.session.execute(query).scalars().first()
    if existing:
        return jsonify({"error": "Email already associated with an account."}), 400

    new_mechanic = Mechanic(**mechanic_data)
    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201

@mechanics_bp.route("/", methods=["GET"])
def list_mechanics():
    mechanics = db.session.execute(select(Mechanic)).scalars().all()
    return mechanics_schema.jsonify(mechanics), 200

@mechanics_bp.route("/<int:mechanic_id>", methods=["GET"])
def get_mechanic(mechanic_id: int):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404
    return mechanic_schema.jsonify(mechanic), 200

@mechanics_bp.route("/most-tickets", methods=["GET"])
def mechanics_by_most_tickets():
    """
    Returns mechanics sorted by how many tickets they have worked on (descending).

    Why this works:
    - mechanic.service_tickets is a relationship list
    - len(mechanic.service_tickets) tells us how many tickets they are attached to
    """
    mechanics = db.session.execute(select(Mechanic)).scalars().all()

    mechanics.sort(key=lambda m: len(m.service_tickets), reverse=True)

    results = []
    for m in mechanics:
        results.append({
            "id":m.id,
            "name":m.name,
            "email":m.email,
            "phone":m.phone,
            "salary":m.salary,
            "tickets_count":len(m.service_tickets),
        })
    
    return jsonify(results), 200

@mechanics_bp.route("/<int:mechanic_id>", methods=["PUT"])
def update_mechanic(mechanic_id: int):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

@mechanics_bp.route("/<int:mechanic_id>", methods=["DELETE"])
def delete_mechanic(mechanic_id: int):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic: {mechanic_id} deleted successfully."}), 200
    