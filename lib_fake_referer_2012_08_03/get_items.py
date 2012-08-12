# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2012 Andrej A Antonov <polymorphm@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

assert unicode is not str
assert str is bytes

import sys, os, os.path, itertools, random

class NotFoundError(IOError):
    pass

def file_items_open(path):
    assert isinstance(path, unicode)
    
    with open(path, 'rb') as fd:
        for line in fd:
            if not line:
                continue
            
            item = line.decode('utf-8', 'replace').strip()
            
            if not item:
                continue
            
            yield item

def dir_items_open(path):
    assert isinstance(path, unicode)
    
    for name in os.listdir(path):
        uname = name.decode(sys.getfilesystemencoding(), 'replace')
        
        file_path = os.path.join(path, uname)
        
        if not file_path.endswith('.txt'):
            continue
        
        with open(file_path, 'rb') as fd:
            data = fd.read()
            
            if not data:
                continue
            
            item = data.decode('utf-8', 'replace').strip()
            
            if not item:
                continue
            
            yield item

def items_open(path):
    if os.path.isdir(path):
        return dir_items_open(path)
    
    if os.path.isfile(path):
        return file_items_open(path)
    
    d_path = path + '.d'
    txt_path = path + '.txt'
    
    if os.path.isdir(d_path):
        return dir_items_open(d_path)
    
    if os.path.isfile(txt_path):
        return file_items_open(txt_path)
    
    raise NotFoundError('No such file or directory: ' + repr(path))

def get_finite_items(path):
    return items_open(path)

def get_infinite_items(path):
    for item in itertools.cycle(items_open(path)):
        yield item

def get_random_finite_items(path):
    items = []
    
    for item in items_open(path):
        items.append(item)
    
    random.shuffle(items)
    
    for item in items:
        yield item

def get_random_infinite_items(path):
    items = []
    
    for item in items_open(path):
        items.append(item)
    
    if not items:
        return
    
    while True:
        random.shuffle(items)
        
        for item in items:
            yield item
