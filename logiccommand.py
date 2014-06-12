#-------------------------------------------------------------------------------
# Copyright (c) 2014 Proxima Centauri srl <info@proxima-centauri.it>.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Public License v3.0
# which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/gpl.html
# 
# Contributors:
#     Proxima Centauri srl <info@proxima-centauri.it> - initial API and implementation
#-------------------------------------------------------------------------------
import logging.config
# configure the logging system
logging.config.fileConfig('loggingdev.conf')

import time
from logic import do_logics, config

config.cfgfile = "myna.conf"

def main():
    while True:
        do_logics()
        time.sleep(10)

if __name__ == "__main__":
    main()
