from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select

from application.extensions import db
from application.models.service_ticket import ServiceTicket
from application.models.customer import Customer
from application.models.mechanic import Mechanic
from application.schemas.service_ticket_schema import ticket_schema, tickets_schema
from application.schemas.mechanic_schema import mechanics_schema
from application.blueprints.tickets import tickets_bp

@tickets_bp.route("/", methods=["POST"])
def create_ticket():
    try:
        ticket_data = ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    customer = db.session.get(Customer, ticket_data["customer_id"])
    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    new_ticket = ServiceTicket(**ticket_data)
    db.session.add(new_ticket)
    db.session.commit()
    return ticket_schema.jsonify(new_ticket), 201

@tickets_bp.route("/", methods=["GET"])
def list_tickets():
    tickets = db.session.execute(select(ServiceTicket)).scalars().all()
    return tickets_schema.jsonify(tickets), 200

@tickets_bp.route("/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404
    return ticket_schema.jsonify(ticket), 200

@tickets_bp.route("/<int:ticket_id>", methods=["PUT"])
def update_ticket(ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    try:
        ticket_data = ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    customer = db.session.get(Customer, ticket_data["customer_id"])
    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    for key, value in ticket_data.items():
        setattr(ticket, key, value)

    db.session.commit()
    return ticket_schema.jsonify(ticket), 200

@tickets_bp.route("/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": f"Ticket: {ticket_id} deleted successfully."}), 200

# ---- Many-to-Many: Assign mechanics to tickets ----

@tickets_bp.route("/<int:ticket_id>/assign_mechanics", methods=["POST"])
def assign_mechanics_to_ticket(ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    data = request.get_json() or {}
    mechanic_ids = data.get("mechanic_ids")

    if not isinstance(mechanic_ids, list) or not mechanic_ids:
        return jsonify({"error": "Invalid mechanic IDs."}), 400

    mechanics = db.session.execute(
        select(Mechanic).where(Mechanic.id.in_(mechanic_ids))
    ).scalars().all()

    found_ids = {m.id for m in mechanics}
    missing_ids = [mid for mid in mechanic_ids if mid not in found_ids]
    if missing_ids:
        return jsonify({"error": "Some mechanics not found: {missing_ids}"}), 400

    existing_ids = {m.id for m in ticket.mechanics}
    for mech in mechanics:
        if mech.id not in existing_ids:
            ticket.mechanics.append(mech)

    db.session.commit()

    return jsonify({
        "ticket_id": ticket.id,
        "assigned_mechanic_ids": [m.id for m in ticket.mechanics],
    }), 200

@tickets_bp.route("/<int:ticket_id>/mechanics", methods=["GET"])
def list_ticket_mechanics(ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    return mechanics_schema.jsonify(ticket.mechanics), 200

@tickets_bp.route("/<int:ticket_id>/mechanics/<int:mechanic_id>", methods=["DELETE"])
def remove_ticket_mechanic(ticket_id: int, mechanic_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    if mechanic not in ticket.mechanics:
        return jsonify({"error": "Mechanic not assigned to this ticket."}), 400

    ticket.mechanics.remove(mechanic)
    db.session.commit()

    return jsonify({
        "message": "Mechanic removed from ticket.",
        "ticket_id": ticket.id,
        "remaining_mechanic_ids": [m.id for m in ticket.mechanics],
    }), 200