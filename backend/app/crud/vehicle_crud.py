"""
Vehicle CRUD operations and report-vehicle junction operations.
"""
from sqlalchemy.orm import Session
from typing import Optional

from .. import models, schemas
from ..base_crud import BaseCRUD
from .report_crud import get_report

_base_vehicle_crud = BaseCRUD(models.Vehicle, "Vehicle")


def create_vehicle(db: Session, vehicle: schemas.VehicleCreate, user_id: int):
    """Create a new vehicle for a user"""
    return _base_vehicle_crud.create(db, vehicle.model_dump(), user_id)


def get_vehicle(db: Session, vehicle_id: int, user_id: int = None):
    """Get vehicle by ID, optionally filtered by user_id"""
    query = db.query(models.Vehicle).filter(
        models.Vehicle.id == vehicle_id,
        models.Vehicle.is_deleted == False
    )
    if user_id:
        query = query.filter(models.Vehicle.user_id == user_id)
    return query.first()


def get_user_vehicles(db: Session, user_id: int, skip: int = 0, limit: int = 100,
                      include_deleted: bool = False):
    """Get all vehicles for a specific user"""
    query = db.query(models.Vehicle).filter(models.Vehicle.user_id == user_id)
    if not include_deleted:
        query = query.filter(models.Vehicle.is_deleted == False)
    return query.order_by(models.Vehicle.created_at.desc()).offset(skip).limit(limit).all()


def get_vehicle_templates(db: Session, user_id: int):
    """Get all vehicle templates (Vehicle Library) for a user"""
    return db.query(models.Vehicle).filter(
        models.Vehicle.user_id == user_id,
        models.Vehicle.is_template == True,
        models.Vehicle.is_deleted == False
    ).order_by(models.Vehicle.make, models.Vehicle.model).all()


def update_vehicle(db: Session, vehicle_id: int, vehicle_update: schemas.VehicleUpdate,
                   user_id: int = None):
    """Update a vehicle"""
    query = db.query(models.Vehicle).filter(
        models.Vehicle.id == vehicle_id,
        models.Vehicle.is_deleted == False
    )
    if user_id:
        query = query.filter(models.Vehicle.user_id == user_id)

    db_vehicle = query.first()
    if not db_vehicle:
        return None

    update_data = vehicle_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)

    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def delete_vehicle(db: Session, vehicle_id: int, user_id: int = None, soft_delete: bool = True):
    """Delete a vehicle (soft delete by default)"""
    query = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id)
    if user_id:
        query = query.filter(models.Vehicle.user_id == user_id)

    db_vehicle = query.first()
    if not db_vehicle:
        return False

    usage_count = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.vehicle_id == vehicle_id
    ).count()

    if usage_count > 0 and not soft_delete:
        raise ValueError(
            f"Cannot permanently delete vehicle. It is used in {usage_count} report(s). "
            "Use soft delete instead."
        )

    if soft_delete:
        db_vehicle.is_deleted = True
        db.commit()
    else:
        db.delete(db_vehicle)
        db.commit()

    return True


def duplicate_vehicle(db: Session, vehicle_id: int, user_id: int):
    """Duplicate a vehicle (create a copy)"""
    original = get_vehicle(db, vehicle_id, user_id)
    if not original:
        return None

    vehicle_data = {
        'status': 'draft',
        'vehicle_type': original.vehicle_type,
        'is_template': False,
        'registration_number': original.registration_number,
        'provincial_council': original.provincial_council,
        'class_of_vehicle': original.class_of_vehicle,
        'body_colour': original.body_colour,
        'chassis_number': original.chassis_number,
        'engine_number': original.engine_number,
        'vehicle_status': original.vehicle_status,
        'country_of_origin': original.country_of_origin,
        'make': original.make,
        'model': original.model,
        'date_of_first_registration': original.date_of_first_registration,
        'year_of_manufacture': original.year_of_manufacture,
        'cylinder_capacity': original.cylinder_capacity,
        'fuel_type': original.fuel_type,
        'mileage': original.mileage,
        'mileage_unit': original.mileage_unit,
        'engine_type': original.engine_type,
        'transmission': original.transmission,
        'wheel_drive': original.wheel_drive,
        'running_condition': original.running_condition,
        'clutch_status': original.clutch_status,
        'engine_condition': original.engine_condition,
        'gear_box_condition': original.gear_box_condition,
        'differential_status': original.differential_status,
        'gear_selection': original.gear_selection,
        'body_condition': original.body_condition,
        'chassis_condition': original.chassis_condition,
        'upholstery_condition': original.upholstery_condition,
        'underside_condition': original.underside_condition,
        'body_parts_status': original.body_parts_status,
        'engine_parts_status': original.engine_parts_status,
        'accessories_status': original.accessories_status,
        'fuel_consumption': original.fuel_consumption,
        'fuel_consumption_unit': original.fuel_consumption_unit,
        'foot_brake_condition': original.foot_brake_condition,
        'disc_brake_available': original.disc_brake_available,
        'parking_brake_condition': original.parking_brake_condition,
        'abs_available': original.abs_available,
        'features': original.features,
        'suspension': original.suspension,
        'tyres': original.tyres,
        'electrical': original.electrical,
        'lights': original.lights,
        'has_accidents': original.has_accidents,
        'has_repairs': original.has_repairs,
        'needs_repairs_within_year': original.needs_repairs_within_year,
        'body_parts_replaced': original.body_parts_replaced,
        'purchase_price': original.purchase_price,
        'brand_new_price': original.brand_new_price,
        'market_value': original.market_value,
        'forced_sale_value': original.forced_sale_value,
        'valuation_summary': original.valuation_summary,
        'office_data': original.office_data,
        'past_valuations': original.past_valuations,
        'vehicle_photos': original.vehicle_photos,
        'book_images': original.book_images,
        'original_vehicle_id': original.id,
    }

    new_vehicle = models.Vehicle(**vehicle_data, user_id=user_id)
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle


