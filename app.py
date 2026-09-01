import time
import sys
import os
import board
import busio
import csv
import adafruit_mcp9808
import adafruit_scd30
import adafruit_tca9548a
import adafruit_bme280.advanced as adafruit_bme280
import adafruit_sht31d
import adafruit_veml7700
import adafruit_tsl2591
import adafruit_bh1750
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from sensirion_i2c_driver import I2cConnection, LinuxI2cTransceiver
from sensirion_i2c_sen5x import Sen5xI2cDevice
from smbus2 import SMBus, i2c_msg
from datetime import datetime
from influxdb import InfluxDBClient

#----------------------------------------------------------------------------
# InfluxDB configuration
host = "influxdb"
port = 8086
user = "NTNU"
password = "PASSWORD"
dbname = "sensordata"
client = InfluxDBClient(host, port, user, password, dbname)

#----------------------------------------------------------------------------
# Ensure the data directory exists
data_directory = "/app/data"
os.makedirs(data_directory, exist_ok=True)

file_name = os.path.join(data_directory, "rpi.csv")

# Initialize the CSV file with headers if it doesn't exist
if not os.path.exists(file_name):
    with open(file_name, "w", newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['timestamp', 'sensor', 'type', 'location', 'label', 'temperature', 'humidity', 'pressure',
                             'co2', 'lux', 'voltage', 'heat_flux', 'velocity', 'sound_level', 'dp',
                             'PM1.0', 'PM2.5', 'PM4.0', 'PM10.0', 'voc_index', 'nox_index'])

#----------------------------------------------------------------------------
# Scans all channels of a given TCA9548A I2C multiplexer to detect connected I2C devices
def scan_i2c_bus(tca_device):
    for channel in range(8):
        channel_bus = tca_device[channel]
        if channel_bus.try_lock():
            try:
                addresses = channel_bus.scan()
                addresses = [hex(addr) for addr in addresses if addr != tca_device.address]
                if addresses:
                    print(f"Channel {channel}: Devices found at {addresses}")
                else:
                    print(f"Channel {channel}: No devices found")
            finally:
                channel_bus.unlock()

# Initialize TSL2591 sensor
def initialize_sensor_tsl(mux, channel):
    if mux != 'nan':
        try:
            sensor = adafruit_tsl2591.TSL2591(mux[channel])
            sensor.gain = adafruit_tsl2591.GAIN_LOW
            sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS
            return sensor
        except Exception as e:
            print(f"Failed to initialize TSL2591 on channel {channel}: {e}")
    return 'nan'

# Initialize VEML7700 sensor
def initialize_sensor_veml(mux, channel):
    if mux != 'nan':
        try:
            sensor = adafruit_veml7700.VEML7700(mux[channel])
            sensor.light_gain = sensor.ALS_GAIN_1_8
            sensor.light_integration_time = sensor.ALS_25MS
            return sensor
        except Exception as e:
            print(f"Failed to initialize VEML7700 on channel {channel}: {e}")
    return 'nan'

# Initialize BH1750 sensor
def initialize_sensor_bh(mux, channel):
    if mux != 'nan':
        try:
            sensor = adafruit_bh1750.BH1750(mux[channel])
            sensor.mode = adafruit_bh1750.Mode.CONTINUOUS
            sensor.resolution = adafruit_bh1750.Resolution.LOW
            return sensor
        except Exception as e:
            print(f"Failed to initialize BH1750 on channel {channel}: {e}")
    return 'nan'

# Create I2C bus as normal
i2c_bus1 = busio.I2C(board.SCL, board.SDA)
i2c_bus2 = busio.I2C(board.D1, board.D0)

# Create the TCA9548A object and give it the I2C bus
try:
    tca1 = adafruit_tca9548a.TCA9548A(i2c_bus1, address=0x70)
except Exception as e:
    print(f"Failed to initialize TCA9548A at address 0x70: {e}")
    tca1 = 'nan'
scan_i2c_bus(tca1)

try:
    tca2 = adafruit_tca9548a.TCA9548A(i2c_bus1, address=0x71)
except Exception as e:
    print(f"Failed to initialize TCA9548A at address 0x71: {e}")
    tca2 = 'nan'
scan_i2c_bus(tca2)

