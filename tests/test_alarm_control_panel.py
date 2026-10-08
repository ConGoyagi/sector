from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from homeassistant.exceptions import HomeAssistantError

from custom_components.sector.alarm_control_panel import SectorAlarmControlPanel
from custom_components.sector.const import CONF_IGNORE_QUICK_ARM
from custom_components.sector.coordinator import (
    DeviceRegistry,
    SectorDeviceDataUpdateCoordinator,
)


@pytest.fixture
def panel():
    registry = DeviceRegistry()
    registry.register_device(
        {
            "serial_no": "PANEL1",
            "entities": {
                "Alarm panel": {
                    "sensors": {"online": True, "alarm_status": 1},
                    "panel_code_length": 4,
                }
            },
        }
    )
    coordinator = Mock(spec=SectorDeviceDataUpdateCoordinator)
    coordinator.data = {"device_registry": registry}
    coordinator.sector_api = AsyncMock()
    entry = Mock(options={CONF_IGNORE_QUICK_ARM: False})
    return SectorAlarmControlPanel(
        coordinator, entry, "PANEL1", "Alarm Control Panel", "Alarm panel", "Alarm panel"
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (1, AlarmControlPanelState.DISARMED),
        (2, AlarmControlPanelState.ARMED_HOME),
        (3, AlarmControlPanelState.ARMED_AWAY),
        (0, None),
        (99, None),
    ],
)
def test_panel_mapping_unchanged(panel, status, expected):
    registry = panel.coordinator.data["device_registry"]
    device = registry.fetch_device("PANEL1")
    device["entities"]["Alarm panel"]["sensors"]["alarm_status"] = status
    registry.register_device(device)
    assert panel.alarm_state == expected


async def test_offline_panel_keeps_state_and_blocks_commands(panel):
    assert panel.alarm_state == AlarmControlPanelState.DISARMED
    registry = panel.coordinator.data["device_registry"]
    device = registry.fetch_device("PANEL1")
    device["entities"]["Alarm panel"]["sensors"].update(online=False, alarm_status=3)
    registry.register_device(device)

    assert panel.alarm_state == AlarmControlPanelState.DISARMED
    for command in (
        panel.async_alarm_arm_away,
        panel.async_alarm_arm_home,
        panel.async_alarm_disarm,
    ):
        with pytest.raises(HomeAssistantError, match="offline"):
            await command(code="1234")
    panel.coordinator.sector_api.arm_system.assert_not_called()
    panel.coordinator.sector_api.disarm_system.assert_not_called()
