

def memory():
    global mem_access

    try:
        return mem_access

    except:
        mem_access = {}
        return mem_access
