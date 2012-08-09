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

import argparse, ConfigParser, sys, os.path
from tornado import ioloop
from .fake_referer import fake_referer

class UserError(Exception):
    pass

class Config(object):
    pass

def final():
    print(u'done!')
    ioloop.IOLoop.instance().stop()

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
    
    if cfg.site_items is None:
        raise UserError('cfg.site_items is None')
    if cfg.referer_items is None:
        raise UserError('cfg.referer_items is None')
    
    fake_referer(cfg, on_finish=final)
    
    ioloop.IOLoop.instance().start()
