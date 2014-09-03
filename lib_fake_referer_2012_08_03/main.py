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

import argparse, configparser, sys, os.path, \
        contextlib, signal, functools, threading
from tornado import ioloop
from . import fake_referer

class UserError(Exception):
    pass

class Config(object):
    pass

@contextlib.contextmanager
def set_signal_listener(signalnum, handler):
    orig_handler = signal.signal(signalnum, handler)
    try:
        yield
    finally:
        signal.signal(signalnum, orig_handler)

def on_done(verbose=None):
    if verbose is None:
        verbose = fake_referer.DEFAULT_VERBOSE
    
    if verbose >= 1:
        print('done!')
    
    ioloop.IOLoop.instance().stop()

def on_interrupt_sig(signum, frame, verbose=None):
    if verbose is None:
        verbose = fake_referer.DEFAULT_VERBOSE
    
    def loop_target():
        if verbose >= 1:
            print('interrupted!')
        
        ioloop.IOLoop.instance().stop()
    
    def sig_target():
        ioloop.IOLoop.instance().add_callback(loop_target)
    
    threading.Thread(target=sig_target).start()

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
    cfg.agent_name = config.get(cfg_section, 'agent-name', fallback=None)
    cfg.verbose = config.getint(cfg_section, 'verbose', fallback=None)
    
    if cfg.site_items is None:
        raise UserError('cfg.site_items is None')
    if cfg.referer_items is None:
        raise UserError('cfg.referer_items is None')
    
    io_loop = ioloop.IOLoop.instance()
    
    io_loop.add_callback(functools.partial(fake_referer.fake_referer, cfg,
            on_finish=functools.partial(on_done, verbose=cfg.verbose)))
    
    with set_signal_listener(signal.SIGINT, functools.partial(
                    on_interrupt_sig, verbose=cfg.verbose)), \
            set_signal_listener(signal.SIGTERM, functools.partial(
                    on_interrupt_sig, verbose=cfg.verbose)):
        loop_thr = threading.Thread(target=io_loop.start)
        
        loop_thr.start()
        loop_thr.join()
