from __future__ import absolute_import

import xbmc
from time import time

import_started = time()
from src.service import main  # type: ignore
xbmc.log('TorrSpy service import finished in {:.2f} s'.format(time() - import_started))

if __name__ == '__main__':
    main()
