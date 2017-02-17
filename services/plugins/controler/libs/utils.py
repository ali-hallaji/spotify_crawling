import os
import time
import subprocess
import random
import spotipy
import base64
import uuid
from shutil import *
from spotipy.oauth2 import SpotifyClientCredentials

from config.settings import CREDENCIAL


def copytree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst):  # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error, err:
            errors.extend(err.args[0])
        except EnvironmentError, why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError, why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error, errors


def get_sp_token(client_id, client_secret):
    s = SpotifyClientCredentials(client_id, client_secret)
    token = s.get_access_token()
    return token


def gen_sp():
    tokens = random.choice(CREDENCIAL)
    token = get_sp_token(
        tokens[0],
        tokens[1]
    )
    sp = spotipy.Spotify(auth=token)

    return sp


def to_pytables_date(_date):
    return time.mktime(_date.timetuple())


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def restart_service(name):
    command = ['/usr/sbin/service', name, 'restart']
    # shell=FALSE for sudo to work.
    subprocess.call(command, shell=False)


def check_db(db):
    time.sleep(random.choice([2, 3, 4, 5, 4, 3]))
    status = subprocess.check_output(
        "/usr/sbin/service {} status".format(db),
        shell=True
    )

    if "Active: active" in status:
        return False
    else:
        return True


# get a UUID - URL safe, Base64
def get_a_uuid():
    r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    return r_uuid.replace('=', '')

