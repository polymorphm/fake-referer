# -*- mode: python; coding: utf-8 -*-
#
# Copyright (c) 2011, 2012, 2014 Andrej Antonov <polymorphm@gmail.com>
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

import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, json
from .daemon_async import daemon_async

DEFAULT_TIMEOUT = 20.0
DEFAULT_LIMIT = 10000000

class Response:
    pass

@daemon_async
def async_fetch(url, data=None, header_list=None, proxies=None,
        limit=None, timeout=None, use_json=None):
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data)
    if limit is None:
        limit = DEFAULT_LIMIT
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    if use_json is None:
        use_json = False
    
    build_opener_args = []
    if proxies is not None:
        build_opener_args.append(
                urllib.request.ProxyHandler(proxies=proxies))
    
    opener = urllib.request.build_opener(*build_opener_args)
    
    if header_list is not None:
        opener.addheaders = tuple(header_list)
    
    f = opener.open(url, data=data, timeout=timeout)
    
    response = Response()
    response.code = f.getcode()
    response.body = f.read(limit)
    
    if use_json:
        response = json.loads(response.body)
    
    return response
