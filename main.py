import glob
import re
import os
import xml.etree.ElementTree as ET
import csv
from datetime import datetime
import time


class Files:
    name = ''
    read = None
    write = None

    def __init__(self, filename, f):
        print(filename, '.', f)
        self.name = filename
        if 'csv' in f:
            self.read = CSV(filename)
            self.write = XML(filename)
        elif 'xml' in f:
            self.read = XML(filename)
            self.write = CSV(filename)
        else:
            print(f'Файл формата .{f} не определен.')

    def append_dir(self):
        dir_name = 'Сконвертировано'
        if dir_name not in os.listdir():
            os.mkdir(dir_name)


class CSV(Files):

    def __init__(self, filename):
        self.name = filename

    def read_file(self):
        data = {}
        with open(f'{self.name}.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        sensors_count = int(len(rows[0])/2)
        if sensors_count == 0:
            raise Exception('WialonError')
        for i in range(sensors_count):
            data[i] = {}
            for row in rows:
                if len(row) != 0:
                    data[i][row[i*2]] = row[i*2+1].replace(' ', '')
        return data

    def read_file_wialon(self):
        data = {}
        with open(f'{self.name}.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        data[0] = {}
        for row in rows:
            parts = row[0].split(';')
            data[0][parts[0]] = int(parts[1])
        return data

    def save_file(self, data):
        self.append_dir()
        sensors = [[[str(k), str(sensor[k])] for k in sensor.keys()] for sensor in data.values()]
        for sensor in sensors:
            with open(f'Сконвертировано/{self.name} ({sensors.index(sensor)}).csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(sensor)


class XML(Files):

    def __init__(self, filename):
        self.name = filename

    def read_file(self):
        data = {}
        with open(f'{self.name}.xml') as file:
            rows = file.readlines()
        i = -1
        for row in rows:
            if 'sensor number' in row:
                i += 1
                data[i] = {}
            if 'value code' in row:
                parts = re.split('<|>|"', row)
                data[i][parts[2]] = int(int(parts[4])/10)
        return data

    def save_file(self, data):
        self.append_dir()
        current_time = datetime.utcfromtimestamp(int(time.time()) + 10800).strftime("%Y-%m-%d")
        root = ET.Element('vehicle')
        veh_id = ET.SubElement(root, 'id')
        veh_id.text = '1'
        calibrationDate = ET.SubElement(root, 'calibrationDate')
        calibrationDate.text = current_time
        approximationBufferLength = ET.SubElement(root, 'approximationBufferLength')
        approximationBufferLength.text = '70'
        fillThreshold = ET.SubElement(root, 'fillThreshold')
        fillThreshold.text = '190'
        drainThreshold = ET.SubElement(root, 'drainThreshold')
        drainThreshold.text = '190'
        dutyConsumption = ET.SubElement(root, 'dutyConsumption')
        dutyConsumption.text = '0'
        roughFilterLength = ET.SubElement(root, 'roughFilterLength')
        roughFilterLength.text = '15'
        fineFilterLength = ET.SubElement(root, 'fineFilterLength')
        fineFilterLength.text = '10'
        for key in data.keys():
            sensor = ET.SubElement(root, 'sensor')
            sensor.set('number', str(key))
            for row in data[key].keys():
                value = ET.SubElement(sensor, 'value')
                value.set('code', str(row))
                value.text = str(int(data[key][row])*10)
            tankNmb = ET.SubElement(sensor, 'tankNmb')
            tankNmb.text = '1'
        tree = ET.ElementTree(root)
        my_file = open(f'Сконвертировано/{self.name}.xml', 'wb')
        tree.write(my_file, encoding='UTF-8', xml_declaration=True, method='xml')


def main():
    files = glob.glob('*')
    for file in files:
        ob_file = None
        if '.' in file and '.exe' not in file:
            parts = file.split('.')
            file_format = parts.pop(-1)
            name = file[:-4]
            ob_file = Files(name, file_format)
        try:
            if ob_file is not None:
                data = ob_file.read.read_file()
                ob_file.write.save_file(data)
                print(f'Файл "{file}" сконвертирован.')
        except Exception as ex_:
            if ex_.args[0] == 'WialonError':
                data = ob_file.read.read_file_wialon()
                ob_file.write.save_file(data)
            elif 'NoneType' in ex_.args[0]:
                pass
            else:
                print(ex_)
                input('Предоставьте ифнормацию Александру Тимофееву')


main()