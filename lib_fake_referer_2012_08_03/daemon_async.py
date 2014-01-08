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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.



assert str is not str
assert str is bytes

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
            except Exception:
                exc = sys.exc_info()
            
            ioloop.IOLoop.instance().add_callback(
                    functools.partial(callback, result, exc))
        
        thread = threading.Thread(target=daemon)
        thread.daemon = True
        thread.start()
    
    return wrapper
