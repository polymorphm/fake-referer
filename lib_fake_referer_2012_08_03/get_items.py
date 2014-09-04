# -*- mode: python; coding: utf-8 -*-
#
# Copyright (c) 2012, 2014 Andrej Antonov <polymorphm@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

assert str is not bytes

import os, os.path, itertools, random

class NotFoundError(IOError):
    pass

def file_items_open(path):
    assert isinstance(path, str)
    
    with open(path, 'rb') as fd:
        for line in fd:
            if not line:
                continue
            
            item = line.decode('utf-8', 'replace').strip()
            
            if not item:
                continue
            
            yield item

def dir_items_open(path):
    assert isinstance(path, str)
    
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        
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
