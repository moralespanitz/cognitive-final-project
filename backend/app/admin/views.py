"""
SQLAdmin views for TaxiWatch models.
"""
from sqladmin import ModelView
from ..models.user import User
from ..models.vehicle import Driver, Vehicle, Trip
from ..models.tracking import GPSLocation
from ..models.device import Device
from ..models.faq import FAQ
from ..models.image import TripImage
from ..models.admin_log import AdminLog, SystemMetric


class UserAdmin(ModelView, model=User):
    """User admin view."""
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.username,
        User.email,
        User.first_name,
        User.last_name,
        User.role,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.username, User.email, User.first_name, User.last_name]
    column_sortable_list = [User.id, User.username, User.email, User.created_at]
    column_default_sort = [(User.id, True)]

    form_excluded_columns = [User.hashed_password]
    can_create = True
    can_edit = True
    can_delete = True


class DriverAdmin(ModelView, model=Driver):
    """Driver admin view."""
    name = "Driver"
    name_plural = "Drivers"
    icon = "fa-solid fa-id-card"

    column_list = [
        Driver.id,
        Driver.user_id,
        Driver.license_number,
        Driver.license_expiry,
        Driver.status,
        Driver.rating,
    ]
    column_searchable_list = [Driver.license_number]
    column_sortable_list = [Driver.id, Driver.license_number, Driver.rating]
    can_create = True
    can_edit = True
    can_delete = True


class VehicleAdmin(ModelView, model=Vehicle):
    """Vehicle admin view."""
    name = "Vehicle"
    name_plural = "Vehicles"
    icon = "fa-solid fa-car"

    column_list = [
        Vehicle.id,
        Vehicle.license_plate,
        Vehicle.make,
        Vehicle.model,
        Vehicle.year,
        Vehicle.vin,
        Vehicle.status,
        Vehicle.current_driver_id,
    ]
    column_searchable_list = [Vehicle.license_plate, Vehicle.make, Vehicle.model, Vehicle.vin]
    column_sortable_list = [Vehicle.id, Vehicle.license_plate, Vehicle.year]
    column_default_sort = [(Vehicle.id, True)]
    can_create = True
    can_edit = True
    can_delete = True


class TripAdmin(ModelView, model=Trip):
    """Trip admin view."""
    name = "Trip"
    name_plural = "Trips"
    icon = "fa-solid fa-route"

    column_list = [
        Trip.id,
        Trip.customer_id,
        Trip.driver_id,
        Trip.vehicle_id,
        Trip.status,
        Trip.estimated_fare,
        Trip.fare,
        Trip.distance,
        Trip.created_at,
    ]
    column_searchable_list = []
    column_sortable_list = [Trip.id, Trip.created_at, Trip.fare]
    column_default_sort = [(Trip.created_at, False)]
    can_create = True
    can_edit = True
    can_delete = False


class GPSLocationAdmin(ModelView, model=GPSLocation):
    """GPS Location admin view."""
    name = "GPS Location"
    name_plural = "GPS Locations"
    icon = "fa-solid fa-location-dot"

    column_list = [
        GPSLocation.id,
        GPSLocation.vehicle_id,
        GPSLocation.device_id,
        GPSLocation.latitude,
        GPSLocation.longitude,
        GPSLocation.speed,
        GPSLocation.timestamp,
    ]
    column_sortable_list = [GPSLocation.id, GPSLocation.timestamp]
    column_default_sort = [(GPSLocation.timestamp, False)]
    can_create = False
    can_edit = False
    can_delete = True


class DeviceAdmin(ModelView, model=Device):
    """Device admin view."""
    name = "Device"
    name_plural = "Devices"
    icon = "fa-solid fa-microchip"

    column_list = [
        Device.id,
        Device.serial_number,
        Device.vehicle_id,
        Device.device_type,
        Device.status,
        Device.model,
        Device.manufacturer,
        Device.last_ping,
    ]
    column_searchable_list = [Device.serial_number, Device.model, Device.manufacturer]
    column_sortable_list = [Device.id, Device.last_ping, Device.serial_number]
    column_default_sort = [(Device.id, True)]
    can_create = True
    can_edit = True
    can_delete = True


