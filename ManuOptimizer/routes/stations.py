from flask import Blueprint, request, jsonify
from models import Station, db
import logging

logger = logging.getLogger(__name__)

stations_bp = Blueprint('stations', __name__, url_prefix='/api/stations')

from sqlalchemy.exc import IntegrityError

@stations_bp.route('', methods=['POST'])
def add_station():
    try:
        data = request.json
        name = data.get('name')
        station_id = data.get('station_id')

        if not name or not station_id:
            return jsonify({'error': 'Both name and station_id are required'}), 400

        try:
            station_id = int(station_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid station_id'}), 400

        if Station.query.filter_by(station_id=station_id).first():
            return jsonify({'error': 'Station ID already exists'}), 400

        new_station = Station(name=name, station_id=station_id)
        db.session.add(new_station)
        db.session.commit()

        return jsonify({'message': 'Station added successfully', 'station': {
            'id': new_station.id,
            'name': new_station.name,
            'station_id': new_station.station_id
        }}), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Station ID already exists'}), 400

    except Exception as e:
        db.session.rollback()
        logger.error("Failed to add station", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500



@stations_bp.route('', methods=['GET'])
def list_stations():
    stations = Station.query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'station_id': s.station_id} for s in stations]), 200


@stations_bp.route('/<int:id>', methods=['DELETE'])
def delete_station(id):
    station = Station.query.get(id)
    if not station:
        return jsonify({'error': 'Station not found'}), 404

    try:
        db.session.delete(station)
        db.session.commit()
        return jsonify({'message': 'Station deleted'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to delete station", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@stations_bp.route('/<int:id>', methods=['PUT'])
def edit_station(id):
    data = request.json
    name = data.get('name')
    station_id_val = data.get('station_id')

    station = Station.query.get(id)
    if not station:
        return jsonify({'error': 'Station not found'}), 404

    if not name or not station_id_val:
        return jsonify({'error': 'Name and station_id required'}), 400

    # Check if new station_id is already taken by another station
    if Station.query.filter(Station.station_id == station_id_val, Station.id != id).first():
        return jsonify({'error': 'Station ID already exists for another station'}), 400

    try:
        station.name = name
        station.station_id = station_id_val
        db.session.commit()
        return jsonify({'message': 'Station updated', 'station': {'id': station.id, 'name': station.name, 'station_id': station.station_id}}), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to update station", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
