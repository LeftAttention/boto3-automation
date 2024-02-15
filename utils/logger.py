from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import logging
import time
from pathlib import Path

def create_logger(cfg):
    logdir = Path(cfg.logdir)

    if not logdir.exists():
        logdir.mkdir()

    time_str = time.strftime('%Y-%m-%d-%H-%M')
    
    log_file = f'{time_str}.log'
    final_log_file = logdir / log_file

    head = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename=str(final_log_file),
                        format=head)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    logging.getLogger('').addHandler(console)

    return logger