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

from urllib import request as url_request
import asyncio
import threading

DEFAULT_TIMEOUT = 20.0
DEFAULT_LIMIT = 10000000

class Response:
    pass

def async_fetch(req, timeout=None, limit=None, loop=None):
    assert loop is not None
    assert isinstance(req, url_request.Request)
    
    if limit is None:
        limit = DEFAULT_LIMIT
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    
    future = asyncio.Future(loop=loop)
    
    def set_result(result):
        if not future.cancelled():
            future.set_result(result)
    
    def set_exception(e):
        if not future.cancelled():
            future.set_exception(e)
    
    def async_fetch_thread_func():
        try:
            opener = url_request.build_opener()
            opener_res = opener.open(req, timeout=timeout)
            
            response = Response()
            response.code = opener_res.getcode()
            response.url = opener_res.geturl()
            response.body = opener_res.read(limit)
        except Exception as e:
            loop.call_soon_threadsafe(set_exception, e)
        else:
            loop.call_soon_threadsafe(set_result, response)
    
    threading.Thread(target=async_fetch_thread_func, daemon=True).start()
    
    return future
