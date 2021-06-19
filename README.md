# Innova AC Integration for Home Assistant

This integration is used to control Innova ACs (or ones copatible with their app), 
it support most of the modes (drying, fan only,auto, heating, cooling), 
setting the setpoint, reading the ambient temperature, fan speed, swing and on/off

## Installation
Installation is via the Home Assistant Community Store (HACS), which is the best place to get third-party integrations for Home Assistant. Once you have HACS set up, simply search the Integrations section for Goldair.

## Configuration
You can easily configure your devices using the Integrations UI at Home Assistant > Configuration > Integrations > +. This is the preferred method as things will be unlikely to break as this integration is upgraded. You will need to provide your device's IP address, device ID and local key; the last two can be found using the instructions below.

If you would rather configure using yaml, add the following lines to your configuration.yaml file (but bear in mind that if the configuration options change your configuration may break until you update it to match the changes):

```
# Example configuration.yaml entry
climate:
  - platform: innova_ac
    host: 192.168.1.86
    name: First AC
```

### Configuration variables
##### host
*(string) (Required)* IP or hostname of the device.
##### name
*(string) (Optional)* Any unique name for the device; if omitted the name is took from the device itself