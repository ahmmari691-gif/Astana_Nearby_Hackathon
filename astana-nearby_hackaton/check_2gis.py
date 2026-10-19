#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check a 2GIS Places key without printing or saving it."""
import getpass
from sources import check_2gis_key
if __name__=='__main__':
    key=getpass.getpass('Вставьте ключ 2ГИС (ввод скрыт): ').strip()
    try:check_2gis_key(key)
    except RuntimeError as error:
        print(str(error));raise SystemExit(1)
    print('Ключ принят: доступ к Places API работает.')