try:
    tca3 = adafruit_tca9548a.TCA9548A(i2c_bus1, address=0x73)
except Exception as e:
    print(f"Failed to initialize TCA9548A at address 0x73: {e}")
    tca3 = 'nan'
scan_i2c_bus(tca3)

try:
    tca4 = adafruit_tca9548a.TCA9548A(i2c_bus1, address=0x74)
except Exception as e:
    print(f"Failed to initialize TCA9548A at address 0x74: {e}")
    tca4 = 'nan'
scan_i2c_bus(tca4)

#----------------------------------------------------------------------------
# Initialize sensors
mcp1 = adafruit_mcp9808.MCP9808(tca1[0])
mcp2 = adafruit_mcp9808.MCP9808(tca1[1])
mcp3 = adafruit_mcp9808.MCP9808(tca1[2])
mcp4 = adafruit_mcp9808.MCP9808(tca1[3])
mcp5 = adafruit_mcp9808.MCP9808(tca1[4])
mcp6 = adafruit_mcp9808.MCP9808(tca1[5])
mcp7 = adafruit_mcp9808.MCP9808(tca1[6])
mcp8 = adafruit_mcp9808.MCP9808(tca1[7])

mcp9 = adafruit_mcp9808.MCP9808(tca2[0])
mcp10 = adafruit_mcp9808.MCP9808(tca2[1])
mcp11 = adafruit_mcp9808.MCP9808(tca2[2])
mcp12 = adafruit_mcp9808.MCP9808(tca2[3])
mcp13 = adafruit_mcp9808.MCP9808(tca2[4])
mcp14 = adafruit_mcp9808.MCP9808(tca2[5])
mcp15 = adafruit_mcp9808.MCP9808(tca2[6])
mcp16 = adafruit_mcp9808.MCP9808(tca2[7])

try:
    sht1 = adafruit_sht31d.SHT31D(i2c_bus1, address=0x45)
except:
    sht1 = 'nan'

try:
    bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c_bus1, address=0x76)
except:
    bme1 = 'nan'

veml1 = initialize_sensor_veml(tca3, 0)
tsl1 = initialize_sensor_tsl(tca3, 1)
bh1 = initialize_sensor_bh(tca3, 3)
tsl0 = initialize_sensor_tsl(tca3, 4)

veml2 = initialize_sensor_veml(tca4, 0)
tsl2 = initialize_sensor_tsl(tca4, 1)
bh2 = initialize_sensor_bh(tca4, 3)

ads1 = ADS.ADS1115(i2c_bus1, address=0x48)
chan1 = AnalogIn(ads1, ADS.P0, ADS.P1)
chan2 = AnalogIn(ads1, ADS.P2, ADS.P3)
ads1.gain = 8

ads2 = ADS.ADS1115(i2c_bus1, address=0x49)
chan3 = AnalogIn(ads2, ADS.P0, ADS.P1)
chan4 = AnalogIn(ads2, ADS.P2, ADS.P3)
ads2.gain = 8

ads3 = ADS.ADS1115(i2c_bus1, address=0x4a)
chan5 = AnalogIn(ads3, ADS.P0)
chan6 = AnalogIn(ads3, ADS.P1)
chan7 = AnalogIn(ads3, ADS.P2)
chan8 = AnalogIn(ads3, ADS.P3)
ads3.gain = 2/3

try:
    sen1 = Sen5xI2cDevice(I2cConnection(LinuxI2cTransceiver('/dev/i2c-1')))
    sen1.device_reset()
    sen1.start_measurement()
except:
    sen1 = 'nan'

try:
    scd1 = adafruit_scd30.SCD30(i2c_bus1)
except:
    scd1 = 'nan'

try:
    mcp23 = adafruit_mcp9808.MCP9808(i2c_bus1, address=0x19)
except:
    mcp23 = 'nan'

try:
    mcp24 = adafruit_mcp9808.MCP9808(i2c_bus1, address=0x1a)
except:
    mcp24 = 'nan'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
try:    
    mcp17 = adafruit_mcp9808.MCP9808(i2c_bus2)	#black TC2 back
except:
    mcp17 = 'nan'
try:
    mcp18 = adafruit_mcp9808.MCP9808(i2c_bus2, address=0x19)		#black TC2 back
