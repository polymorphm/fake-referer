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

from __future__ import absolute_import

assert unicode is not str
assert str is bytes

import functools
from tornado import ioloop, stack_context, gen
from zope.interface import implements
from twisted.internet import reactor
from twisted.python.failure import Failure
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.interfaces import IProtocol

DEFAULT_TIMEOUT = 20.0
DEFAULT_LIMIT = 10000000

class Response:
    pass

class TwDeliverBody(object):
    implements(IProtocol)
    
    def __init__(self, response, finished, limit=None):
        if limit is None:
            limit = DEFAULT_LIMIT
        
        self._response = response
        self._finished = finished
        self._remaining = limit
        self._response.body = bytes()
        self._transport = None
    
    def dataReceived(self, data):
        if self._remaining:
            used_data = data[:self._remaining]
            self._response.body += used_data
            self._remaining -= len(used_data)
        
        if not self._remaining:
            if self._transport is not None:
                transport.stopProducing()
    
    def connectionLost(self, reason):
        self._finished.callback(self._response)
    
    def makeConnection(self, transport):
        self._transport = transport
    
    def connectionMade():
        pass

def tw_async_fetch(url, data=None, header_map=None, limit=None, timeout=None,
        use_loop=None, callback=None):
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    if use_loop is None:
        use_loop = False
    
    if isinstance(url, unicode):
        url = url.encode('utf-8', 'replace')
    
    if data is not None:
        method = 'POST'
        raise NotImplementedError('post requests not implemented yet')
    else:
        method = 'GET'
    
    if header_map is not None:
        headers = Headers(header_map)
    else:
        headers = None
    
    agent = Agent(reactor, connectTimeout=timeout)
    d = agent.request(method, url, headers=Headers(header_map))
    
    def cbRequest(response):
        resp = Response()
        resp.code = response.code
        
        finished = Deferred()
        response.deliverBody(TwDeliverBody(resp, finished, limit=limit))
        return finished
    d.addCallback(cbRequest)
    
    if use_loop:
        def cbLoopFinally(arg):
            response = None
            exc = None
            
            if isinstance(arg, Failure):
                exc = arg.type, arg.value, arg.getTracebackObject()
            else:
                response = arg
            
            if callback is not None:
                ioloop.IOLoop.instance().add_callback(functools.partial(
                        callback,
                        response,
                        exc,
                        ))
        d.addBoth(cbLoopFinally)

@gen.engine
def async_fetch(url, data=None, header_map=None, use_json=None,
        limit=None, timeout=None, callback=None):
    callback = stack_context.wrap(callback)
    
    if isinstance(data, dict):
        data = urllib.urlencode(data)
    if use_json is None:
        use_json = False
    
    response, exc = (yield gen.Task(
            reactor.callFromThread,
            tw_async_fetch,
            url,
            data=data,
            header_map=header_map,
            limit=limit,
            timeout=timeout,
            use_loop=True,
            ))[0]
    
    if use_json:
        response = json.loads(response.body)
    
    if callback is not None:
        callback(response, exc)
