[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
# Deutsche Bahn Homeassistant Sensor
The `deutsche_bahn` sensor will give you the departure time of the next train for the given connection. In case of a delay, the delay is also shown. Additional details are used to inform about, e.g., the type of the train, price, and if it is on time.

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Db-bahn.svg/1280px-Db-bahn.svg.png" alt="Deutsche Bahn" width="300px">

<img src="images/sensor.png" alt="Deutsche Bahn Sensor" width="300px">


The official Deutsche Bahn Homeassistant integration got removed with release 2022.11 - therefore this custom integration exists. It got removed due to cloud scraping, but still was fully functional.
I will not give much support on this integration! Use it as it is, this is the same part as of release 2022.09 from HA, see [here](https://github.com/home-assistant/core/tree/c741d9d0452970c39397deca1c65766c8cb917da/homeassistant/components/deutsche_bahn).

Below is the old Homeassistant documentation taken from [here](https://github.com/home-assistant/home-assistant.io/blob/b38ab5e8bc745e8e751eb27c2c079de8a8e83d5e/source/_integrations/deutsche_bahn.markdown).
---
- title: Deutsche Bahn
- description: Instructions on how to integrate timetable data for traveling in Germany within Home Assistant.
- ha_category:
  - Transport
- ha_iot_class: Cloud Polling
- ha_release: 0.14
- ha_domain: deutsche_bahn
- ha_platforms:
  - sensor
- ha_integration_type: integration
---

The `deutsche_bahn` sensor will give you the departure time of the next train for the given connection. In case of a delay, the delay is also shown. Additional details are used to inform about, e.g., the type of the train, price, and if it is on time.

To enable this sensor, add the following lines to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: deutschebahn
    from: NAME_OF_START_STATION
    to: NAME_OF_FINAL_STATION
```

{% configuration %}
from:
  description: The name of the start station.
  required: true
  type: string
to:
  description: The name of the end/destination station.
  required: true
  type: string
offset:
  description: Do not display departures leaving sooner than this number of seconds. Useful if you are a couple of minutes away from the stop. The formats "HH:MM" and "HH:MM:SS" are also supported.
  required: false
  type: time
  default: 00:00
only_direct:
  description: Only show direct connections.
  required: false
  type: boolean
  default: false
{% endconfiguration %}

This sensor stores a lot of attributes which can be accessed by other sensors, e.g., a [template sensor](/integrations/template).

{% raw %}

```yaml
# Example configuration.yaml entry
template:
  - sensor:
    - name : "Next departure"
      state: "{{ state_attr('sensor.munich_to_ulm', 'next') }}"
```

{% endraw %}

The data is coming from the [bahn.de](https://www.bahn.de/p/view/index.shtml) website.

## Installation
### 1. Using HACS (recommended way)

Open your HACS Settings and add

https://github.com/faserf/ha-deutschebahn

as custom repository URL.

Then install the "Deutsche Bahn" integration.

If you use this method, your component will always update to the latest version.

### 2. Manual
Place a copy of:

[`__init__.py`](custom_components/deutschebahn) at `<config>/custom_components/`

where `<config>` is your Home Assistant configuration directory.

>__NOTE__: Do not download the file by using the link above directly. Rather, click on it, then on the page that comes up use the `Raw` button.

## Configuration

### Configuration Variables
- **from**: Enter your Start location
- **to**: Enter your destination

## Bug reporting
Open an issue over at [github issues](https://github.com/FaserF/ha-deutschebahn/issues). Please prefer sending over a log with debugging enabled.

Please note that I will only give limited support, as this integration was written by the HA devs and not by me!

To enable debugging enter the following in your configuration.yaml

```yaml
logger:
    logs:
        custom_components.deutschebahn: debug
```

## Thanks to
Huge thanks to [@homeassistant](https://github.com/home-assistant/core/tree/c741d9d0452970c39397deca1c65766c8cb917da/homeassistant/components/deutsche_bahn) for the official old integration, where this one is based on!