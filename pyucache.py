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
        company_id = int.from_bytes(data[0:2], byteorder='little')
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