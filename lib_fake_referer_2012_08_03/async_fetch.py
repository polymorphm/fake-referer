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

import functools, threading
from tornado import ioloop, stack_context, gen
from zope import interface
from twisted.internet import reactor, defer, interfaces
from twisted.python import failure
from twisted.web import client, http_headers

DEFAULT_TIMEOUT = 20.0
DEFAULT_LIMIT = 10000000

_local = threading.local()

class Response:
    pass

class TwDeliverBody(object):
    interface.implements(interfaces.IProtocol)
    
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
        self._transport = None
        self._finished.callback(self._response)
    
    def makeConnection(self, transport):
        self._transport = transport
    
    def connectionMade(self):
        pass

def tw_get_pool():
    try:
        pool = _local.pool
    except AttributeError:
        pool = _local.pool = client.HTTPConnectionPool(reactor)
    
    return pool

def tw_get_agent():
    try:
        agent = _local.agent
    except AttributeError:
        agent = _local.agent = client.Agent(
                reactor,
                connectTimeout=DEFAULT_TIMEOUT,
                pool=tw_get_pool(),
                )
    
    return agent

def tw_async_fetch(url, data=None, header_map=None, limit=None,
        use_loop=None, callback=None):
    if use_loop is None:
        use_loop = False
    
    if isinstance(url, unicode):
        url = url.encode('utf-8', 'replace')
    
    if data is not None:
        method = 'POST'
        raise NotImplementedError('post requests not implemented yet')
    else:
        method = 'GET'
    
    init_header_map = {
        'User-Agent': ['Twisted Web Client'],
    }
    init_header_map.update(header_map)
    headers = http_headers.Headers(init_header_map)
    
    agent = tw_get_agent()
    d = agent.request(method, url, headers=headers)
    
    def cbRequest(response):
        resp = Response()
        resp.code = response.code
        resp.headers = response.headers
        
        finished = defer.Deferred()
        response.deliverBody(TwDeliverBody(resp, finished, limit=limit))
        return finished
    d.addCallback(cbRequest)
    
    if use_loop:
        def cbLoopFinally(arg):
            response = None
            exc = None
            
            if isinstance(arg, failure.Failure):
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
    
    return d

@gen.engine
def async_fetch(url, data=None, header_map=None, use_json=None,
        limit=None, callback=None):
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
            use_loop=True,
            ))[0]
    
    if use_json:
        response = json.loads(response.body)
    
    if callback is not None:
        callback(response, exc)