def add_vehicle_to_report(db: Session, report_id: int, vehicle_id: int,
                          user_id: int, vehicle_order: int = None):
    """Add an existing vehicle to a report"""
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    db_vehicle = get_vehicle(db, vehicle_id, user_id)
    if not db_vehicle:
        raise ValueError("Vehicle not found or access denied")

    existing = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id,
        models.ReportVehicle.vehicle_id == vehicle_id
    ).first()
    if existing:
        raise ValueError("Vehicle is already in this report")

    if vehicle_order is None:
        max_order = db.query(models.ReportVehicle).filter(
            models.ReportVehicle.report_id == report_id
        ).count()
        vehicle_order = max_order + 1

    report_vehicle = models.ReportVehicle(
        report_id=report_id,
        vehicle_id=vehicle_id,
        vehicle_order=vehicle_order
    )
    db.add(report_vehicle)
    db.flush()

    new_count = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id
    ).count()
    db_report.vehicle_count = new_count

    _update_report_total_valuation_with_vehicles(db, db_report)

    db.commit()
    db.refresh(report_vehicle)
    return report_vehicle


def remove_vehicle_from_report(db: Session, report_id: int, vehicle_id: int, user_id: int):
    """Remove a vehicle from a report"""
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    report_vehicle = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id,
        models.ReportVehicle.vehicle_id == vehicle_id
    ).first()

    if not report_vehicle:
        raise ValueError("Vehicle is not in this report")

    db.delete(report_vehicle)
    db.flush()

    new_count = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id
    ).count()
    db_report.vehicle_count = new_count

    _update_report_total_valuation_with_vehicles(db, db_report)

    db.commit()
    return True


def reorder_report_vehicles(db: Session, report_id: int, vehicle_order_map: dict, user_id: int):
    """
    Reorder vehicles in a report.
    vehicle_order_map: {vehicle_id: new_order, ...}
    """
    db_report = get_report(db, report_id, user_id)
    if not db_report:
        raise ValueError("Report not found or access denied")

    for vehicle_id, new_order in vehicle_order_map.items():
        report_vehicle = db.query(models.ReportVehicle).filter(
            models.ReportVehicle.report_id == report_id,
            models.ReportVehicle.vehicle_id == vehicle_id
        ).first()

        if report_vehicle:
            report_vehicle.vehicle_order = new_order

    db.commit()
    return True


def get_report_vehicles(db: Session, report_id: int):
    """Get all vehicles for a report, ordered by vehicle_order"""
    return db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == report_id
    ).order_by(models.ReportVehicle.vehicle_order).all()


def _update_report_total_valuation_with_vehicles(db: Session, db_report: models.Report):
    """Recalculate total valuation for a report including both properties and vehicles."""
    total = 0

    report_properties = db.query(models.ReportProperty).filter(
        models.ReportProperty.report_id == db_report.id
    ).all()

    for rp in report_properties:
        if rp.override_market_value is not None:
            total += float(rp.override_market_value)
        else:
            prop = db.query(models.Property).filter(
                models.Property.id == rp.property_id
            ).first()
            if prop and prop.valuation_market_value is not None:
                total += float(prop.valuation_market_value)

    report_vehicles = db.query(models.ReportVehicle).filter(
        models.ReportVehicle.report_id == db_report.id
    ).all()

    for rv in report_vehicles:
        if rv.override_market_value is not None:
            total += float(rv.override_market_value)
        else:
            vehicle = db.query(models.Vehicle).filter(
                models.Vehicle.id == rv.vehicle_id
            ).first()
            if vehicle and vehicle.market_value is not None:
                total += float(vehicle.market_value)

    db_report.total_valuation_amount = total if total > 0 else None
