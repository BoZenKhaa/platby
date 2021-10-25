import os
import pathlib
import configparser


def read_config(config_paths):
    config = configparser.ConfigParser()

    read_configs = config.read(config_paths)
    if read_configs:
        print("Succesfully read config from: {}".format(str(read_configs)))
    else:
        print("Failed to find any config in {}".format([os.path.abspath(path) for path in config_paths]))
    return config


CONFIG = read_config(['./config_test.cfg'])

print(CONFIG['credentials']['path'])
