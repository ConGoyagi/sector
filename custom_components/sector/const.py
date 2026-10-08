"""Constants for the Sector Alarm integration."""

from enum import Enum

from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.const import Platform

DOMAIN = "sector"
PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.CAMERA,
    Platform.LOCK,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.EVENT,
]

CONF_PANEL_ID = "panel_id"
CONF_IGNORE_QUICK_ARM = "ignore_quick_arm"

ALARM_STATE_TO_HA_STATE = {
    3: AlarmControlPanelState.ARMED_AWAY,
    2: AlarmControlPanelState.ARMED_HOME,
    1: AlarmControlPanelState.DISARMED,
    0: None,
}


class RUNTIME_DATA(Enum):
    DEVICE_COORDINATORS = ("Device coordinators list key",)
    SECTOR_ALARM_API = "Sector Alarm API object key"
