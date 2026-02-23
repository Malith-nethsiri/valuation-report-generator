# Barrel re-exports — zero caller changes required.
# All names that were previously in crud.py are available here.

from .building_helpers import (
    verify_ownership,
    validate_report_buildings,
    _normalize_and_validate_buildings,
    _duplicate_entity_data,
)

from .user_crud import (
    create_user,
    get_user,
    get_user_by_email,
    update_user,
    add_bank_account,
    update_bank_account,
    delete_bank_account,
    get_bank_accounts,
)

from .report_crud import (
    create_report,
    get_report,
    get_user_reports,
    get_user_reports_filtered,
    get_adjacent_report_date,
    get_all_reports,
    update_report,
    delete_report,
    get_report_properties,
    duplicate_report,
)

from .property_crud import (
    create_property,
    get_property,
    get_user_properties,
    get_property_templates,
    update_property,
    delete_property,
    update_property_status,
    duplicate_property,
    get_report_completed_properties,
    create_report_property,
    add_property_to_report,
    remove_property_from_report,
    reorder_report_properties,
    create_multi_property_report,
)

from .vehicle_crud import (
    create_vehicle,
    get_vehicle,
    get_user_vehicles,
    get_vehicle_templates,
    update_vehicle,
    delete_vehicle,
    duplicate_vehicle,
    add_vehicle_to_report,
    remove_vehicle_from_report,
    reorder_report_vehicles,
    get_report_vehicles,
)

__all__ = [
    # building helpers
    "verify_ownership", "validate_report_buildings",
    "_normalize_and_validate_buildings", "_duplicate_entity_data",
    # user
    "create_user", "get_user", "get_user_by_email", "update_user",
    "add_bank_account", "update_bank_account", "delete_bank_account", "get_bank_accounts",
    # report
    "create_report", "get_report", "get_user_reports", "get_user_reports_filtered",
    "get_adjacent_report_date", "get_all_reports", "update_report", "delete_report",
    "get_report_properties", "duplicate_report",
    # property
    "create_property", "get_property", "get_user_properties", "get_property_templates",
    "update_property", "delete_property", "update_property_status", "duplicate_property",
    "get_report_completed_properties", "create_report_property",
    "add_property_to_report", "remove_property_from_report", "reorder_report_properties",
    "create_multi_property_report",
    # vehicle
    "create_vehicle", "get_vehicle", "get_user_vehicles", "get_vehicle_templates",
    "update_vehicle", "delete_vehicle", "duplicate_vehicle",
    "add_vehicle_to_report", "remove_vehicle_from_report",
    "reorder_report_vehicles", "get_report_vehicles",
]
