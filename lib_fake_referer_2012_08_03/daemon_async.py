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

import sys, functools, threading
from tornado import ioloop, stack_context

def daemon_async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        callback = kwargs.pop('callback', None)
        callback = stack_context.wrap(callback)
        
        def daemon():
            result = None
            exc = None
            
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                exc = type(e), str(e)
            
            ioloop.IOLoop.instance().add_callback(
                    functools.partial(callback, result, exc))
        
        thread = threading.Thread(target=daemon)
        thread.daemon = True
        thread.start()
    
    return wrapper
