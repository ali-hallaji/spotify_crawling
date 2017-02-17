# python import
import re
import uuid
import time
import base64
import hashlib

from bson.regex import Regex
from random import random

from cerberus import Validator
from cerberus import errors

# Core Services import


def get_token(dict):
    unique_str = ''.join(["'%s':'%s';" % (key, val) for
                          (key, val) in sorted(dict.items())])
    token = hashlib.sha1(unique_str).hexdigest()
    # token = base64.b64encode(hashlib.sha1(unique_str).digest())
    return token


def unique_code(seed):
    one_part = time.time()
    two_part = random.randint(10000000, 999999999)
    unique_id = str(int(one_part + two_part))
    return unique_id[:seed]


class MongoValidator(Validator):

    def _validate_type_objectid(self, field, value):
        """
        Validation for `objectid` schema attribute.

        :param field: field name.
        :param value: field value.
        """

        if not re.match('[a-f0-9]{24}', str(value)):
            self._error(field, errors.ERROR_BAD_TYPE % 'ObjectId')

    def _validate_type_bsonregex(self, field, value):
        """
        Validation for `bson regex` schema attribute.

        :param field: field name.
        :param value: field value.
        """

        if not isinstance(value, Regex):
            self._error(field, errors.ERROR_BAD_TYPE % 'BsonRegex')


# get a UUID - URL safe, Base64
def get_uuid():
    r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    return r_uuid.replace('=', '')
