# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2012, 2014 Andrej A Antonov <polymorphm@gmail.com>
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
