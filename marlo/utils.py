#!/usr/bin/env python
import gym
import marlo
import sys
import os
import importlib
import logging
logger = logging.getLogger(__name__)

from threading import Thread
from queue import Queue

import socket
from contextlib import closing

from marlo.launch_minecraft_in_background import launch_minecraft_in_background

def register_environments(MARLO_ENV_PATHS):
    for env_path in MARLO_ENV_PATHS:
        sys.path.append(env_path)
        for _marlo_env_dir in os.listdir(env_path):
            """
            Expect that each env directory will have the relevant 
            gym registrations in a "register_environments" functions 
            implemented in __init__.py
            """
            if os.path.isdir(os.path.join(env_path, _marlo_env_dir)) and \
                    not _marlo_env_dir.startswith("__"):
                module = importlib.import_module(_marlo_env_dir)
                module._register()
                logger.debug("Creating envs from : {}".format(_marlo_env_dir))

def threaded(fn):
    def wrap(queue, *args, **kwargs):
        queue.put(fn(*args, **kwargs))

    def call(*args, **kwargs):
        queue = Queue()
        job = Thread(target=wrap, args=(queue,) + args, kwargs=kwargs)
        job.start()
        return queue

    return call

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def launch_clients(number_of_clients, replaceable=False):
    """Launches a series of Minecraft Client which can be used by 
    MarLo environments.

    :param number_of_clients: Number of Minecraft Clients to launch
    :type number_of_clients: int
    :param replaceable: `replaceable` argument from `launchClient.sh` (TODO: Check with @Andre)
    :type replaceable: bool

    **Note** This is still in experimental phase, as this does not yet clean up 
    the processes after the code exits.
    
    :returns:  A valid `client_pool` object

    >>> import marlo
    >>> client_pool = marlo.launch_clients(number_of_client=2)
    >>> print(client_pool)
    >>> [('127.0.0.1', 27655), ('127.0.0.1', 15438)]
    """    
    ports = [find_free_port() for _ in range(number_of_clients)]
    MINECRAFT_ROOT = os.getenv("MALMO_MINECRAFT_ROOT")
    if not MINECRAFT_ROOT:
        raise Exception("Please set the environment variable"
                        "`MALMO_MINECRAFT_ROOT` as the root of your "
                        "Minecraft Directory")

    launch_processes = launch_minecraft_in_background(
                            MINECRAFT_ROOT,
                            ports,
                            replaceable=False
                            )

    client_pool = [('127.0.0.1', port) for port in ports]
    return client_pool
