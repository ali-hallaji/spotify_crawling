from jsonrpclib import Server


def rpc_connection(host, port, user, _pass):
    s = Server('http://{}:{}@{}:{}'.format(user, _pass, host, port))
    return s
