from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select

from application.extensions import db, limiter, cache
from application.models.service_ticket import ServiceTicket
from application.models.customer import Customer
from application.models.mechanic import Mechanic
from application.utils.util import token_required
from application.blueprints.tickets.schemas import ticket_schema, tickets_schema
from application.blueprints.tickets import tickets_bp

@tickets_bp.route("/", methods=["POST"])
@limiter.limit("5 per minute")
@token_required
def create_ticket(customer_id: int):
    try:
        ticket_data = ticket_schema.load(request.json, partial=("customer_id",))
    except ValidationError as e:
        return jsonify(e.messages), 400

    ticket_data["customer_id"] = customer_id
    customer = db.session.get(Customer, ticket_data["customer_id"])
    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    new_ticket = ServiceTicket(**ticket_data)
    db.session.add(new_ticket)
    db.session.commit()
    cache.clear()
    return ticket_schema.jsonify(new_ticket), 201

@tickets_bp.route("/", methods=["GET"])
@cache.cached(timeout=60)
def list_tickets():
    tickets = db.session.execute(select(ServiceTicket)).scalars().all()
    return tickets_schema.jsonify(tickets), 200

@tickets_bp.route("/<int:ticket_id>", methods=["GET"])
@token_required
def get_ticket(customer_id: int, ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404
    if ticket.customer_id != customer_id:
        return jsonify({"error": "Forbidden."}), 403
    return ticket_schema.jsonify(ticket), 200

@tickets_bp.route("/<int:ticket_id>", methods=["PUT"])
@token_required
def update_ticket(customer_id: int, ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    if ticket.customer_id != customer_id:
        return jsonify({"error": "Forbidden."}), 403

    try:
        ticket_data = ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    ticket_data["customer_id"] = customer_id
    customer = db.session.get(Customer, ticket_data["customer_id"])
    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    for key, value in ticket_data.items():
        setattr(ticket, key, value)

    db.session.commit()
    cache.clear()
    return ticket_schema.jsonify(ticket), 200

@tickets_bp.route("/<int:ticket_id>", methods=["DELETE"])
@token_required
def delete_ticket(customer_id: int, ticket_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    if ticket.customer_id != customer_id:
        return jsonify({"error": "Forbidden."}), 403

    db.session.delete(ticket)
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Ticket: {ticket_id} deleted successfully."}), 200

# ---- Many-to-Many: Assign / remove mechanics ----

@tickets_bp.route("/<int:ticket_id>/assign-mechanic/<int:mechanic_id>", methods=["PUT"])
def assign_mechanic_to_ticket(ticket_id: int, mechanic_id: int):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 404

    if mechanic in ticket.mechanics:
        return jsonify({"message": "Mechanic already assigned.", "ticket_id": ticket.id}), 200

    ticket.mechanics.append(mechanic)
    db.session.commit()
    cache.clear()
    return ticket_schema.jsonify(ticket), 200


@tickets_bp.route("/<int:ticket_id>/remove-mechanic/<int:mechanic_id>", methods=["PUT"])
def remove_mechanic_from_ticket(ticket_id: int, mechanic_id: int):
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
    cache.clear()
    return jsonify({
        "message": "Mechanic removed from ticket.",
        "ticket_id": ticket.id,
        "remaining_mechanic_ids": [m.id for m in ticket.mechanics],
    }), 200

@tickets_bp.route("/<int:ticket_id>/edit", methods=["PUT"])
@token_required
def edit_ticket_mechanics(customer_id: int, ticket_id: int):
    f"""
    Update the many-to-many relationship between ServiceTicket and Mechanic.

    Expects JSON like:
    {
        "add_ids": [1, 2],
        "remove_ids": [3]
    }

    Rules:
    - Only the owner (customer from token) can edit their ticket
    - add_ids: mechanics will be appended if not already assigned
    - remove_ids: mechanics will be removed if currently assigned
    """

    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    if ticket.customer_id != customer_id:
        return jsonify({"error": "Forbidden."}), 403

    payload = request.get_json(silent=True) or {}

    add_ids = payload.get("add_ids", [])
    remove_ids = payload.get("remove_ids", [])

    if not isinstance(add_ids, list) or not isinstance(remove_ids, list):
        return jsonify({"error": "add_ids and remove_ids must be lists."}), 400

    if any(not isinstance(x, int) for x in add_ids + remove_ids):
        return jsonify({"error": "All ids in add_ids/remove_ids must be integers."}), 404


    for mechanic_id in add_ids:
        mechanic = db.session.get(Mechanic, mechanic_id)
        if not mechanic:
            return jsonify({"error": f"Mechanic {mechanic_id} not found."}), 404

        if mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)

    for mechanic_id in remove_ids:
        mechanic = db.session.get(Mechanic, mechanic_id)
        if not mechanic:
            return jsonify({"error": f"Mechanic {mechanic_id} not found."}), 404

        if mechanic not in ticket.mechanics:
            return jsonify({"error": f"Mechanic {mechanic_id} is not assigned to this ticket."}), 400
        
        ticket.mechanics.remove(mechanic)

    db.session.commit()

    cache.clear()

    return jsonify({
        "message": "Ticket mechanics updated successfully.",
        "ticket_id": ticket.id,
        "mechanic_ids": [m.id for m in ticket.mechanics]
    }), 200