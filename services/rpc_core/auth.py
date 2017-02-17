from zope.interface import implements
from twisted.cred import checkers, credentials, error as credError
from twisted.internet import defer


class BasicCredChecker:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)

    def __init__(self, credentials):
        "passwords: a dict-like object mapping usernames to passwords"
        self.credentials = {}
        for username, password in credentials:
            self.credentials[username] = password

    def requestAvatarId(self, credentials):
        username = credentials.username
        if username in self.credentials:
            if credentials.password == self.credentials[username]:
                return defer.succeed(username)
            else:
                return defer.fail(credError.UnauthorizedLogin("Bad password"))
        else:
            return defer.fail(credError.UnauthorizedLogin("No such user"))
