import bluetooth.ble as ble

# Define the Bluetooth Company Identifier for SIG
SIG_COMPANY_ID = 0x0644

# Define a function to print the data of a discovered BLE device
def print_device_data(addr, name, data):
    print("Address: ", addr)
    print("Name: ", name)
    print("Data: ", data)

# Scan for nearby BLE devices
devices = ble.discover_devices(duration=10, flush_cache=True, lookup_names=True)

# Loop through the discovered devices and try to connect to the device with the SIG company ID
for addr, name in devices:
    data = ble.find_service_name(addr, company_id=SIG_COMPANY_ID)
    if data:
        print("Found SIG device with address: ", addr)
        print_device_data(addr, name, data)
        # Connect to the device
        try:
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