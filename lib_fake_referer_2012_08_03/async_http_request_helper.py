# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2011, 2012, 2014 Andrej A Antonov <polymorphm@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
