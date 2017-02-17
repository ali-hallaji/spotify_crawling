import time
import datetime

from functools import wraps
from twisted.internet import reactor
from twisted.internet.threads import deferToThreadPool
from txjsonrpc.web.jsonrpc import with_activity_log

from core import toLog
from config.settings import AFTER_DONE
from config.settings import BEFORE_DONE
from config.settings import DEBUG_RESULT
from services.libs.tools import get_uuid
from base_handler import exception_handler
from core.threading_pool.core_thread import get_twisted_pool as pool


def asynchronous(cls):

    cls = exception_handler(cls)
    with_activity_log(cls)

    @wraps(cls)
    def async(*args, **kwargs):
        """
           This asynchronous call function.
        """

        args = list(args)
        username = args.pop(1)
        addr = args.pop(1)
        args = tuple(args)

        # start time
        ts = time.time()
        start_time = datetime.datetime.now().strftime('%H:%M:%S')

        # Pass to defer
        worker = deferToThreadPool(reactor, pool(), cls, *args, **kwargs)
        # worker = deferToThread(cls, *args, **kwargs)

        # Handle defer
        uuid = get_uuid()
        worker.addCallback(timeit, uuid, username, addr, start_time, ts, *args)
        worker.addErrback(to_log_error)
        before_finish(uuid, username, addr, start_time, ts, *args)
        return worker

    return async


def before_finish(uuid, username, address, start_time, ts, *args):
    if BEFORE_DONE:
        func_name = args[0].__class__.__full_name__
        msg = "Before Finish << {} >> username: {}  -|- "
        msg += "func: {} -- address: {} -- args: {}"
        msg = msg.format(
            uuid,
            username,
            func_name,
            address,
            args[1:]
        )
        toLog(msg, 'request')


def timeit(result, uuid, username, address, start_time, ts, *args):
    if AFTER_DONE:
        # End of time execute work
        func_name = args[0].__class__.__full_name__
        te = time.time()

        msg = "After Done (Finish) == {} ==> start from: {} >|< username: {} "
        msg += "-|- time: {:2.4f} sec -|- func: {} -- address: {} -- args: {}"

        if DEBUG_RESULT:
            msg += " -- result: {}"
            msg = msg.format(
                uuid,
                start_time,
                username,
                te - ts,
                func_name,
                address,
                args[1:],
                result
            )
        else:
            msg = msg.format(
                start_time,
                username,
                te - ts,
                func_name,
                address,
                args[1:]
            )

        toLog(msg, 'request')
        # set_activity_log(username, address, func_name, args[1:])

    return result


def to_log_error(failure):
    toLog(str(failure), 'error')
