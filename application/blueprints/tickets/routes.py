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
from application.models.inventory import Inventory

@tickets_bp.route("/", methods=["POST"])
@limiter.limit("5 per minute")
def create_ticket():
    """
    Create a service ticket. No auth; shop supplies customer_id in body.
    Body: {"VIN": str, "service_date": str, "service_desc": str, "customer_id": int}.
    """
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
    cache.clear()
    return ticket_schema.jsonify(new_ticket), 201

@tickets_bp.route("/", methods=["GET"])
@cache.cached(timeout=60)
def list_tickets():
    tickets = db.session.execute(select(ServiceTicket)).scalars().all()
    return tickets_schema.jsonify(tickets), 200

@tickets_bp.route("/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id: int):
    """
    Get a single ticket by ID. No auth; shop can view any ticket.
    """
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404
    return ticket_schema.jsonify(ticket), 200

@tickets_bp.route("/<int:ticket_id>", methods=["PUT"])
def update_ticket(ticket_id: int):
    """
    Update a ticket by ID. No auth; shop can update any ticket.
    Body: {"VIN": str, "service_date": str, "service_desc": str, "customer_id": int (optional)}.
    """
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    try:
        ticket_data = ticket_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400

    if "customer_id" in ticket_data:
        customer = db.session.get(Customer, ticket_data["customer_id"])
        if not customer:
            return jsonify({"error": "Customer not found."}), 404

    for key, value in ticket_data.items():
        setattr(ticket, key, value)

    db.session.commit()
    cache.clear()
    return ticket_schema.jsonify(ticket), 200

@tickets_bp.route("/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id: int):
    """
    Delete a ticket by ID. No auth; shop can delete any ticket.
    """
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    db.session.delete(ticket)
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Ticket: {ticket_id} deleted successfully."}), 200

# ---- Many-to-Many: Assign / remove mechanics ----

@tickets_bp.route("/<int:ticket_id>/assign-mechanic/<int:mechanic_id>", methods=["PUT"])
def assign_mechanic_to_ticket(ticket_id: int, mechanic_id: int):
    """
    Assign a mechanic to a ticket.

    Path parameters:
    - ticket_id (int, required): Unique service ticket ID.
    - mechanic_id (int, required): Unique mechanic ID.
    """
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
    """
    Remove a mechanic from a ticket.

    Path parameters:
    - ticket_id (int, required): Unique service ticket ID.
    - mechanic_id (int, required): Unique mechanic ID (must be currently assigned).
    """
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
def edit_ticket_mechanics(ticket_id: int):
    """
    Bulk add/remove mechanics on a ticket. No auth; shop can edit any ticket.
    Body: {"add_ids": [int, ...], "remove_ids": [int, ...]}.
    """

    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

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

@tickets_bp.route("/<int:ticket_id>/add-part/<int:part_id>", methods=["PUT"])
def add_part_to_ticket(ticket_id: int, part_id: int):
    """
    Add an inventory part to a ticket. No auth; shop can add parts to any ticket.
    """
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found."}), 404

    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"error": "Part not found."}), 404

    if part in ticket.parts:
        return jsonify({"message": "Part already added to ticket."}), 200

    ticket.parts.append(part)
    db.session.commit()

    return ticket_schema.jsonify(ticket), 200