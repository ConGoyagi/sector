# Repository guidance

## Build, test, and validation

- Install the Home Assistant and pytest test dependencies with `./scripts/setup.sh` (run from a POSIX shell).
- Run the full test suite with `pytest -vv`.
- Run one test with `pytest -vv tests/test_client_Retryable.py::test_should_retry_on_retryable_exception`; replace the path and test name for the test being changed. `pytest -q tests -k "keyword"` is useful for selecting related tests.
- CI also runs HACS integration validation and Home Assistant Hassfest validation. These are GitHub Actions steps, not repository-provided local lint commands.

## Architecture

This is a Home Assistant custom integration in `custom_components/sector`. The config flow authenticates with the Sector API, discovers/selects a panel, and stores its ID and options in the config entry. Setup creates one shared API client and token provider using Home Assistant's managed `aiohttp` session.

`client.py` handles authentication, HTTP requests, retries, and API actions; `endpoints.py` maps endpoint types to Sector URLs and methods; `api_model.py` describes the provider's JSON payloads. `coordinator.py` uses a panel-info coordinator plus domain-specific polling coordinators. It filters unsupported endpoints using panel capabilities and available equipment, then `_DeviceProcessor` normalizes API responses into a shared `DeviceRegistry`, keyed by device serial and entity model.

Platform modules (`sensor.py`, `binary_sensor.py`, `lock.py`, `switch.py`, `alarm_control_panel.py`, `event.py`, and `camera.py`) turn registry data into Home Assistant entities. `entity.py` supplies shared device identity and availability behavior. Control entities send commands through the shared API client and request coordinator refreshes; preserve their optimistic pending-state handling.

## Repository-specific conventions

- Endpoint support is expressed in `DataEndpointType` metadata and coordinator endpoint sets. Keep endpoint classification, URL/method mapping, setup filtering, and response processing consistent when adding or changing an API endpoint.
- Sector responses use provider-shaped keys and nested `Floors`/`Rooms`/`Devices` or `Sections`/`Places`/`Components` structures. The processor converts them into the registry shape consumed by platforms; update both sides when changing that shape.
- Device identity is based on serial number. Entity identity is typically a serial-derived unique ID, and entity data is selected by its entity model and owning coordinator.
- Tests are async pytest tests using `pytest-homeassistant-custom-component`; pytest's asyncio mode is configured as `auto`. API and coordinator behavior is commonly tested with `AsyncMock`, `Mock`, and typed payload fixtures.
