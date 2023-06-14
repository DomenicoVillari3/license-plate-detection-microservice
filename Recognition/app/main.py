# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""License Plate Detection
This implementation does its best to follow the Robert Martin's Clean code guidelines.
The comments follows the Google Python Style Guide:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md
"""

__copyright__ = 'Copyright 2023, FCRlab at University of Messina'
__author__ = 'Lorenzo Carnevale <lcarnevale@unime.it>'
__credits__ = ''
__description__ = 'License Plate Detection'

import os
import yaml
import argparse
from threading import Lock
#from logic.writer import Writer
from logic.recognition import Recognition

def main():
    description = ('%s\n%s' % (__author__, __description__))
    epilog = ('%s\n%s' % (__credits__, __copyright__))
    parser = argparse.ArgumentParser(
        description = description,
        epilog = epilog
    )

    parser.add_argument('-c', '--config',
                        dest='config',
                        help='YAML configuration file',
                        type=str,
                        required=True)

    parser.add_argument('-v', '--verbosity',
                        dest='verbosity',
                        help='Logging verbosity level',
                        action="store_true")

    options = parser.parse_args()
    verbosity = options.verbosity
    mutex = Lock()
    with open(options.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    logdir_name = config['logging']['logging_folder']
    logging_path = '%s/%s' % (config['logging']['logging_folder'], config['logging']['logging_filename'])
    if not os.path.exists(logdir_name):
        os.makedirs(logdir_name)

    recognition = setup_recognition(config, mutex, verbosity, logging_path)
    recognition.start()


def setup_recognition(config, mutex, verbosity, logging_path):
    recognition = Recognition(config['static_files']['detected'], logging_path, verbosity, config['restful']['host'],config['restful']['port'],mutex)
    recognition.setup()
    return recognition

if __name__ == '__main__':
    main()