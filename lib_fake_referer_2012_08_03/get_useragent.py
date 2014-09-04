# -*- mode: python; coding: utf-8 -*-
#
# Copyright (c) 2014 Andrej Antonov <polymorphm@gmail.com>
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

from urllib import parse as url_parse
from urllib import request as url_request
import json

USERAGENT_LIST_URL = 'https://getuseragent.blogspot.com/2014/03/getuseragent.html'
REQUEST_TIMEOUT = 60.0
REQUEST_READ_LIMIT = 10000000

def get_useragent_list():
    marker_prefix = 'USERAGENT_DATA'
    start_marker = '{}_START'.format(marker_prefix)
    stop_marker = '{}_STOP'.format(marker_prefix)
    
    opener = url_request.build_opener()
    opener_res = opener.open(
            url_request.Request(USERAGENT_LIST_URL),
            timeout=REQUEST_TIMEOUT,
            )
    raw_data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    start_pos = raw_data.find(start_marker)
    stop_pos = raw_data.find(stop_marker)
    
    if start_pos == -1 or stop_pos == -1:
        raise ValueError(
                'not found: start_marker or stop_marker',
                )
    
    useragent_raw_data = raw_data[start_pos+len(start_marker):stop_pos]
    useragent_data = json.loads(useragent_raw_data)
    
    if not isinstance(useragent_data, (tuple, list)):
        raise ValueError(
                'useragent_data is not isinstance of tuple-or-list',
                )
    
    useragent_list = []
    
    for useragent_item in useragent_data:
        if not isinstance(useragent_item, str) or \
                '\n' in useragent_item or '\r' in useragent_item:
            continue
        
        useragent_list.append(useragent_item)
    
    return tuple(useragent_list)
