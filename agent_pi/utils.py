import os


def EXTERN_IP():
    return os.environ.get("EXTERN_IP", "120.158.101.13")


def LAN_IP():
    return os.environ.get("LAN_IP", "192.168.0.67")


def AGENT_IP():
    # return os.environ.get("AGENT_IP", "120.158.101.13:42069")  # changes
    # return os.environ.get("AGENT_IP", "{}:42069".format(SELF_IP()))  # changes
    return os.environ.get("AGENT_IP", "{}:42069".format(LAN_IP()))


def IS_PI():
    return os.environ.get("IS_PI", False)  # set to True


def FACE_RECOG_ENABLED():
    return os.environ.get("FACE_RECOG", False) == "ENABLED"  # set to True


def MASTERSERVICE_IP():
    # return os.environ.get('MASTERSERVICE_IP', "111.223.128.211:50505")
    # return os.environ.get('MASTERSERVICE_IP', "120.158.101.13:50505")
    # return os.environ.get('MASTERSERVICE_IP', "{}:50505".format(SELF_IP()))
    return os.environ.get('MASTERSERVICE_IP', "{}:50505".format(LAN_IP()))


def TESTING_ENV():
    return os.environ.get('TESTING_ENV', 'GCP')


def SOCKETS_ENABLED():
    return os.environ.get("ENABLE_SOCKETS", False)  # set to True


def SELF_IP():
    return os.environ.get("SELF_IP", "localhost")
    # return os.environ.get("SELF_IP", "192.168.0.67")


def ENABLE_BLUETOOTH():
    return os.environ.get("ENABLE_BLUETOOTH", False)  # set to True
