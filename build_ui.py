# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Wrote', path)
