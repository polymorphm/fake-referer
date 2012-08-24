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

import argparse, ConfigParser, sys, os.path, \
        contextlib, signal, functools, threading
from tornado import ioloop
from twisted.internet import reactor, error as tw_error
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

def sig_lst_thread_join(thread):
    # if ``timeout`` not setted (at least any value), then ``join()`` has behavior bug.
    #       but only on Python2, not Python3
    
    while thread.is_alive():
        thread.join(timeout=7200.0)

def reactor_stop():
    def reactor_target():
        try:
            reactor.stop()
        except tw_error.ReactorNotRunning:
            pass
    
    reactor.callFromThread(reactor_target)

def on_done(verbose=None):
    if verbose is None:
        verbose = fake_referer.DEFAULT_VERBOSE
    
    if verbose >= 1:
        print u'done!'
    
    reactor_stop()
    ioloop.IOLoop.instance().stop()

def on_interrupt_sig(signum, frame, verbose=None):
    if verbose is None:
        verbose = fake_referer.DEFAULT_VERBOSE
    
    def loop_target():
        if verbose >= 1:
            print u'interrupted!'
        
        ioloop.IOLoop.instance().stop()
    
    def sig_target():
        reactor_stop()
        ioloop.IOLoop.instance().add_callback(loop_target)
    
    threading.Thread(target=sig_target).start()

def main():
    parser = argparse.ArgumentParser(
            description=u'utility for making massive www-requests with fake referer.')
    parser.add_argument('cfg', metavar='CONFIG-FILE',
            help=u'config file for task process')
    
    args = parser.parse_args()
    config = ConfigParser.ConfigParser()
    config.read(args.cfg)
    
    cfg = Config()
    
    cfg_section = 'fake-referer'
    cfg_dir = os.path.dirname(args.cfg).decode(sys.getfilesystemencoding())
    
    cfg.site_items = os.path.join(
                cfg_dir,
                config.get(cfg_section, 'site-items').decode('utf-8', 'replace')
            ) if config.has_option(cfg_section, 'site-items') else None
    cfg.referer_items = os.path.join(
                cfg_dir,
                config.get(cfg_section, 'referer-items').decode('utf-8', 'replace')
            ) if config.has_option(cfg_section, 'referer-items') else None
    cfg.count = config.get(cfg_section, 'count').decode('utf-8', 'replace') \
            if config.has_option(cfg_section, 'count') else None
    cfg.conc = int(config.get(cfg_section, 'conc').decode('utf-8', 'replace')) \
            if config.has_option(cfg_section, 'conc') else None
    cfg.delay = float(config.get(cfg_section, 'delay').decode('utf-8', 'replace')) \
            if config.has_option(cfg_section, 'delay') else None
    cfg.verbose = int(config.get(cfg_section, 'verbose').decode('utf-8', 'replace')) \
            if config.has_option(cfg_section, 'verbose') else None
    
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
        reactor_thr = threading.Thread(target=reactor.run,
                kwargs={'installSignalHandlers': False})
        
        loop_thr.start()
        reactor_thr.start()
        
        sig_lst_thread_join(reactor_thr)
        sig_lst_thread_join(loop_thr)