class FAQAdmin(ModelView, model=FAQ):
    """FAQ admin view."""
    name = "FAQ"
    name_plural = "FAQs"
    icon = "fa-solid fa-circle-question"

    column_list = [
        FAQ.id,
        FAQ.question,
        FAQ.category,
        FAQ.priority,
        FAQ.is_active,
    ]
    column_searchable_list = [FAQ.question, FAQ.answer, FAQ.keywords]
    column_sortable_list = [FAQ.id, FAQ.priority, FAQ.category]
    column_default_sort = [(FAQ.priority, False)]
    can_create = True
    can_edit = True
    can_delete = True


class TripImageAdmin(ModelView, model=TripImage):
    """Trip Image admin view."""
    name = "Trip Image"
    name_plural = "Trip Images"
    icon = "fa-solid fa-image"

    column_list = [
        TripImage.id,
        TripImage.trip_id,
        TripImage.device_id,
        TripImage.captured_at,
    ]
    column_sortable_list = [TripImage.id, TripImage.captured_at, TripImage.trip_id]
    column_default_sort = [(TripImage.captured_at, False)]
    can_create = False
    can_edit = False
    can_delete = True


class AdminLogAdmin(ModelView, model=AdminLog):
    """Admin Log admin view for audit trail."""
    name = "Admin Log"
    name_plural = "Admin Logs"
    icon = "fa-solid fa-list-check"

    column_list = [
        AdminLog.id,
        AdminLog.username,
        AdminLog.action,
        AdminLog.level,
        AdminLog.resource_type,
        AdminLog.resource_id,
        AdminLog.message,
        AdminLog.ip_address,
        AdminLog.endpoint,
        AdminLog.method,
        AdminLog.created_at,
    ]
    column_searchable_list = [AdminLog.username, AdminLog.message, AdminLog.endpoint, AdminLog.ip_address]
    column_sortable_list = [AdminLog.id, AdminLog.created_at, AdminLog.level, AdminLog.action]
    column_default_sort = [(AdminLog.created_at, False)]
    column_filters = [AdminLog.level, AdminLog.action, AdminLog.resource_type, AdminLog.username]

    # Read-only view - logs should not be modified
    can_create = False
    can_edit = False
    can_delete = True  # Allow cleanup of old logs


class SystemMetricAdmin(ModelView, model=SystemMetric):
    """System Metric admin view."""
    name = "System Metric"
    name_plural = "System Metrics"
    icon = "fa-solid fa-chart-line"

    column_list = [
        SystemMetric.id,
        SystemMetric.metric_name,
        SystemMetric.metric_type,
        SystemMetric.value,
        SystemMetric.unit,
        SystemMetric.recorded_at,
    ]
    column_searchable_list = [SystemMetric.metric_name, SystemMetric.metric_type]
    column_sortable_list = [SystemMetric.id, SystemMetric.recorded_at, SystemMetric.metric_name]
    column_default_sort = [(SystemMetric.recorded_at, False)]
    column_filters = [SystemMetric.metric_name, SystemMetric.metric_type]

    # Read-only view
    can_create = False
    can_edit = False
    can_delete = True  # Allow cleanup


def setup_admin(admin):
    """Register all admin views."""
    admin.add_view(UserAdmin)
    admin.add_view(DriverAdmin)
    admin.add_view(VehicleAdmin)
    admin.add_view(TripAdmin)
    admin.add_view(GPSLocationAdmin)
    admin.add_view(DeviceAdmin)
    admin.add_view(FAQAdmin)
    admin.add_view(TripImageAdmin)
    admin.add_view(AdminLogAdmin)
    admin.add_view(SystemMetricAdmin)
