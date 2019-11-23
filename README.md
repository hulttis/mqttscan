# MQTT SCAN 1.2.7 (191123)
This software can be used to collect information about sonoff/tasmota/shelly devices reqistered in the MQTT broker.

## MAIN FUNCTIONALITIES
- publishes different status requests to the sonoff/tasmota group topics `sonoffs/cmnd/backlog`, `cmnd/sonoffs/backlog`, `tasmotas/cmnd/backlog` and `cmnd/tasmotas/backlog`
- publishes `shellies/announce` for shelly devices and then collects device settings using http API

## COMMAND LINE PARAMETERS
### mqttscan.py [-h] -b <broker> [-v <verbose>] [-f] [-t <mqtttimeout>] [-s <httptimeout>] [--tasmota] [--shellies]
| optional argument | long format   | parameter                                                 |
|:------------------|:--------------|:----------------------------------------------------------|
| -h                | --help        |                                                           |
| -b                | --broker      | MQTT broker (mqtt://<username>:<password>@mqtt.local.net) |
| -v                | --verbose     | output verbose level basic/full (default: basic)          |
| -f                | --features    | decodes sonoff/tasmota features                           |
| -t                | --mqtttimeout | mqtt timeout (default: 1s)                                |
| -s                | --httptimeout | http timeout (default: 8s)                                |

# LICENCE
MIT License is used for this software.
