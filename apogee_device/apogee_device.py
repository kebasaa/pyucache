import asyncio
import logging
from bleak import BleakClient, BleakScanner
import datetime
import struct
import csv
import os
import time

# Check until device found or timeout
async def search_devices(timeout=5, silent=False):
    if not silent: print('Searching for devices:')
    start_time = time.time()
    elapsed_time = start_time
    apogee_devices = []
    async with BleakScanner() as scanner:
        try:
            while True:
                # Stop if the searching time is over
                elapsed_time = time.time() - start_time
                if not silent: print('  - Search time: ' + str(int(elapsed_time)) + 's')
                if(elapsed_time > timeout):
                    break
                    
                devices = await asyncio.wait_for(scanner.discover(), timeout=10)
                for device in devices:
                    if device.metadata["manufacturer_data"] and 0x0644 in device.metadata["manufacturer_data"]:
                        # Prepare data to return to calling function
                        manufacturer_data = [(k,v) for k,v in device.metadata['manufacturer_data'].items()][0]
                        company_id      = manufacturer_data[0]
                        advertised_data = manufacturer_data[1]
                        apogee_devices.append({'address': device.address, 'name': device.name, 'rssi': device.rssi,
                                               'company_id': company_id, 'advertised_data': advertised_data})
                        break
                else:
                    continue
                break
        except asyncio.TimeoutError:
            print('  - Device not found, scanning timed out after ' + str(timeout) + 's')
            print('    Try a long press (device should respond with blue blinking)')
        
    return(apogee_devices)

