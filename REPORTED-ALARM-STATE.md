# Reported Alarm State sensor

## Goal

Add a read-only Home Assistant sensor that exposes Sector's reported alarm state,
including when `GetPanelStatus` returns `IsOnline: false`. The intended use is
to arm a separate camera system when Sector reports an armed state.

The sensor represents the last state reported by Sector's API. A successful
fetch does not guarantee that Sector has received a recent update from the
physical panel.

## Behavior

| Item | Requirement |
| --- | --- |
| Name | Reported Alarm State |
| Device | Existing alarm panel device |
| Unique ID | `<panel_id>_reported_alarm_state` |
| Device class | Enum |
| State `1` | `disarmed` |
| State `2` | `armed_home` |
| State `3` | `armed_away` |
| State `0`, missing, or unsupported | Unknown |
| Online handling | Report state whether `IsOnline` is true or false |
| Polling | Reuse the existing panel-status coordinator; no additional requests |
| Controls | Read-only; existing arm/disarm restrictions remain unchanged |

Expose these attributes alongside the base entity's existing attributes:

- `is_online`: the connectivity flag returned by Sector.
- `status_time_utc`: the API's `StatusTimeUtc`, or `None` when absent.
- `last_successful_update`: the successful panel-status processing time stored
  in the registry's `last_updated`.

Do not use the state-change timestamp as a freshness limit: an alarm can
legitimately remain in the same state for days. Follow existing coordinator
health, entity failed-update, and fetch-age availability thresholds instead.
Those thresholds may retain the last value through transient failures.

## Tasks

### 1. Preserve the state-change timestamp

- [x] Add optional `StatusTimeUtc` to the `PanelStatus` payload type in
  `custom_components/sector/api_model.py`.
- [x] Preserve the timestamp in the panel entity data created by
  `_DeviceProcessor.process_alarm_panel` in
  `custom_components/sector/coordinator.py`.
- [x] Keep the API timestamp separate from `last_updated`.
- [x] Cover payloads with and without `StatusTimeUtc` in coordinator tests.

### 2. Share alarm-state mapping

- [x] Move the existing status-to-Home-Assistant-state mapping to a suitable
  shared location, avoiding a dependency from the sensor platform on the alarm
  control panel platform.
- [x] Reuse it in both the existing alarm panel and the new sensor.
- [x] Preserve the alarm panel's existing mappings and offline behavior.

### 3. Add the sensor

Depends on tasks 1 and 2.

- [x] Add a dedicated reported-state sensor in
  `custom_components/sector/sensor.py`, based on `SectorAlarmBaseEntity`.
- [x] Create exactly one sensor for each alarm panel through the existing
  coordinator-filtered registry discovery.
- [x] Use an enum description with `disarmed`, `armed_home`, and `armed_away`
  as its supported options.
- [x] Return `None` for missing, zero, or unsupported status codes rather than
  treating them as disarmed.
- [x] Expose the attributes defined above without dropping the base entity's
  attributes.
- [x] Reuse existing availability behavior without an `IsOnline` gate.
- [x] Keep temperature and humidity sensor values numeric.
- [x] Do not add API requests, change polling intervals, or change alarm
  controls.

### 4. Localize and document

Depends on task 3.

- [x] Add the sensor name and enum state labels to the existing translation
  files in `custom_components/sector/translations`.
- [x] Update `readme.md` with the reported-state sensor's purpose and its
  distinction from connectivity.
- [x] Explain that polling and API propagation introduce a delay, and
  throttling can extend it.
- [x] Explain that camera automations should act on explicit states and leave
  camera mode unchanged when the sensor is unknown or unavailable.

### 5. Verify behavior

Depends on tasks 1 through 4.

- [x] Extend `tests/test_sensor.py` to cover sensor discovery, device identity,
  unique ID, enum options, attributes, and each supported state.
- [x] Cover missing, zero, and unsupported status codes.
- [x] Verify that an offline panel can still produce updated sensor states.
- [x] Verify successful-fetch timestamps are distinct from state-change
  timestamps and that an old state-change time does not make the sensor
  unavailable.
- [x] Cover coordinator health, failed-update, and fetch-age availability
  thresholds using existing test patterns.
- [x] Retain coverage for existing temperature and humidity sensors.
- [x] Verify the shared mapping leaves alarm-panel state handling and offline
  arm/disarm guards unchanged.
- [x] Run the targeted tests:

  ```powershell
  pytest -vv tests\test_sensor.py tests\test_coordinator_SectorDeviceDataUpdateCoordinator.py tests\test_entity.py tests\test_alarm_control_panel.py
  ```

  All 56 targeted tests passed in a Linux Docker environment with Python 3.14
  and the dependencies from `scripts/setup.sh`.

## Server acceptance

- [ ] Install the updated integration and reload it.
- [ ] Confirm that the sensor is attached to the existing alarm panel device.
- [ ] Observe normal arm/disarm operations and compare the sensor with
  `GetPanelStatus` and the Sector app.
- [ ] Verify that status and state-change timestamps follow those operations
  even if `IsOnline` remains false.
- [ ] Measure the delay before relying on the sensor for camera automation.
- [ ] Confirm API failures are not interpreted as disarming.

## Scope boundary

This addition does not establish why the legacy panel reports itself offline,
guarantee real-time data, or change API retry/throttling behavior. It exposes
the already-fetched reported state while preserving existing alarm controls.
