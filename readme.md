[![Sector Alarm](custom_components/sector/brand/logo.png)](https://www.sectoralarm.se/)

[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Repo size](https://img.shields.io/github/repo-size/gjohansson-ST/sector?style=for-the-badge)](https://github.com/gjohansson-ST/sector)
[![Latest release](https://img.shields.io/github/release/gjohansson-ST/sector?style=for-the-badge)](https://github.com/gjohansson-ST/sector/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/gjohansson-ST/sector/total?style=for-the-badge)](https://github.com/gjohansson-ST/sector/releases/latest)
![Stars](https://img.shields.io/github/stars/gjohansson-ST/sector?style=for-the-badge)
![Issues or Pull Requests](https://img.shields.io/github/issues/gjohansson-ST/sector?style=for-the-badge)
[![License](https://img.shields.io/github/license/gjohansson-ST/sector?style=for-the-badge)](LICENSE)

[![Made for Home Assistant](https://img.shields.io/badge/Made_for-Home%20Assistant-blue?style=for-the-badge&logo=homeassistant)](https://github.com/home-assistant)

[![Discord](https://img.shields.io/discord/872446427664625664?style=for-the-badge&label=Discord&cacheSeconds=3600)](https://discord.gg/EG7cWFQMGW)

# Sector Alarm integration for Home Assistant

This integration connects Home Assistant with the Sector Alarm system allowing monitoring and control directly from Home Assistant (officially supported in Sweden and expected to work in other regions).

## Supported features ##
- ✅ Alarm control
- ✅ Door lock
- ✅ Smart Plugs
- ✅ Temperature sensors
- ✅ Humidity sensors
- ✅ Various binary sensors

## Important notes ##

On alarm installations which are not wired, make sure you take the binary sensor `Online` into account to ensure the alarm state is a trusted state. The entity for alarm panel can only be armed/disarmed on alarms which are online.

### Reported Alarm State sensor

The read-only **Reported Alarm State** sensor exposes the last alarm state returned
by Sector's API, even when the panel reports `IsOnline: false`. Its states are
`disarmed`, `armed_home`, and `armed_away`; missing or unsupported status codes
produce an unknown state. It uses the existing panel-status polling and does not
change the alarm control panel's offline safeguards.

The attributes `is_online`, `status_time_utc`, and `last_successful_update`
distinguish reported connectivity, the API's state-change timestamp (when
provided), and the last successful fetch. A successful fetch does not guarantee
fresh data from the physical panel. The sensor follows the integration's existing
availability thresholds, which retain the last value through transient failures.
An old state-change timestamp alone does not make it unavailable.

For camera automations, trigger on explicit states and leave camera mode unchanged
when the sensor is unknown or unavailable. Normal polling introduces up to about
one minute of delay, plus API propagation time; throttling or failed requests can
extend that delay. Confirm that the sensor follows normal arm/disarm operations
on your installation before relying on it.

## Installation ##

**Minimum Required Home Assistant version:** 2026.1.0

### Option 1: HACS (recommended)

Click the button below to add the repository to HACS:

[![Add integrations](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=sector)

After installation:

1. Restart Home Assistant
2. Go to **Settings → Integrations**
3. Click **Add Integration**
4. Search for **Sector Alarm**
5. Follow the on-screen setup instructions

### Option 2: Manual ###

1. Download the [latest release](https://github.com/gjohansson-ST/sector/releases/latest)
2. In your Home Assistant configuration directory, create folder `custom_components` if it doesn’t already exist
3. Inside `custom_components`, create a folder named `sector`
4. Copy all release files from `custom_components/sector` into `homeassistant/custom_components/sector`.
5. Restart Home Assistant

The file structure should look like below when completed:
```
homeassistant/
└── custom_components/
    └── sector/
        ├── __init__.py
        ├── ...

```

## Configuration options ##
| Configuration        | Required | Description                   |
|----------------------| -------- | ----------------------------- |
| Username             | **Yes**  | Sets the e-mail user address for your Sector alarm account.|
| Password             | **Yes**  | Sets the password for your Sector alarm account.|
| Ignore ”Quick Arming”| No       | *Default: false* <br> Ignore the "Quick Arming" Sector alarm setting and always require PIN-code when arming.|

## Contributing & Support ##

This integration is actively maintained, and help and ideas are always welcome.

If you encounter any issues, bugs, or unexpected behavior, please don’t hesitate to open an [issue](https://github.com/gjohansson-ST/sector/issues) on GitHub, or make a post in the [discord](https://discord.gg/EG7cWFQMGW) channel.

## Maintainers

- [OathMeadow](https://github.com/OathMeadow)
- [gjohansson-ST](https://github.com/gjohansson-ST)

### Previous maintainers

Big thanks to:

- [garnser](https://github.com/garnser)