class ucache:
    def __init__(self, address):
        self.address = address
        self.client = BleakClient(address, timeout=5.0)
        self.disconnected = True
        self.device_info = {}
        self.current_dataset = []
        self.base_apogee_service_uuid ='b3e0xxxx-2594-42a1-a5fe-4e660ff2868f'
        self.uuid_time     = '000a'
        self.uuid_logfull  = '000c'
        self.uuid_nb_logs  = '000d'
        self.uuid_lastransfer = '000e'
        self.uuid_sensor   = '0003'
        self.uuid_alias    = '0004'
        self.uuid_live_set = '0005'
        self.uuid_logging  = '0010'
        self.uuid_log_set  = '0012'
        self.uuid_data     = '0013'
        self.uuid_advertise  = '0014'

    async def connect(self):
        try:
            await self.client.connect()
            self.disconnected = False
        except Exception as e:
            logging.error(f'Failed to connect to {self.address}: {e}')
            raise
        pass
            
    async def read_info(self):
        dis_service = '0000180A-0000-1000-8000-00805f9b34fb'
        dis_characteristics = {
            'manufacturer_name': '00002A29-0000-1000-8000-00805f9b34fb',
            'model_number': '00002A24-0000-1000-8000-00805f9b34fb',
            'serial_number': '00002A25-0000-1000-8000-00805f9b34fb',
            'firmware_revision': '00002A26-0000-1000-8000-00805f9b34fb',
            'hardware_revision': '00002A27-0000-1000-8000-00805f9b34fb',
        }
        if self.disconnected:
            raise Exception('Not connected to device')
        try:
            for characteristic in dis_characteristics:
                uuid = dis_characteristics[characteristic]
                value = await self.client.read_gatt_char(uuid)
                value_str = value.decode('utf-8').strip() if value else ''
                self.device_info.update({characteristic: value_str})
            return self.device_info # All the hardware information remains stored in the class
        except Exception as e:
            logging.error(f'Failed to read information from {self.address}: {e}')
            raise
        pass
    
    async def read_battery_level(self):
        battery_service = '0000180F-0000-1000-8000-00805f9b34fb'
        battery_level_uuid = '00002A19-0000-1000-8000-00805f9b34fb'
        try:
            battery_value_raw = await self.client.read_gatt_char(battery_level_uuid)
            battery_level = struct.unpack('<B', battery_value_raw)[0]
            return battery_level
        except Exception as e:
            logging.error(f'Failed to read battery level from {self.address}: {e}')
            raise
        pass
    
    async def read_time(self):
        service_uuid = self.uuid_time
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        try:
            raw_unix_time_value = await self.client.read_gatt_char(current_service)
            current_unix_time = struct.unpack('<I', raw_unix_time_value)[0]
            return current_unix_time
        except Exception as e:
            logging.error(f'Failed to read time from {self.address}: {e}')
            raise
        pass
    
    async def check_and_update_time(self, tolerance=2):
        service_uuid = self.uuid_time
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        # Check time difference. Assume that the computer time is accurate. This may be error-prone!
        dt_computer = datetime.datetime.utcnow()
        dt_computer_unix = int(dt_computer.timestamp())
        dt_device = await self.read_time()
        dt_difference = abs(dt_computer_unix - dt_device)
        
        # Only set the time if there is more than 2s difference,
        # but less than 1 year (to avoid problems, in case the computer time is completely off)
        if((dt_difference > tolerance) & (dt_difference < 31536000)):
            # Convert battery level to bytes
            dt_computer_unix_bytes = struct.pack('<I', dt_computer_unix)
            # Set the time
            try:
                await self.client.write_gatt_char(current_service, dt_computer_unix_bytes)
                return(dt_difference)
            except Exception as e:
                logging.error(f'Failed to set time at {self.address}: {e}')
                return(dt_difference)
        return(dt_difference)
    
    async def read_installed_sensor(self):
        service_uuid = self.uuid_sensor
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        # Based on Table 10 in the API manual. This dictionnary is incomplete but can be completed from the API manual
        sensor_list = {0: {'name': None, 'description': 'No sensor chosen', 'outputs': 0, 'params': None, 'units': None},
                       1: {'name': 'SP-110', 'description': 'Pyranometer', 'outputs': 1, 'params': 'S', 'units': 'W m-2'},
                       2: {'name': 'SP-510', 'description': 'Thermopile Pyranometer', 'outputs': 1, 'params': 'Sin', 'units': 'W m-2'},
                       3: {'name': 'SP-610', 'description': 'Thermopile Pyranometer (Downward)', 'outputs': 1, 'params': 'Sout', 'units': 'W m-2'},
                       4: {'name': 'SQ-110', 'description': 'Quantum (Electric)', 'outputs': 1, 'params': 'PPFD', 'units': 'μmol m-2 s-1'},
                       5: {'name': 'SQ-120', 'description': 'Quantum (Solar)', 'outputs': 1, 'params': 'PPFD_artificial', 'units': 'μmol m-2 s-1'},
                       6: {'name': 'SQ-500', 'description': 'Quantum (Full Spectrum)', 'outputs': 1, 'params': 'PPFD_full', 'units': 'μmol m-2 s-1'},
                       7: {'name': 'SL-510', 'description': 'Pyrgeometer', 'outputs': 1, 'params': 'Lin', 'units': 'W m-2, °C'},
                       8: {'name': 'SL-610', 'description': 'Pyrgeometer (Downward)', 'outputs': 1, 'params': 'Lout', 'units': 'W m-2, °C'},
                       9: {'name': 'SI-100', 'description': 'IR Sensor', 'outputs': 2, 'params': 'Ts', 'units': '°C, °C'},
                       10: {'name': 'SU-200', 'description': 'UV Sensor', 'outputs': 1, 'params': 'UV', 'units': 'W m-2'},
                       11: {'name': 'SE-100', 'description': 'Photometric', 'outputs': 1, 'params': 'Lux', 'units': 'lm m-2'},
                       12: {'name': 'S2-111', 'description': 'NDVI', 'outputs': 2, 'params': 'NDVI', 'units': 'W m-2, W m-2'},
                       13: {'name': 'S2-112', 'description': 'NDVI (Downward)', 'outputs': 2, 'params': 'NDVIout', 'units': 'W m-2, W m-2'},
                       20: {'name': 'SP-700', 'description': 'Albedometer', 'outputs': 2, 'params': 'Sin,Sout', 'units': 'W m-2, W m-2'},
                       26: {'name': '2 Differential', 'description': '2 Differential Measurements', 'outputs': 2, 'params': 'D1,D2', 'units': 'mV, mV'}}
        
        try:
            sensor_id_raw = await self.client.read_gatt_char(current_service)
            sensor_id = struct.unpack('<B', sensor_id_raw)[0]
        except Exception as e:
            logging.error(f'Failed to read time from {self.address}: {e}')
            raise
        
        current_sensor = sensor_list[sensor_id]
        return(current_sensor)
    
    async def read_logging_settings(self, sampling_interval_s, logging_interval_s, start_time=None):
        service_uuid = self.uuid_log_set
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        try:
            data_bytes = await self.client.read_gatt_char(current_service)
            return(set_interval_s)
        except Exception as e:
            logging.error(f'Failed to set logging settings at {self.address}: {e}')
            raise
        # Success, now convert data to dict
        values = struct.unpack('<III', data)
        keys = ['sampling_interval', 'logging_interval', 'starting_time'][:len(values)]
        if(values[2] == 0): # Data logging is disabled, so start_time is 0 (replace with None)
            values[2] = None
        return dict(zip(keys, values))
    
    async def read_logging_status(self):
        service_uuid = self.uuid_logging
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        try:
            logging_status_raw = await self.client.read_gatt_char(current_service)
            logging_status = bool(struct.unpack('<B', logging_status_raw))
            return(logging_status)
        except Exception as e:
            logging.error(f'Failed to read logging status at {self.address}: {e}')
            raise
        pass
    
    async def set_logging_status(self, status=False):
        service_uuid = self.uuid_logging
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        # True is on, False is off
        status_bytes = struct.pack('?', status)
        try:
            await self.client.write_gatt_char(current_service, status_bytes)
        except Exception as e:
            logging.error(f'Failed to set logging status at {self.address}: {e}')
            raise
        pass
    
    async def read_log_full_time(self):
        service_uuid = self.uuid_logfull
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        try:
            full_time_raw = await self.client.read_gatt_char(current_service)
            full_time_unix = struct.unpack('<I', full_time_raw)[0]
            if(full_time_unix > 0):
                return(full_time_unix)
            else: # If it's 0, datalogging is disabled
                return(None)
        except Exception as e:
            logging.error(f'Failed to read time when logging memory will be full, at {self.address}: {e}')
            raise
        pass
    
    async def read_nb_logs_available(self):
        service_uuid = self.uuid_nb_logs
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        try:
            nb_logs_raw = await self.client.read_gatt_char(current_service)
            nb_logs = struct.unpack('<III', nb_logs_raw)
        except Exception as e:
            logging.error(f'Failed to read the number of available logs, at {self.address}: {e}')
            raise
        return(list(nb_logs))
    
    async def read_last_transferred_time(self):
        service_uuid = self.uuid_lastransfer
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        try:
            last_transfer_time_raw = await self.client.read_gatt_char(current_service)
            last_transfer_time_unix = struct.unpack('<I', last_transfer_time_raw)[0]
            if(last_transfer_time_unix > 0):
                return(last_transfer_time_unix)
            else: # If it's 0, the datalog is empty
                return(None)
        except Exception as e:
            logging.error(f'Failed to read time time of last transfer, at {self.address}: {e}')
            raise
        pass
    
    # Write the timestamp of the last transferred row of data. Should be used after transferring data, or to skip some
    async def write_last_transferred_time(self, last_transfer_time_unix):
        # For a set timestamp 0, the oldest timestamp will be found
        service_uuid = self.uuid_lastransfer
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        last_transfer_time_bytes = struct.pack('<I', last_transfer_time_unix)
        try:
            await self.client.write_gatt_char(current_service, last_transfer_time_bytes)
        except Exception as e:
            logging.error(f'Failed to write time time of last transfer, at {self.address}: {e}')
            raise
        pass
    
    async def transfer_data(self, silent=True):
        service_uuid = self.uuid_data
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        # Re-initialise dataset
        self.current_dataset = []
        
        #global received_data
        received_data = []
        async def notifications_callback(sender, data):
            # Check if the data bytes are FF-FF-FF-FF
            if data == b'\xFF\xFF\xFF\xFF':
                # Stop listening to notifications
                await self.client.stop_notify(current_service)
            else:
                # Append the data to the list
                received_data.append(data)
                
        def visualise_progress(percent_progress, previous):
            for dots in range(0, percent_progress-previous):
                print('.', end='')
            if(percent_progress >= 100):
                print('')
            pass
        
        # Read data until everything has been received
        nb_logs = await self.read_nb_logs_available()
        percent_transferred = 0
        previous_percent = 0
        if not silent: print('    ', end='')
        for i in range(1, nb_logs[0]):
            if(len(received_data) == nb_logs[0]):
                break
            # Start listening to notifications
            try:
                await self.client.start_notify(current_service, notifications_callback)
                # Wait until the last data packet is received
                while not received_data:
                    await asyncio.sleep(0.1)
            except:
                try:
                    await self.client.stop_notify(current_service)
                except:
                    break
            # Show transfer progress
            percent_transferred = len(received_data) * 100 / nb_logs[0]
            if not silent: visualise_progress(int(percent_transferred), previous_percent)
            previous_percent = int(percent_transferred)
        
        # Interpret data
        for row in received_data:
            # Unpack the unsigned 32-bit integer
            sampling_time = struct.unpack('<I', row[:4])[0]
            # Calculate the number of remaining bytes
            num_remaining_bytes = len(row) - 4
            # Unpack the signed 32-bit integers
            if num_remaining_bytes % 4 != 0:
                raise ValueError('Invalid data length')
            num_values = num_remaining_bytes // 4
            raw_values = list(struct.unpack('<{}i'.format(num_values), row[4:]))
            values = [x / 10000.0 for x in raw_values] # The original data is stored with an exponent -4
            self.current_dataset.append([sampling_time] + values)
        
        return(self.current_dataset)
    
    async def write_datafile(self, file_path):
        # Get the header
        sensor = await self.read_installed_sensor()
        header_params = 'timestamp,' + sensor['params']
        header_units = ',' + sensor['units']
        header_params = header_params.split(',')
        header_units = header_units.split(',')
        
        # Check if file already exists to determine whether to write header
        write_header = not os.path.isfile(file_path)

        # Open the file in write mode and create a CSV writer
        with open(file_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            # Write header if file is new
            if write_header:
                writer.writerow(header_params)
                writer.writerow(header_units)
            # Write data
            for row in self.current_dataset:
                row[0] = str(datetime.datetime.fromtimestamp(row[0]))
                writer.writerow(row)
        pass
    
    async def set_advertising_frequency(self, freq=0):
        service_uuid = self.uuid_advertise
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        # 0 is upon button press, >0 is every nth time that a log entry is made
        adv_freq_bytes = struct.pack('<B', freq)
        try:
            await self.client.write_gatt_char(current_service, adv_freq_bytes)
        except Exception as e:
            logging.error(f'Failed to set advertising frequency at {self.address}: {e}')
            raise
        pass
        
    async def set_logging_settings(self, sampling_interval_s, logging_interval_s, start_time=None):
        service_uuid = self.uuid_log_set
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        if(logging_interval_s < sampling_interval_s):
            logging.warn('Logging interval must be > sampling interval!')
            logging.warn('   -> Setting logging interval to sampling interval...')
            sampling_interval_s = logging_interval_s
        if(logging_interval_s % sampling_interval_s != 0):
            logging.warn('Logging interval must be dividable by sampling interval!')
            logging_interval_s = int(logging_interval_s / sampling_interval_s) * sampling_interval_s
            logging.warn('   -> Setting logging interval to ' + str(logging_interval_s) + 's...')
        
        # Sampling Interval
        sampling_interval_bytes = struct.pack('<I', sampling_interval_s)
        # Logging Interval (All the values sampled since the last logging event are averaged)
        logging_interval_bytes = struct.pack('<I', logging_interval_s)
        # Start Time
        if(start_time is None):
            # Connect data fields
            settings_bytes = sampling_interval_bytes + logging_interval_bytes
        else: # Start at a specific time
            # Convert to Unix Epoch time
            start_time_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            start_time_unix = int(start_time_dt.timestamp())
            # Convert to bytes
            start_time_bytes = struct.pack('<I', start_time_unix)
            settings_bytes = sampling_interval_bytes + logging_interval_bytes + start_time_bytes
        try:
            await self.client.write_gatt_char(current_service, settings_bytes)
            return([sampling_interval_s, logging_interval_s])
        except Exception as e:
            logging.error(f'Failed to set logging settings at {self.address}: {e}')
            raise
        pass
        
    async def set_live_settings(self, avg_time_s):
        service_uuid = self.uuid_live_set
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        # Convert the value from seconds to units of 0.25 seconds
        avg_time_units = avg_time_s / 0.25
        avg_time_units = min(max(avg_time_units, 0), 127)  # Clamp the value to the valid range
        avg_time_units_bytes = bytes([avg_time_units])
        # Convert back to the set interval (to inform the user)
        set_interval_s = avg_time_units * 0.25
        try:
            await self.client.write_gatt_char(current_service, avg_time_units_bytes)
            return(set_interval_s)
        except Exception as e:
            logging.error(f'Failed to set live averaging time at {self.address}: {e}')
            raise
        pass
        
    async def set_alias(self, alias):
        service_uuid = self.uuid_alias
        current_service = self.base_apogee_service_uuid.replace('xxxx', service_uuid)
        
        alias_bytes = alias.encode('utf-8')
        
        try:
            await self.client.write_gatt_char(current_service, alias_bytes)
        except Exception as e:
            logging.error(f'Failed to set time at {self.address}: {e}')
            raise
        pass
    
    def write_logfile(self, file_path, data, header):
        # Check if file already exists to determine whether to write header
        write_header = not os.path.isfile(file_path)
        
        # Open the file in write mode and create a CSV writer
        with open(file_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            # Write header if file is new
            if write_header:
                writer.writerow(header)
            # Write data
            writer.writerow(data)
        pass
    
    async def disconnect(self):
        if not self.disconnected:
            try:
                await self.client.disconnect()
            except Exception as e:
                logging.error(f'Failed to disconnect from {self.address}: {e}')
                raise
            finally:
                self.disconnected = True
        pass
    
    async def info_routine(self):
        print('  - Connecting to device')
        await self.connect()
    
        print('  - Reading device information:')
        device_info = await self.read_info()
        print('      Type:  ' + device_info['manufacturer_name'] + ' ' + device_info['model_number'])
        print('      Serial:' + device_info['serial_number'])
        print('      Firmware rev.:' + device_info['firmware_revision'])
        print('      Hardware rev.:' + device_info['hardware_revision'])
        
        print('  - Reading battery level:')
        battery_level = await self.read_battery_level()
        print('      Battery Level: ' + str(battery_level) + '%')
    
        print('  - Reading device time:')
        time = await self.read_time()
        print('      Device Time: ' + str(datetime.datetime.fromtimestamp(time)))
        return
    
    async def setup_routine(self, logfile, sampling_interval=10, logging_interval=60, advertising_freq=1, silent=True):
        if not silent: print('  - Connecting to device')
        await self.connect()
    
        if not silent: print('  - Reading device information:')
        device_info = await self.read_info()
        if not silent: print('      Type:  ' + device_info['manufacturer_name'] + ' ' + device_info['model_number'])
        if not silent: print('      Serial:' + device_info['serial_number'])
        if not silent: print('      Firmware rev.:' + device_info['firmware_revision'])
        if not silent: print('      Hardware rev.:' + device_info['hardware_revision'])
    
        if not silent: print('  - Reading battery level:')
        battery_level = await self.read_battery_level()
        if not silent: print('      Level: ' + str(battery_level) + '%')
    
        if not silent: print('  - Reading device time:')
        time = await self.read_time()
        if not silent: print('      Time: ' + str(datetime.datetime.fromtimestamp(time)))
    
        if not silent: print('  - Setting up logging:')
        interval_settings = await self.set_logging_settings(sampling_interval, logging_interval)
        if not silent: print('      Sample every ' + str(interval_settings[0]) + 's')
        if not silent: print('      Log avg every ' + str(interval_settings[1]) + 's')
    
        if not silent: print('  - Setting advertising frequency:')
        if not silent: print('      Advertising every ' + str(sampling_interval) + ' time(s) a log entry is saved')
        await self.set_advertising_frequency(advertising_freq)
        await self.set_logging_status(True)
    
        if not silent: print('  - Checking when memory will be full')
        memory_full_time = await self.read_log_full_time()
        if not silent: print('      Memory will be full on: ' + str(datetime.datetime.fromtimestamp(memory_full_time)))
    
        if not silent: print('  - Disconnecting')
        await self.disconnect()
        
        if not silent: print('  - Writing log to ' + logfile)
        data = [str(datetime.datetime.fromtimestamp(time)),
                device_info['model_number'],
                device_info['serial_number'],
                battery_level,
                str(datetime.datetime.fromtimestamp(memory_full_time)),
                'setup',
                sampling_interval,
                logging_interval,
                advertising_freq,
                '']
        header = ['timestamp',
                  'model',
                  'serial',
                  'battery_level',
                  'memory_full_time',
                  'type'
                  'sampling_interval',
                  'logging_interval',
                  'advertising_freq',
                  'time_difference']
        self.write_logfile(logfile, data, header)
        return
    
    async def download_routine(self, datafile, logfile, from_timestamp=None, silent=True):
        if not silent: print('  - Connecting to device')
        try:
            await self.connect()
        except:
            return
    
        if not silent: print('  - Reading device information:')
        device_info = await self.read_info()
        if not silent: print('      Type:  ', device_info['manufacturer_name'], device_info['model_number'])
        if not silent: print('      Serial:', device_info['serial_number'])
        if not silent: print('      Firmware rev.:', device_info['firmware_revision'])
        if not silent: print('      Hardware rev.:', device_info['hardware_revision'])
    
        if not silent: print('  - Reading battery level:')
        battery_level = await self.read_battery_level()
        if not silent: print('      Level: ' + str(battery_level) + '%')
    
        if not silent: print('  - Reading device time:')
        time = await self.read_time()
        if not silent: print('      Device Time: ' + str(datetime.datetime.fromtimestamp(time)))
    
        # Check if device is logging
        # If false don't even bother downloading
        if not silent: print('  - Checking if device is logging: ', end='')
        logging = await self.read_logging_status()
        if(logging == False):
            if not silent: print('No. Abort')
            await self.disconnect()
            return
        if not silent: print('Yes')
    
        # To download data from a specific timestamp
        if(from_timestamp is not None):
            if(from_timestamp == 'all'):
                if not silent: print('  - Setting transfer time to download all')
                transfer_time_unix = int(0)
            else:
                if not silent: print('  - Setting transfer time: ', end='')
                transfer_time = datetime.datetime.strptime(from_timestamp, '%Y-%m-%d %H:%M')
                transfer_time_unix = int(transfer_time.timestamp())
                if not silent: print(datetime.datetime.fromtimestamp(transfer_time_unix))
            await self.write_last_transferred_time(transfer_time_unix)
            pass
    
        # Read number of logs to be downloaded, and timestamp of last downloaded one
        if not silent: print('  - Checking number of logs:')
        min_logs = 5 # Minimum log number for downloads
        nb_logs = await self.read_nb_logs_available()
        last_transferred_time = await self.read_last_transferred_time()
        if not silent: print('      ' + str(nb_logs[0]) + ' logs, last transferred log from ' + \
                             str(datetime.datetime.fromtimestamp(last_transferred_time)))
        if(nb_logs[0] < min_logs):
            if not silent: print('      Less than ' + str(min_logs) + ' logs available, do not download')
            await self.disconnect()
            return
    
        # Download data, is stored in self.current_dataset
        if not silent: print('  - Downloading data')
        await self.transfer_data(silent=silent)
    
        # Fix time if necessary, comparing to computer time
        tolerance = 2 # If <2s difference between the computer and the device, no update done
        if not silent: print('  - Checking and updating time')
        time_difference = await self.check_and_update_time(tolerance)
        if(time_difference <= tolerance):
            if not silent: print('      Time not updated. Difference: ' + str(time_difference) + 's')
        else:
            if not silent: print('      Time was updated. Difference: ' + str(time_difference) + 's')
        
        if not silent: print('  - Checking when memory will be full')
        memory_full_time = await self.read_log_full_time()
        if not silent: print('      Memory will be full on: ' + str(datetime.datetime.fromtimestamp(memory_full_time)))
    
        # Write data to file
        if not silent: print('  - Writing data to ' + datafile)
        await self.write_datafile('./data.csv')
    
        if not silent: print('  - Writing log to ' + logfile)
        data = [str(datetime.datetime.fromtimestamp(time)),
                device_info['model_number'],
                device_info['serial_number'],
                battery_level,
                str(datetime.datetime.fromtimestamp(memory_full_time)),
                'data transfer',
                '',
                '',
                '',
                time_difference]
        header = ['timestamp',
                  'model',
                  'serial',
                  'battery_level',
                  'memory_full_time',
                  'type'
                  'sampling_interval',
                  'logging_interval',
                  'advertising_freq',
                  'time_difference']
        self.write_logfile(logfile, data, header)
    
        if not silent: print('  - Disconnecting')
        await self.disconnect()
        
        return
        