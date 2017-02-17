import signal
from threading import Thread
from twisted.python import log
from twisted.web import server
from twisted.internet import reactor
from txjsonrpc.auth import wrapResource

from core import toLog
from config.settings import CORE_PORT
from config.settings import CORE_ID
from config.settings import DEBUG
from config.settings import background_process_thread_pool as pool
from config.settings import CREDENTIALS
from services.rpc_core.main_json_rpc import CoreServices
from services.rpc_core.auth import BasicCredChecker


def runRPC():
    print 'Core Services running  \t\t\t\t\t\t[OK]'
    setup_signal_handlers()
    Thread(target=run_reactor).start()


def run_reactor():
    main = CoreServices()
    observer = log.PythonLoggingObserver()
    observer.start()

    if CREDENTIALS:
        checker = BasicCredChecker(CREDENTIALS)
        main = wrapResource(main, [checker], realmName=CORE_ID)

    reactor.listenTCP(CORE_PORT, server.Site(resource=main))
    reactor.suggestThreadPoolSize(pool)
    reactor.run(installSignalHandlers=False)


def setup_signal_handlers():
    if DEBUG:
        toLog('Setting debug handlers', 'debug')
        signal.signal(signal.SIGUSR1, embed)
        signal.signal(signal.SIGUSR2, trace)
        signal.signal(signal.SIGWINCH, print_trace)


def embed(sig, frame):
    try:
        from IPython import embed
        embed()
    except ImportError:
        import code
        code.interact(local=locals())


def trace(sig, frame):
    try:
        import ipdb as pdb
    except ImportError:
        import pdb

    pdb.set_trace()


def print_trace(sig, frame):
    traceback.print_stack()
