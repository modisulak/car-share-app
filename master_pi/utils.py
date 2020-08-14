# credit to https://stackoverflow.com/questions/21060073/dynamic-inheritance-in
# -python


def get_sqlalchemy_config(inherit_config):
    # credit to https://docs.python.org/3/library/stdtypes.html#str.format_map
    class Default(dict):
        def __missing__(self, key):
            return ""

    class AlchemyConfig(inherit_config):

        SQLALCHEMY_DATABASE_URI = None
        # SQLALCHEMY_ECHO = True
        SQLALCHEMY_TRACK_MODIFICATIONS = False

        def __init__(self, *args, **kwargs):
            super(AlchemyConfig, self).__init__(*args, **kwargs)
            # credit to https://stackoverflow.com/questions/22252397/
            # importerror-no-module-named-mysqldb
            uri = "mysql+pymysql://{user}:{password}@{host}{port}/{database}" +\
                "?charset=utf8mb4"
            AlchemyConfig.SQLALCHEMY_DATABASE_URI = uri.format_map(
                Default(inherit_config.DATABASE))

    return AlchemyConfig
