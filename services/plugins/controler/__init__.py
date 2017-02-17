CONTROLER_LOADED_MODULE = None


def getFlag():
    global CONTROLER_LOADED_MODULE
    try:
        return CONTROLER_LOADED_MODULE
    except:
        CONTROLER_LOADED_MODULE = False
        return CONTROLER_LOADED_MODULE


def loadFlag():
    global CONTROLER_LOADED_MODULE
    CONTROLER_LOADED_MODULE = True


def unLoadFlag():
    global CONTROLER_LOADED_MODULE
    CONTROLER_LOADED_MODULE = False
