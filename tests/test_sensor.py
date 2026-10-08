import logging
from datetime import timedelta
from typing import Any
from unittest.mock import Mock

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from custom_components.sector.const import RUNTIME_DATA
from custom_components.sector.coordinator import DeviceRegistry
from custom_components.sector.sensor import (
    SectorAlarmSensor,
    SectorReportedAlarmStateSensor,
    async_setup_entry,
)

_DEVICE_COORDINATOR_NAME = "device-coordinator"

@pytest.fixture
def coordinator():
    devices: dict[str, Any] = {
        "serial_no": "SERIAL1",
        "name": "Smoke Detector Entrance",
        "model": "Smoke Detector",
        "entities": {
            "Humidity Sensor": {
                "name": "My Humidity Sensor A",
                "model": "Humidity Sensor",
                "coordinator_name": _DEVICE_COORDINATOR_NAME,
                "sensors": {
                    "humidity": 45,
                },
            },
            "Temperature Sensor": {
                "name": "My Temperature Sensor A",
                "model": "Temperature Sensor",
                "coordinator_name": _DEVICE_COORDINATOR_NAME,
                "sensors": {
                    "temperature": 25,
                },
            },
        },
    }

    device_registry = DeviceRegistry()
    device_registry.register_device(devices)
    coordinator = Mock(spec=DataUpdateCoordinator)
    coordinator.data = {"device_registry": device_registry}
    coordinator.name = _DEVICE_COORDINATOR_NAME
    return coordinator


@pytest.fixture
def entry(coordinator):
    entry = Mock()
    entry.runtime_data = {RUNTIME_DATA.DEVICE_COORDINATORS: [coordinator]}
    return entry


async def test_async_setup_entry_adds_sensors(hass: HomeAssistant, entry, coordinator):
    entities = []

    def async_add_entities(new_entities, update_before_add=False):
        entities.extend(new_entities)

    await async_setup_entry(hass, entry, async_add_entities)

    assert len(entities) == 2

    temp: SectorAlarmSensor = next(
        e for e in entities if e.entity_description.key == "temperature"
    )
    hum: SectorAlarmSensor = next(
        e for e in entities if e.entity_description.key == "humidity"
    )

    assert temp.entity_description.device_class == SensorDeviceClass.TEMPERATURE
    assert (
        temp.entity_description.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    )
    assert temp.unique_id == "SERIAL1_temperature"
    assert temp.native_value == 25

    assert hum.entity_description.device_class == SensorDeviceClass.HUMIDITY
    assert hum.entity_description.native_unit_of_measurement == PERCENTAGE
    assert hum.unique_id == "SERIAL1_humidity"
    assert hum.native_value == 45


def test_native_value_none_when_missing(coordinator):
    device_registry: DeviceRegistry = coordinator.data["device_registry"]
    device = device_registry.fetch_device("SERIAL1")
    device["entities"]["Temperature Sensor"]["sensors"].pop("temperature")
    device_registry.register_device(device)

    entity = SectorAlarmSensor(
        coordinator=coordinator,
        serial_no="SERIAL1",
        entity_description=Mock(key="temperature"),
        device_name="Smoke Detector Entrance",
        device_model="Smoke Detector",
        entity_model="Temperature Sensor",
    )

    assert entity.native_value is None


async def test_async_setup_entry_no_entities(hass: HomeAssistant):
    device_registry = DeviceRegistry()
    coordinator = Mock(spec=DataUpdateCoordinator)
    coordinator.data = {"device_registry": device_registry}
    coordinator.name = _DEVICE_COORDINATOR_NAME

    entry = Mock()
    entry.runtime_data = {RUNTIME_DATA.DEVICE_COORDINATORS: [coordinator]}

    add = Mock()

    await async_setup_entry(hass, entry, add)

    add.assert_not_called()


@pytest.fixture
def panel_coordinator(coordinator):
    coordinator.is_healthy = Mock(return_value=True)
    coordinator.data["device_registry"].register_device(
        {
            "serial_no": "PANEL1",
            "name": "Alarm Control Panel",
            "model": "Alarm panel",
            "entities": {
                "Alarm panel": {
                    "coordinator_name": coordinator.name,
                    "sensors": {"online": False, "alarm_status": 3},
                    "status_time_utc": "2000-01-01T00:00:00Z",
                    "last_updated": dt_util.utcnow().isoformat(),
                }
            },
        }
    )
    return coordinator


@pytest.fixture
def reported_sensor(panel_coordinator):
    return SectorReportedAlarmStateSensor(
        panel_coordinator, "PANEL1", "Alarm Control Panel", "Alarm panel", "Alarm panel"
    )


