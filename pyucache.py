import bluetooth.ble as ble
import codecs

# Define the Bluetooth Company Identifier for SIG
SIG_COMPANY_ID = 0x0644

# Define a function to print the data of a discovered BLE device
def print_device_data(addr, name, company_id, alias):
    print("Address: ", addr)
    print("Name: ", name)
    print("Company ID: ", hex(company_id))
    print("Alias: ", codecs.decode(alias, 'hex').decode('utf-8'))

# Scan for nearby BLE devices
devices = ble.discover_devices(duration=10, flush_cache=True, lookup_names=True)

# Loop through the discovered devices and try to connect to the device with the SIG company ID
for addr, name in devices:
    try:
        # Get the advertising data of the device
        data = ble.read_advertisement_data(addr, ble.ADV_TYPE_NAME_COMPLETE)
        # Extract the company ID and device alias from the advertising data
        company_id = int.from_bytes(data[0:2][::-1], byteorder='little')
        alias = data[2:].hex()
        if company_id == SIG_COMPANY_ID:
            print("Found SIG device with address: ", addr)
            print_device_data(addr, name, company_id, alias)
            # Connect to the device
            sock = ble.BluetoothBLESocket(ble.RFCOMM)
            sock.connect((addr, 1))
            print("Connected to device with address: ", addr)
            # Do something with the connected device
            # ...
            # Close the connection
            sock.close()
            print("Disconnected from device with address: ", addr)
    except:
        print("Failed to connect to device with address: ", addr)
        
# Further tools
'''
This function takes a socket sock as its input parameter and returns a dictionary with the values of the DIS characteristics. You can call this function by passing in the socket returned by ble.connect(). For example:

sock = ble.connect("AA:BB:CC:DD:EE:FF")
dis_characteristics = read_dis_characteristics(sock)
print(dis_characteristics)

Access specific characteristics like this:
print(dis_characteristics["manufacturer_name"])
'''
def read_dis_characteristics(sock):
    # Get the handles for the DIS characteristics
    dis_service_uuid = ble.UUID("0000180a-0000-1000-8000-00805f9b34fb")
    handles = ble.get_service_handles(sock, dis_service_uuid)

    # Read the Manufacturer Name characteristic
    manufacturer_name_uuid = ble.UUID("00002a29-0000-1000-8000-00805f9b34fb")
    manufacturer_name = ble.read_characteristic(sock, handles, manufacturer_name_uuid)

    # Read the Model Number characteristic
    model_number_uuid = ble.UUID("00002a24-0000-1000-8000-00805f9b34fb")
    model_number = ble.read_characteristic(sock, handles, model_number_uuid)

    # Read the Serial Number characteristic
    serial_number_uuid = ble.UUID("00002a25-0000-1000-8000-00805f9b34fb")
    serial_number = ble.read_characteristic(sock, handles, serial_number_uuid)

    # Read the Firmware Revision characteristic
    firmware_revision_uuid = ble.UUID("00002a26-0000-1000-8000-00805f9b34fb")
    firmware_revision = ble.read_characteristic(sock, handles, firmware_revision_uuid)

    # Read the Hardware Revision characteristic
    hardware_revision_uuid = ble.UUID("00002a27-0000-1000-8000-00805f9b34fb")
    hardware_revision = ble.read_characteristic(sock, handles, hardware_revision_uuid)

    # Create a dictionary with the characteristic values
    characteristics = {
        "manufacturer_name": manufacturer_name.decode(),
        "model_number": model_number.decode(),
        "serial_number": serial_number.decode(),
        "firmware_revision": firmware_revision.decode(),
        "hardware_revision": hardware_revision.decode()
    }

    return characteristics

'''
Read the Battery Level characteristic from a Bluetooth LE device and returns its value as a percentage
'''
def read_battery_level(sock):
    # Get the handle for the Battery Level characteristic
    battery_service_uuid = ble.UUID("0000180f-0000-1000-8000-00805f9b34fb")
    handles = ble.get_service_handles(sock, battery_service_uuid)

    battery_level_uuid = ble.UUID("00002a19-0000-1000-8000-00805f9b34fb")
    battery_level = ble.read_characteristic(sock, handles, battery_level_uuid)

    # Return the battery level value as a percentage
    return ord(battery_level)
    
'''
The Live Data Control Characteristic controls averaging time of the Live Data Characteristic. Valid values are 0-127 in units of 0.25 seconds. A value of 0 is interpreted as no averaging with data calculated from a single ADC sample.
'''
def set_averaging_time_apogee(sock, value_sec):
    # Convert the value from seconds to units of 0.25 seconds
    time_units = int(value_sec / 0.25)
    time_units = min(max(time_units, 0), 127)  # Clamp the value to the valid range

    # Write the value to the characteristic
    base_uuid = ble.UUID("b3e00000-2594-42a1-a5fe-4e660ff2868f")
    service_uuid = ble.UUID("0005", base_uuid)
    handle = ble.get_characteristic_handle(sock, service_uuid)
    ble.write_command(sock, handle, time_units.to_bytes(1, 'little'))
    pass
    
'''
Check and set time
'''
import time
import struct
from datetime import datetime
from ntplib import NTPClient
from bluepy.btle import Peripheral, UUID

def set_current_time(ntp_server='pool.ntp.org', timeout=5):
    # Define the UUIDs for the device and service
    base_uuid = UUID("b3e0xxxx-2594-2a1a-5fe4-e660ff2868f")
    service_uuid = UUID("000a")

    # Create a connection to the device
    device = Peripheral('AA:BB:CC:DD:EE:FF')
    service = device.getServiceByUUID(UUID(str(base_uuid).replace('xxxx', str(service_uuid))))

    # Read the current Unix Epoch time from the device
    characteristic = service.getCharacteristics(UUID("0002"))[0]
    device_time = struct.unpack("<I", characteristic.read())[0]

    # Read the current time from the NTP server
    ntp_client = NTPClient()
    ntp_response = ntp_client.request(ntp_server, version=3)
    ntp_time = int(ntp_response.tx_time)

    # Calculate the difference between the device time and the NTP time
    time_diff = abs(device_time - ntp_time)

    # If the difference is greater than 3 seconds, update the device time
    if time_diff > 3:
        # Convert the NTP time to an unsigned 32-bit integer
        ntp_time_bytes = struct.pack("<I", ntp_time)

        # Write the NTP time to the device
        characteristic = service.getCharacteristics(UUID("0001"))[0]
        characteristic.write(ntp_time_bytes, withResponse=True)

    # Disconnect from the device
    device.disconnect()

    # Return the current Unix Epoch time
    return datetime.fromtimestamp(device_time).strftime("%Y-%m-%d %H:%M:%S")