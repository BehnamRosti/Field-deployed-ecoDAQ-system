# Field-deployed ecoDAQ system

This repository contains the ecoDAQ software used for long-term monitoring at the ZEB Living Lab in Trondheim, Norway. The deployment monitored the TC1 ventilated window and the surrounding indoor and outdoor environment.

## System architecture

```text
Sensors -> Raspberry Pi/Python -> InfluxDB -> Grafana
                         `------> local CSV file
```

The system combines sensor acquisition, local data logging, time-series storage, and real-time visualization. Docker is used to run the Python application, InfluxDB, and Grafana as connected services.

## Repository files

- `app.py` — integrated acquisition and data-transfer application.
- `requirements.txt` — Python packages used by the application.
- `Dockerfile` — container definition for the acquisition application.
- `docker-compose.yml` — configuration for the application, InfluxDB, and Grafana.
- `ZEB-Living-Lab-Grafana-dashboard.json` — exported Grafana dashboard.
- `CITATION.cff` — citation metadata.
- `LICENSE` — MIT license.

## Monitored parameters

The deployed system records:

- air and surface temperature;
- relative humidity and air pressure;
- CO2 concentration;
- particulate matter, VOC, and NOx indices;
- illuminance;
- heat flux using Hukseflux HFP01 sensors;
- airflow velocity;
- sound level;
- differential pressure using Sensirion SDP810 sensors.

The SDP810 implementation uses continuous averaged measurement, CRC checking, signed pressure conversion, and the scale factor returned by the sensor.

## Software configuration

The Docker stack uses InfluxDB 1.8 and Grafana 7.5.7, matching the deployed software environment. Sensor data are written to the `sensordata` database and simultaneously stored in a local CSV file.

Passwords in the public files are replaced with `PASSWORD`; no deployment password is included in this repository.

## Relation to earlier ecoDAQ work

This repository continues the ecoDAQ development presented in:

1. [Basic low-cost DAQ system](https://github.com/BehnamRosti/Basic_low-cost_DAQ_system)
2. [Raspberry Pi DAQ with Docker, InfluxDB, and Grafana](https://github.com/BehnamRosti/RPi_based_DAQ_system_with_Docker_influxDB_Grafana)
3. [Low-cost modular monitoring system for indoor lighting assessment](https://github.com/BehnamRosti/Low-cost-modular-monitoring-system-for-indoor-lighting-assessment)

The earlier repositories describe laboratory development and toolkit validation. This repository documents the subsequent field deployment at the ZEB Living Lab.