async def test_setup_adds_one_panel_sensor(hass, entry, panel_coordinator):
    other_coordinator = Mock(spec=DataUpdateCoordinator)
    other_coordinator.name = "other-coordinator"
    other_coordinator.data = panel_coordinator.data
    entry.runtime_data[RUNTIME_DATA.DEVICE_COORDINATORS].append(other_coordinator)
    add = Mock()

    await async_setup_entry(hass, entry, add)

    entities = add.call_args.args[0]
    assert len(entities) == 3
    panel = next(e for e in entities if isinstance(e, SectorReportedAlarmStateSensor))
    assert panel.unique_id == "PANEL1_reported_alarm_state"
    assert panel.device_info["identifiers"] == {("sector", "PANEL1")}
    assert panel.entity_description.device_class == SensorDeviceClass.ENUM
    assert panel.entity_description.options == ["disarmed", "armed_home", "armed_away"]
    assert panel.entity_description.translation_key == "reported_alarm_state"
    assert panel.native_value == "armed_away"


@pytest.mark.parametrize("online", [True, False])
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (1, "disarmed"),
        (2, "armed_home"),
        (3, "armed_away"),
        (0, None),
        (99, None),
        (None, None),
    ],
)
def test_reported_state_mapping(
    panel_coordinator, reported_sensor, online, status, expected
):
    registry = panel_coordinator.data["device_registry"]
    device = registry.fetch_device("PANEL1")
    sensors = device["entities"]["Alarm panel"]["sensors"]
    sensors["online"] = online
    if status is None:
        sensors.pop("alarm_status")
    else:
        sensors["alarm_status"] = status
    registry.register_device(device)

    assert reported_sensor.native_value == expected
    assert reported_sensor.available


def test_offline_sensor_follows_registry_updates(panel_coordinator, reported_sensor):
    assert reported_sensor.native_value == "armed_away"
    registry = panel_coordinator.data["device_registry"]
    device = registry.fetch_device("PANEL1")
    device["entities"]["Alarm panel"]["sensors"]["alarm_status"] = 1
    registry.register_device(device)

    assert reported_sensor.native_value == "disarmed"
    assert reported_sensor.extra_state_attributes["is_online"] is False


def test_reported_attributes_and_old_state_timestamp(panel_coordinator, reported_sensor):
    entity = reported_sensor.entity_data
    assert reported_sensor.extra_state_attributes == {
        "serial_number": "PANEL1",
        "is_online": False,
        "status_time_utc": "2000-01-01T00:00:00Z",
        "last_successful_update": entity["last_updated"],
    }
    assert reported_sensor.available

    registry = panel_coordinator.data["device_registry"]
    device = registry.fetch_device("PANEL1")
    device["entities"]["Alarm panel"].pop("status_time_utc")
    registry.register_device(device)
    assert reported_sensor.extra_state_attributes["status_time_utc"] is None
    assert reported_sensor.available


@pytest.mark.parametrize(
    ("healthy", "failures", "age_minutes", "expected"),
    [
        (True, 0, 0, True),
        (True, 1, 0, True),
        (True, 2, 0, False),
        (False, 0, 0, False),
        (True, 0, 59, True),
        (True, 0, 61, False),
    ],
)
def test_reported_availability(
    panel_coordinator, reported_sensor, healthy, failures, age_minutes, expected
):
    panel_coordinator.is_healthy.return_value = healthy
    registry = panel_coordinator.data["device_registry"]
    device = registry.fetch_device("PANEL1")
    entity = device["entities"]["Alarm panel"]
    entity["failed_update_count"] = failures
    entity["last_updated"] = (
        dt_util.utcnow() - timedelta(minutes=age_minutes)
    ).isoformat()
    registry.register_device(device)

    assert reported_sensor.available is expected
    assert reported_sensor.native_value == "armed_away"


def test_reported_sensor_unavailable_when_panel_missing(
    panel_coordinator, reported_sensor
):
    panel_coordinator.data["device_registry"] = DeviceRegistry()

    assert not reported_sensor.available
    assert reported_sensor.native_value is None


async def test_reported_sensor_writes_enum_state(hass, reported_sensor):
    component = EntityComponent(logging.getLogger(__name__), "sensor", hass)
    await component.async_add_entities([reported_sensor])

    state = hass.states.get(reported_sensor.entity_id)
    assert state.state == "armed_away"
    assert state.attributes["device_class"] == "enum"
    assert state.attributes["options"] == ["disarmed", "armed_home", "armed_away"]
    assert state.attributes["is_online"] is False
