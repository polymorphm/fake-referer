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

import itertools, datetime, urllib.parse
from tornado import ioloop, stack_context, gen
from . import get_items, async_http_request_helper

DEFAULT_CONC = 10
DEFAULT_DELAY = 0.0
DEFAULT_VERBOSE = 0

def url_normalize(url):
    if url.startswith('http:') or url.startswith('https:'):
        return url
    
    if url.startswith('//'):
        return 'http:%s' % url
    
    return 'http://%s' % url

@gen.coroutine
def fake_referer_thread(site_iter, referer_iter,
            delay=None, agent_name=None, verbose=None, on_finish=None):
    site_iter = iter(site_iter)
    referer_iter = iter(referer_iter)
    on_finish = stack_context.wrap(on_finish)
    
    if delay is None:
        delay = DEFAULT_DELAY
    if verbose is None:
        verbose = DEFAULT_VERBOSE
    
    for site in site_iter:
        referer = next(referer_iter)
        
        if delay:
            delay_wait_key = object()
            ioloop.IOLoop.instance().add_timeout(
                    datetime.timedelta(seconds=delay),
                    callback=(yield gen.Callback(delay_wait_key)),
                    )
        
        if verbose >= 1:
            print('%s (<- %s): opening...' % (site, referer))
        
        header_list = [
            ('Referer', referer),
        ]
        
        if agent_name is not None:
            header_list.append(('User-agent', agent_name))
        
        response, exc = (yield gen.Task(
                async_http_request_helper.async_fetch,
                site,
                header_list=header_list,
                limit=100,
                ))[0]
        
        if exc is not None:
            if verbose >= 1:
                print('%s (<- %s): ERROR: %s' % (site, referer, exc[1]))
            continue
        
        if response.code and response.code != 200:
            if verbose >= 1:
                print('%s (<- %s): WARN (code is %s)' % (site, referer, response.code))
            continue
        
        if verbose >= 1:
            print('%s (<- %s): PASS' % (site, referer))
        
        if delay:
            yield gen.Wait(delay_wait_key)
    
    if on_finish is not None:
        on_finish()

@gen.engine
def bulk_fake_referer(site_iter, referer_iter,
            conc=None, delay=None, agent_name=None, verbose=None, on_finish=None):
    site_iter = iter(site_iter)
    referer_iter = iter(referer_iter)
    on_finish = stack_context.wrap(on_finish)
    
    if conc is None:
        conc = DEFAULT_CONC
    
    wait_key_list = tuple(object() for x in range(conc))
    
    for wait_key in wait_key_list:
        fake_referer_thread(site_iter, referer_iter,
                delay=delay, agent_name=agent_name, verbose=verbose,
                on_finish=(yield gen.Callback(wait_key)))
    
    for wait_key in wait_key_list:
        yield gen.Wait(wait_key)
    
    if on_finish is not None:
        on_finish()

def fake_referer(cfg, on_finish=None):
    on_finish = stack_context.wrap(on_finish)
    
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
    
    bulk_fake_referer(
            site_iter,
            referer_iter,
            conc=cfg.conc,
            delay=cfg.delay,
            agent_name=cfg.agent_name,
            verbose=cfg.verbose,
            on_finish=on_finish,
            )