except:
    mcp18 = 'nan'
try:
    mcp19 = adafruit_mcp9808.MCP9808(i2c_bus2, address=0x1a)		#blue TC2 back
except:
    mcp19 = 'nan'
try:
    mcp20 = adafruit_mcp9808.MCP9808(i2c_bus2, address=0x1b)		#black TC2 front
except:
    mcp20 = 'nan'
try:
    mcp21 = adafruit_mcp9808.MCP9808(i2c_bus2, address=0x1c)		#blue TC2 back
except:
    mcp21 = 'nan'
try:
    mcp22 = adafruit_mcp9808.MCP9808(i2c_bus2, address=0x1d)		#blue TC2 front
except:
    mcp22 = 'nan'
    
    
try:
    tca5 = adafruit_tca9548a.TCA9548A(i2c_bus2, address=0x70)
except Exception as e:
    print(f"Failed to initialize TCA9548A at address 0x70: {e}")
    tca5 = 'nan'

bme2 = adafruit_bme280.Adafruit_BME280_I2C(tca5[2])
bme3 = adafruit_bme280.Adafruit_BME280_I2C(tca5[3])
bme4 = adafruit_bme280.Adafruit_BME280_I2C(tca5[4])
sht2 = adafruit_sht31d.SHT31D(tca5[5])
sht3 = adafruit_sht31d.SHT31D(tca5[6])
sht4 = adafruit_sht31d.SHT31D(tca5[7])

try:
    bme5 = adafruit_bme280.Adafruit_BME280_I2C(i2c_bus2, address=0x77)
except:
    bme5 = 'nan'

try:
    sen2 = Sen5xI2cDevice(I2cConnection(LinuxI2cTransceiver('/dev/i2c-0')))
    sen2.device_reset()
    sen2.start_measurement()
except:
    sen2 = 'nan'

try:
    scd2 = adafruit_scd30.SCD30(i2c_bus2)
except:
    scd2 = 'nan'


