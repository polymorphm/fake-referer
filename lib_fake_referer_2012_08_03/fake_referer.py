# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2012 Andrej A Antonov <polymorphm@gmail.com>
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

import itertools, base64, json, datetime
from tornado import ioloop, stack_context, gen
from . import get_items, async_http_request_helper

DEFAULT_CONC = 10
DEFAULT_DELAY = 0.0

def url_normalize(url):
    if url.startswith('http:') or url.startswith('https:'):
        return url
    
    if url.startswith('//'):
        return 'http:%s' % url
    
    return 'http://%s' % url

@gen.engine
def fake_referer_thread(site_iter, referer_iter,
            delay=None, verbose=None, on_finish=None):
    site_iter = iter(site_iter)
    referer_iter = iter(referer_iter)
    if verbose is None:
        verbose = 0
    on_finish = stack_context.wrap(on_finish)
    
    if delay is None:
        delay = DEFAULT_DELAY
    
    for site in site_iter:
        referer = next(referer_iter)
        
        if verbose >= 1:
            print '%s (<- %s): opening...' % (site, referer)
        
        if delay:
            yield gen.Task(
                    ioloop.IOLoop.instance().add_timeout,
                    datetime.timedelta(seconds=delay),
                    )
        
        response, exc = (yield gen.Task(
                async_http_request_helper.async_fetch,
                site,
                header_list=(('Referer', referer), ),
                use_raise=False,
                ))[0]
        
        if exc is None:
            if verbose >= 1:
                print '%s (<- %s): PASS' % (site, referer)
        else:
            if verbose >= 1:
                print '%s (<- %s): ERROR: %s' % (site, referer, exc[1])
    
    if on_finish is not None:
        on_finish()

@gen.engine
def bulk_fake_referer(site_iter, referer_iter,
            conc=None, delay=None, verbose=None, on_finish=None):
    site_iter = iter(site_iter)
    referer_iter = iter(referer_iter)
    on_finish = stack_context.wrap(on_finish)
    
    if conc is None:
        conc = DEFAULT_CONC
    
    wait_key_list = tuple(object() for x in xrange(conc))
    
    for wait_key in wait_key_list:
        fake_referer_thread(site_iter, referer_iter,
                delay=delay, verbose=verbose,
                on_finish=(yield gen.Callback(wait_key)))
    
    for wait_key in wait_key_list:
        yield gen.Wait(wait_key)
    
    if on_finish is not None:
        on_finish()

def fake_referer(cfg, on_finish=None):
    on_finish = stack_context.wrap(on_finish)
    
    if cfg.count == 'infinite':
        site_iter = itertools.imap(
                url_normalize,
                get_items.get_random_infinite_items(cfg.site_items),
                )
    elif cfg.count is not None:
        count = int(cfg.count)
        site_iter = itertools.imap(
                url_normalize,
                itertools.islice(
                        get_items.get_random_infinite_items(cfg.site_items),
                        count,
                        ),
                )
    else:
        site_iter = itertools.imap(
                url_normalize,
                get_items.get_random_finite_items(cfg.site_items),
                )
    
    referer_iter = itertools.imap(
            url_normalize,
            get_items.get_random_infinite_items(cfg.referer_items),
            )
    
    bulk_fake_referer(site_iter, referer_iter,
            conc=cfg.conc, delay=cfg.delay, verbose=cfg.verbose,
            on_finish=on_finish)
