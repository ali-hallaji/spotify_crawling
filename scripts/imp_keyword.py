import sys
import csv
import datetime

from core.db import cursor
from config.settings import BASE_DIR
from config.settings import KEYWORD_DAYS


def import_keywords(path):
    f = open(path, 'r')
    reader = csv.reader(f)
    now = datetime.datetime.now()
    expected = now - datetime.timedelta(days=(KEYWORD_DAYS + 1))

    for i in reader:
        doc = {}
        doc['total'] = 0
        doc['loops'] = 0
        doc['turn_date'] = expected
        doc['loop'] = 0
        doc['word'] = i[0]
        doc['created_date'] = now
        cursor.keywords.insert(doc)


if __name__ == '__main__':

    try:
        path = BASE_DIR + '/storage/' + sys.argv[1]
        import_keywords(path)

    except IndexError:
        print "Please enter correct args"
