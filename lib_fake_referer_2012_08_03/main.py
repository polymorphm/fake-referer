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

import argparse, configparser, os.path, signal
import asyncio
from . import fake_referer

class UserError(Exception):
    pass

class Config(object):
    pass

def main():
    parser = argparse.ArgumentParser(
            description='utility for making massive www-requests with fake referer.')
    parser.add_argument('cfg', metavar='CONFIG-FILE',
            help='config file for task process')
    
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read(args.cfg, encoding='utf-8')
    
    cfg = Config()
    
    cfg_section = 'fake-referer'
    cfg_dir = os.path.dirname(args.cfg)
    
    cfg.site_items = os.path.join(
                cfg_dir,
                config.get(cfg_section, 'site-items')
            ) if config.has_option(cfg_section, 'site-items') else None
    cfg.referer_items = os.path.join(
                cfg_dir,
                config.get(cfg_section, 'referer-items')
            ) if config.has_option(cfg_section, 'referer-items') else None
    cfg.count = config.get(cfg_section, 'count', fallback=None)
    cfg.conc = config.getint(cfg_section, 'conc', fallback=None)
    cfg.delay = config.getfloat(cfg_section, 'delay', fallback=None)
    cfg.user_agent = config.get(cfg_section, 'user-agent', fallback=None)
    cfg.verbose = config.getint(cfg_section, 'verbose', fallback=None)
    
    if cfg.site_items is None:
        raise UserError('cfg.site_items is None')
    if cfg.referer_items is None:
        raise UserError('cfg.referer_items is None')
    
    loop = asyncio.get_event_loop()
    
    fake_referer_future = fake_referer.fake_referer(cfg, loop=loop)
    assert isinstance(fake_referer_future, asyncio.Future)
    
    def shutdown_handler():
        fake_referer_future.cancel()
    
    try:
        loop.add_signal_handler(signal.SIGINT, shutdown_handler)
    except NotImplementedError:
        pass
    try:
        loop.add_signal_handler(signal.SIGTERM, shutdown_handler)
    except NotImplementedError:
        pass
    
    try:
        loop.run_until_complete(fake_referer_future)
    except asyncio.CancelledError:
        if cfg.verbose is not None and cfg.verbose >= 1:
            print('cancelled!')
    else:
        fake_referer_future.result()
        
        if cfg.verbose is not None and cfg.verbose >= 1:
            print('done!')
