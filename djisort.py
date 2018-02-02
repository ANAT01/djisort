#!/usr/bin/python
# -*- coding: utf-8 -*-

from  extract_exif_data import ImageMetaData
from remove_empty_folders import removeEmptyFolders

import os
from datetime import datetime, timedelta
import http.client
import json
import re

# for dict sort
from collections import OrderedDict

# Копировани, перемещение файлов
import errno
import shutil

# md5sum
import hashlib

# var_dump
from pprint import pprint


def md5sum(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(2 ** 20), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# считаем чанки в папке
def chunk_count(path, pattern='chunk*'):
    count = []
    if not os.path.isdir(path):
        return int(0)
    for entry in os.listdir(path):
        if os.path.isdir(os.path.join(path, entry)):
            if re.match(pattern, entry):
                count.append(entry)
    return len(count)


fpool = {}

#src = u"old/"
src = u"/media/anatoly/d52e0ff2-ca09-454e-984d-cd4e9d16f850/djiaramaki/old"
dst = u"/media/anatoly/d52e0ff2-ca09-454e-984d-cd4e9d16f850/djiaramaki/"
#dst = u"new/"

# TODO: Проходимся по директориям и получаем все файлы
for path, subdirs, files in os.walk(src):
    for name in files:
        fullpath = os.path.join(path, name)
        if fullpath.lower().endswith(('.jpeg', '.jpg')):
            exif = ImageMetaData(fullpath)
            exif_data = exif.get_exif_data()
            img_latlon = exif.get_lat_lon()
            img_datetime = datetime.strptime(exif_data['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')

            #img_date = img_datetime.strftime('%Y-%m-%d')
            fpool[img_datetime] = {
                'src': os.path.abspath(fullpath),
                'lat': img_latlon[0],
                'lon': img_latlon[1]
            }

            # csvfile2.write('{:d},{:.2f},{:.2f}'.format(latlon[0], latlon[1]) + "\n")
            # csvfile3.write('{:.3f},{:.3f}'.format(latlon[0], latlon[1]) + "\n")
            # csvfile4.write('{:.4f},{:.4f}'.format(latlon[0], latlon[1]) + "\n")



# TODO: Строим чанки
fpool = OrderedDict(sorted(fpool.items(), key=lambda t: t[0]))

chunks = {}
counter_chunk = 0
counter_date = datetime.min

for img_datetime, props in fpool.items():
    #Изменение нумерации чанка если разрыв времени больше 2-х минут
    if img_datetime > counter_date + timedelta(minutes=2):
        counter_chunk += 1
    counter_date = img_datetime

    #Если нет чанка, то создаем чанк
    if not chunks.get(counter_chunk):
        chunks[counter_chunk] = {}
        chunks[counter_chunk]['fpool'] = []
        chunks[counter_chunk]['date'] = os.path.join(img_datetime.strftime('%Y-%m-%d'))
        chunks[counter_chunk]['centroid'] = {'lat': float(), 'lon': float()}

    #Вычисляем центр съемки
    if chunks[counter_chunk]['centroid']['lat'] > 0:
        chunks[counter_chunk]['centroid']['lat'] = (chunks[counter_chunk]['centroid']['lat'] + props['lat']) / 2
    else:
        chunks[counter_chunk]['centroid']['lat'] = props['lat']
    if chunks[counter_chunk]['centroid']['lon'] > 0:
        chunks[counter_chunk]['centroid']['lon'] = (chunks[counter_chunk]['centroid']['lon'] + props['lon']) / 2
    else:
        chunks[counter_chunk]['centroid']['lon'] = props['lon']

    chunks[counter_chunk]['fpool'].append({
        'src': props['src'],
        'date': os.path.join(img_datetime.strftime('%Y-%m-%d')),
        'chunk': str(os.path.join("chunk" + str('{:02d}'.format(counter_chunk)))),
        'filename': os.path.join(img_datetime.strftime('%Y%m%d_%H%M%S') + ".jpg"),
        'lat': props['lat'],
        'lon': props['lon'],
    })


#TODO: Рассовывыем мо местам
for key, chunk in chunks.items():
    print("Chunk " + str(key), chunk['centroid']['lat'], chunk['centroid']['lon'])

    # Настраиваем http клиент
    #conn = http.client.HTTPSConnection("nominatim.openstreetmap.org")
    # osm geocoder '/reverse?format=json&lat={:.4f}&lon={:.4f}&zoom=13&addressdetails=1'

    # yandex geocoder
    conn = http.client.HTTPSConnection("geocode-maps.yandex.ru")
    payload = ""
    headers = {'user-agent': "Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail geocoder/0.0.1"}
    conn.request("GET",
                 '/1.x/?format=json&geocode={:.4f},{:.4f}&kind=locality&sco=latlong&spn=0.01,0.01'.format(
                     chunk['centroid']['lat'], chunk['centroid']['lon']),
                 payload,
                 headers
    )

    res = conn.getresponse()
    data = res.read()
    #print(data.decode("utf-8"))
    geocode = json.loads(data.decode("utf-8"))
    conn.close()

    print(geocode)

    try:
        subAdministrativeArea = \
            geocode['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                'GeocoderMetaData'][
                'AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['SubAdministrativeAreaName']
        locality = \
            geocode['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                'GeocoderMetaData'][
                'AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName']
    except IndexError as e:
        pprint(e)
        print('Пропушено так как не нашел населенный пункт для точки')
        continue

    csvfilepath = ''
    pprint(chunk['date'])
    chunknum = 1 + int(chunk_count(os.path.join(dst, subAdministrativeArea, locality, chunk['date'])))
    print(chunknum)
    for index, fpool in enumerate(chunk['fpool']):
        # print(index, fpool['src'])
        src = fpool['src']

        filepath = os.path.join(subAdministrativeArea, locality, fpool['date'],
                                "chunk" + str('{:02d}').format(chunknum),
                                fpool['filename'])
        output = os.path.join(dst, filepath)

        if not os.path.isfile(output):
            try:
                shutil.move(src, output)
            except IOError as e:
                # ENOENT(2): file does not exist, raised also on missing dest parent dir
                if e.errno != errno.ENOENT:
                    raise
                    # try creating parent directories
                os.makedirs(os.path.dirname(output))
                shutil.move(src, output)
            if csvfilepath == '':
                csvfilepath = os.path.join(dst, subAdministrativeArea, locality, fpool['date'],
                                           "chunk" + str('{:02d}').format(chunknum) + '.csv')
                csvfile = open(csvfilepath, 'w')
            csvfile.write('{:f},{:f},{}'.format(fpool['lat'], fpool['lon'],
                                                ','.join(str(filepath.encode('utf-8')).split('/'))) + "\n")

            #master csv
            mastercsv = open(os.path.join(dst, 'master.csv'), 'a')
            mastercsv.write('{:f},{:f},{}'.format(fpool['lat'], fpool['lon'],
                                                  ','.join(str(filepath.encode('utf-8')).split('/'))) + "\n")

        else:
            print("Already exist!!!!!")
            if md5sum(output) == md5sum(src):
                print("EQUIVALENTS")
                os.remove(src)

# Удаляем пустые директории
# TODO Сделать рекурсивное удаление снизу
removeEmptyFolders(src)







