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

import itertools, datetime
from urllib import request as url_request
import asyncio
from . import get_items, async_http_request_helper

DEFAULT_CONC = 10
DEFAULT_DELAY = 0.0

def url_normalize(url):
    if url.startswith('http:') or url.startswith('https:'):
        return url
    
    if url.startswith('//'):
        return 'http:{}'.format(url)
    
    return 'http://{}'.format(url)

@asyncio.coroutine
def fake_referer_thread(site_iter, referer_iter,
            delay=None, agent_name=None, verbose=None, loop=None):
    assert loop is not None
    
    site_iter = iter(site_iter)
    referer_iter = iter(referer_iter)
    
    if delay is None:
        delay = DEFAULT_DELAY
    
    for site in site_iter:
        referer = next(referer_iter)
        
        delay_future = asyncio.async(asyncio.sleep(delay, loop=loop), loop=loop)
        
        if verbose is not None and verbose >= 1:
            print('{} (<- {}): opening...'.format(site, referer))
        
        headers = {
            'Referer': referer,
            }
        
        if agent_name is not None:
            headers['User-Agent'] = agent_name
        
        async_fetch_future = async_http_request_helper.async_fetch(
                url_request.Request(site, headers=headers),
                limit=100,
                loop=loop,
                )
        
        yield from asyncio.wait((async_fetch_future,), loop=loop)
        
        if not async_fetch_future.cancelled() and async_fetch_future.exception():
            if verbose is not None and verbose >= 1:
                print('{} (<- {}): ERROR: {} {}'.format(
                        site,
                        referer,
                        type(async_fetch_future.exception()),
                        str(async_fetch_future.exception())),
                        )
            
            yield from asyncio.wait((delay_future,), loop=loop)
            delay_future.result()
            
            continue
        
        response = async_fetch_future.result()
        
        if verbose is not None and verbose >= 1:
            print('{} (<- {}): PASS (code is {})'.format(
                    site,
                    referer,
                    response.code,
                    ))
        
        yield from asyncio.wait((delay_future,), loop=loop)
        delay_future.result()

def bulk_fake_referer(site_iter, referer_iter,
            conc=None, delay=None, agent_name=None, verbose=None,
            loop=None):
    assert loop is not None
    
    site_iter = iter(site_iter)
    referer_iter = iter(referer_iter)
    
    if conc is None:
        conc = DEFAULT_CONC
    
    future_list = tuple(
            asyncio.async(
                    fake_referer_thread(
                            site_iter,
                            referer_iter,
                            delay=delay,
                            agent_name=agent_name,
                            verbose=verbose,
                            loop=loop,
                            ),
                    loop=loop,
                    )
            for x in range(conc)
            )
    
    wait_coro = asyncio.wait(future_list, loop=loop)
    wait_future = asyncio.async(wait_coro, loop=loop)
    
    return wait_future

def fake_referer(cfg, loop=None):
    assert loop is not None
    
    if cfg.count == 'infinite':
        site_iter = map(
                url_normalize,
                get_items.get_random_infinite_items(cfg.site_items),
                )
    elif cfg.count is not None:
        count = int(cfg.count)
        site_iter = map(
                url_normalize,
                itertools.islice(
                        get_items.get_random_infinite_items(cfg.site_items),
                        count,
                        ),
                )
    else:
        site_iter = map(
                url_normalize,
                get_items.get_random_finite_items(cfg.site_items),
                )
    
    referer_iter = map(
            url_normalize,
            get_items.get_random_infinite_items(cfg.referer_items),
            )
    
    return bulk_fake_referer(
            site_iter,
            referer_iter,
            conc=cfg.conc,
            delay=cfg.delay,
            agent_name=cfg.agent_name,
            verbose=cfg.verbose,
            loop=loop,
            )