class SDP810:
    ADDRESS = 0x25
    START_CONTINUOUS_AVERAGED = [0x36, 0x15]

    def __init__(self, bus_number):
        self.bus = SMBus(bus_number)
        self._write_command(self.START_CONTINUOUS_AVERAGED)
        time.sleep(0.05)

    @staticmethod
    def _calculate_crc(data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    @classmethod
    def _check_crc(cls, data, received_crc):
        if cls._calculate_crc(data) != received_crc:
            raise ValueError("SDP810 CRC check failed")

    @staticmethod
    def _signed_int16(msb, lsb):
        value = (msb << 8) | lsb
        return value - 0x10000 if value & 0x8000 else value

    def _write_command(self, command):
        self.bus.i2c_rdwr(i2c_msg.write(self.ADDRESS, command))

    def read_differential_pressure(self):
        message = i2c_msg.read(self.ADDRESS, 9)
        self.bus.i2c_rdwr(message)
        data = list(message)

        self._check_crc(data[0:2], data[2])
        self._check_crc(data[3:5], data[5])
        self._check_crc(data[6:8], data[8])

        raw_pressure = self._signed_int16(data[0], data[1])
        scale_factor = (data[6] << 8) | data[7]
        if scale_factor == 0:
            raise ValueError("SDP810 returned a zero scale factor")

        return raw_pressure / scale_factor


try:
    sdp1 = SDP810(0)
except Exception as e:
    print(f"Failed to initialize SDP810 on I2C bus 0: {e}")
    sdp1 = 'nan'

try:
    sdp2 = SDP810(1)
except Exception as e:
    print(f"Failed to initialize SDP810 on I2C bus 1: {e}")
    sdp2 = 'nan'

#----------------------------------------------------------------------------
def write_sensor_data(sensor_data):
    client.write_points(sensor_data)

#----------------------------------------------------------------------------
def write_to_file(file_path, data):
    with open(file_path, "a") as f:
        f.write(",".join(map(str, data)) + "\n")

#----------------------------------------------------------------------------
def format_data(sensor, sensor_type, location, label, fields):
    return [{
        "measurement": "sensor_data",
        "tags": {
            "sensor": sensor,
            "type": sensor_type,
            "location": location,
            "label": label,
        },
        "fields": fields,
    }]

#----------------------------------------------------------------------------
def read_sensor(sensor, sensor_type):
    if sensor == 'nan':
        return {}
    if sensor_type == "MCP9808":
        return {"temperature": sensor.temperature}
    elif sensor_type == "BME280":
        return {
            "temperature": sensor.temperature,
            "humidity": sensor.humidity,
            "pressure": sensor.pressure,
        }
    elif sensor_type == "SHT31D":
        return {
            "temperature": sensor.temperature,
            "humidity": sensor.relative_humidity,
        }
    elif sensor_type == "SCD30":
        return {
            "temperature": sensor.temperature,
            "humidity": sensor.relative_humidity,
            "co2": sensor.CO2,
        }
    elif sensor_type == "TSL2591":
        return {"lux": sensor.lux}
    elif sensor_type == "BH1750" or sensor_type == "VEML7700":
        return {"lux": sensor.lux}
    elif sensor_type == "HFP01":
        voltage = sensor.voltage
        if sensor == chan1:
            A = 1e6 / 62.98
        elif sensor == chan2:
            A = 1e6 / 62.09
        elif sensor == chan3:
            A = 1e6 / 62.59
        elif sensor == chan4:
            A = 1e6 / 63.55
        heat_flux = A * voltage
        return {"voltage": voltage, "heat_flux": heat_flux}
    elif sensor_type == "OMRON":
        A = 0.0055
        B = -0.1112
        C = 0.8566
        D = -3.0791
        E = 4.9736
        F = -1.6458
        G = -0.9999
        velocity = A * sensor.voltage ** 6 + B * sensor.voltage ** 5 + C * sensor.voltage ** 4 + D * sensor.voltage ** 3 + E * sensor.voltage ** 2 + F * sensor.voltage + G
        return {"voltage": sensor.voltage, "velocity": velocity}
    elif sensor_type == "SEN0232":
        sound_level = 50.0 * sensor.voltage
        return {"voltage": sensor.voltage, "sound_level": sound_level}

# Read SEN5x sensor data
def read_sen_sensor(sensor):
    values = sensor.read_measured_values()
    return {
        "PM1.0": values.mass_concentration_1p0.physical,
        "PM2.5": values.mass_concentration_2p5.physical,
        "PM4.0": values.mass_concentration_4p0.physical,
        "PM10.0": values.mass_concentration_10p0.physical,
        "humidity": values.ambient_humidity.percent_rh,
        "temperature": values.ambient_temperature.degrees_celsius,
        "voc_index": values.voc_index.scaled,
        "nox_index": values.nox_index.scaled,
    }

# Read SDP sensor data
def read_sdp_sensor(sensor):
    if sensor == 'nan':
        return {}
    return {"dp": sensor.read_differential_pressure()}

#----------------------------------------------------------------------------
sensor_configs = [
    {"name": "mcp1", "sensor": mcp1, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tso_r(mcp1)
    {"name": "mcp2", "sensor": mcp2, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tso_l(mcp2)
    {"name": "mcp3", "sensor": mcp3, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tsi_up_r(mcp3)
    {"name": "mcp4", "sensor": mcp4, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tsi_up_l(mcp4)
    {"name": "mcp5", "sensor": mcp5, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tsi_mid_r(mcp5)
    {"name": "mcp6", "sensor": mcp6, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tsi_mid_l(mcp6)
    {"name": "mcp7", "sensor": mcp7, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tsi_low_r(mcp7)
    {"name": "mcp8", "sensor": mcp8, "type": "MCP9808", "location": "glazing", "label": "TC1"},    # Tsi_low_l(mcp8)
    {"name": "mcp9", "sensor": mcp9, "type": "MCP9808", "location": "opening", "label": "TC1"},    # Tinl_r(mcp9)
    {"name": "mcp10", "sensor": mcp10, "type": "MCP9808", "location": "opening", "label": "TC1"},  # Tinl_l(mcp10)
    {"name": "mcp11", "sensor": mcp11, "type": "MCP9808", "location": "cavity", "label": "TC1"},   # Tc_r(mcp11)
    {"name": "mcp12", "sensor": mcp12, "type": "MCP9808", "location": "cavity", "label": "TC1"},   # Tc_l(mcp12)
    {"name": "mcp13", "sensor": mcp13, "type": "MCP9808", "location": "opening", "label": "TC1"},  # Tsup_lr(mcp13)
    {"name": "mcp14", "sensor": mcp14, "type": "MCP9808", "location": "opening", "label": "TC1"},  # Tsup_ll(mcp14)
    {"name": "mcp15", "sensor": mcp15, "type": "MCP9808", "location": "opening", "label": "TC1"},  # Tsup_rr(mcp15)
    {"name": "mcp16", "sensor": mcp16, "type": "MCP9808", "location": "opening", "label": "TC1"},  # Tsup_rl(mcp16)
    {"name": "mcp17", "sensor": mcp17, "type": "MCP9808", "location": "surface", "label": "TC2"},  # Ts_black_b1(mcp17)
    {"name": "mcp18", "sensor": mcp18, "type": "MCP9808", "location": "surface", "label": "TC2"},  # Ts_black_b2(mcp18)
    {"name": "mcp19", "sensor": mcp19, "type": "MCP9808", "location": "surface", "label": "TC2"},  # Ts_blue_b1(mcp19)
    {"name": "mcp20", "sensor": mcp20, "type": "MCP9808", "location": "surface", "label": "TC2"},  # Ts_black_f(mcp20)
    {"name": "mcp21", "sensor": mcp21, "type": "MCP9808", "location": "surface", "label": "TC2"},  # Ts_blue_b2(mcp21)
    {"name": "mcp22", "sensor": mcp22, "type": "MCP9808", "location": "surface", "label": "TC2"},  # Ts_blue_f(mcp22)
    {"name": "mcp23", "sensor": mcp23, "type": "MCP9808", "location": "glazing", "label": "window"},  # Tsi_window(mcp23)
    {"name": "mcp24", "sensor": mcp24, "type": "MCP9808", "location": "glazing", "label": "window"},  # Tso_window(mcp24)
    {"name": "sht1", "sensor": sht1, "type": "SHT31D", "location": "indoor", "label": "air"},     # T_in(sht1), RH_in(sht1)
    {"name": "sht2", "sensor": sht2, "type": "SHT31D", "location": "outdoor", "label": "air"},    # T_out(sht2), RH_out(sht2)
    {"name": "sht3", "sensor": sht3, "type": "SHT31D", "location": "outdoor", "label": "air"},    # T_out(sht3), RH_out(sht3)
    {"name": "sht4", "sensor": sht4, "type": "SHT31D", "location": "outdoor", "label": "air"},    # T_out(sht4), RH_out(sht4)
    {"name": "bme1", "sensor": bme1, "type": "BME280", "location": "indoor", "label": "air"},     # T_in(bme1), RH_in(bme1), P_in(bme1)
    {"name": "bme2", "sensor": bme2, "type": "BME280", "location": "outdoor", "label": "air"},    # T_out(bme2), RH_out(bme2), P_out(bme2)
    {"name": "bme3", "sensor": bme3, "type": "BME280", "location": "outdoor", "label": "air"},    # T_out(bme3), RH_out(bme3), P_out(bme3)
    {"name": "bme4", "sensor": bme4, "type": "BME280", "location": "outdoor", "label": "air"},    # T_out(bme4), RH_out(bme4), P_out(bme4)
    {"name": "bme5", "sensor": bme5, "type": "BME280", "location": "outdoor", "label": "air"},    # T_out(bme5), RH_out(bme5), P_out(bme5)
    {"name": "tsl0", "sensor": tsl0, "type": "TSL2591", "location": "indoor", "label": "light"},   # L_in_win(tsl0)
    {"name": "tsl1", "sensor": tsl1, "type": "TSL2591", "location": "indoor", "label": "light"},   # L_in_r(tsl1)
    {"name": "tsl2", "sensor": tsl2, "type": "TSL2591", "location": "indoor", "label": "light"},   # L_in_l(tsl2)
    {"name": "veml1", "sensor": veml1, "type": "VEML7700", "location": "indoor", "label": "light"},  # L_in_r(veml1)
    {"name": "veml2", "sensor": veml2, "type": "VEML7700", "location": "indoor", "label": "light"},  # L_in_l(veml2)
    {"name": "bh1", "sensor": bh1, "type": "BH1750", "location": "indoor", "label": "light"},        # L_in_r(bh1)
    {"name": "bh2", "sensor": bh2, "type": "BH1750", "location": "indoor", "label": "light"},        # L_in_l(bh2)
    {"name": "sen1", "sensor": sen1, "type": "SEN55", "location": "indoor", "label": "air"},     # PM1.0_in(sen1), PM2.5_in(sen1), PM4.0_in(sen1), PM10_in(sen1), RH_in(sen1), T_in(sen1), VOC_in(sen1), NOx_in(sen1)
    {"name": "sen2", "sensor": sen2, "type": "SEN55", "location": "outdoor", "label": "air"},    # PM1.0_out(sen2), PM2.5_out(sen2), PM4.0_out(sen2), PM10_out(sen2), RH_out(sen2), T_out(sen2), VOC_out(sen2), NOx_out(sen2)
    {"name": "scd1", "sensor": scd1, "type": "SCD30", "location": "indoor", "label": "air"},     # T_in(scd1), RH_in(scd1), C_in(scd1)
    {"name": "scd2", "sensor": scd2, "type": "SCD30", "location": "outdoor", "label": "air"},    # T_out(scd2), RH_out(scd2), C_out(scd2)
    {"name": "sdp1", "sensor": sdp1, "type": "SDP810", "location": "opening", "label": "TC1"},    # dp_r
    {"name": "sdp2", "sensor": sdp2, "type": "SDP810", "location": "opening", "label": "TC1"},    # dp_l
    {"name": "chan1", "sensor": chan1, "type": "HFP01", "location": "glazing", "label": "TC1"},  # HF_vol_r, HF_TC1_r
    {"name": "chan2", "sensor": chan2, "type": "HFP01", "location": "glazing", "label": "TC1"},  # HF_vol_l, HF_TC1_l
    {"name": "chan3", "sensor": chan3, "type": "HFP01", "location": "glazing", "label": "TC2"},  # HF_vol_TC2, HF_TC2_black
    {"name": "chan4", "sensor": chan4, "type": "HFP01", "location": "glazing", "label": "window"}, # HF_vol_window, HF_window
    {"name": "chan5", "sensor": chan5, "type": "OMRON", "location": "velocity", "label": "TC1"}, # V_vol_r, V_r
    {"name": "chan6", "sensor": chan6, "type": "OMRON", "location": "velocity", "label": "TC1"}, # V_vol_l, V_l
    {"name": "chan7", "sensor": chan7, "type": "SEN0232", "location": "indoor", "label": "sound"},  # SL_vol_in, SL_in
    {"name": "chan8", "sensor": chan8, "type": "SEN0232", "location": "outdoor", "label": "sound"}, # SL_vol_out, SL_out
]

#----------------------------------------------------------------------------
while True:
    timestamp = datetime.utcnow().isoformat()

    for config in sensor_configs:
        sensor = config["sensor"]
        sensor_type = config["type"]
        sensor_name = config["name"]
        location = config["location"]
        label = config["label"]

        try:
            if sensor_type == "SEN55":
                data = read_sen_sensor(sensor)
            elif sensor_type == "SDP810":
                data = read_sdp_sensor(sensor)
            else:
                data = read_sensor(sensor, sensor_type)
            
            json_data = format_data(sensor_name, sensor_type, location, label, data)
        
            # Write data to InfluxDB
            write_sensor_data(json_data)
            
            # Prepare data for CSV file
            file_data = [timestamp, sensor_name, sensor_type, location, label]
            file_data.extend([
                data.get("temperature", ""),
                data.get("humidity", ""),
                data.get("pressure", ""),
                data.get("co2", ""),
                data.get("lux", ""),
                data.get("voltage", ""),
                data.get("heat_flux", ""),
                data.get("velocity", ""),
                data.get("sound_level", ""),
                data.get("dp", ""),
                data.get("PM1.0", ""),
                data.get("PM2.5", ""),
                data.get("PM4.0", ""),
                data.get("PM10.0", ""),
                data.get("voc_index", ""),
                data.get("nox_index", "")
            ])
            
            # Write data to CSV file
            write_to_file(file_name, file_data)
            
            print(f"{sensor_name.upper()}: {data}")

        except Exception as e:
            print(f"Failed to read {sensor_name}: {e}")

    time.sleep(10)

