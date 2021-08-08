import mysql.connector
import Config
from mysql.connector import errorcode

class DNBase:

    def __init__(self, mode=""):
        self.current_env = getattr(Config, 'CURRENT_ENVIRONMENT', 'test')

        if mode == 'traderremotenat':
            db_host = getattr(Config, 'DB_PROD_HOST_NAT_EXTIP', '')
            db_database = getattr(Config, 'DB_PROD_DATABASE', '')
            db_user = getattr(Config, 'DB_PROD_USER_REMOTE_NAT', '')
            db_password = getattr(Config, 'DB_PROD_PASSWORD', '')
            db_port = getattr(Config, 'DB_PROD_PORT_TRADER', '')

        elif self.current_env == 'test':
            # db_host = getattr(Config, 'DB_TEST_HOST', '')
            # db_database = getattr(Config, 'DB_TEST_DATABASE', '')
            # db_user = getattr(Config, 'DB_TEST_USER', '')
            # db_password = getattr(Config, 'DB_TEST_PASSWORD', '')
            # db_port = getattr(Config, 'DB_TEST_PORT', '')
            db_host = "localhost"
            db_database = "swtdblocal"
            db_user = "root"
            db_password = ""
            db_port = 3306

        elif self.current_env == 'trader':
            db_host = getattr(Config, 'DB_PROD_HOST', '')
            db_database = getattr(Config, 'DB_PROD_DATABASE', '')
            db_user = getattr(Config, 'DB_PROD_USER', '')
            db_password = getattr(Config, 'DB_PROD_PASSWORD', '')
            db_port = getattr(Config, 'DB_PROD_PORT_TRADER', '')

        elif self.current_env == 'col':
            db_host = getattr(Config, 'DB_PROD_HOST', '')
            db_database = getattr(Config, 'DB_PROD_DATABASE', '')
            db_user = getattr(Config, 'DB_PROD_USER', '')
            db_password = getattr(Config, 'DB_PROD_PASSWORD', '')
            db_port = getattr(Config, 'DB_PROD_PORT_OPT_COL', '')

        elif self.current_env == 'opt':
            db_host = getattr(Config, 'DB_PROD_HOST', '')
            db_database = getattr(Config, 'DB_PROD_DATABASE', '')
            db_user = getattr(Config, 'DB_PROD_USER', '')
            db_password = getattr(Config, 'DB_PROD_PASSWORD', '')
            db_port = getattr(Config, 'DB_PROD_PORT_OPT', '')

        elif self.current_env == 'optremote':
            db_host = getattr(Config, 'DB_PROD_HOST_NAT_EXTIP', '')
            db_database = getattr(Config, 'DB_PROD_DATABASE', '')
            db_user = getattr(Config, 'DB_PROD_USER_REMOTE', '')
            db_password = getattr(Config, 'DB_PROD_PASSWORD', '')
            db_port = getattr(Config, 'DB_PROD_PORT_OPT', '')

        elif self.current_env == 'traderremote':
            db_host = getattr(Config, 'DB_PROD_HOST_NAT_EXTIP', '')
            db_database = getattr(Config, 'DB_PROD_DATABASE', '')
            db_user = getattr(Config, 'DB_PROD_USER_REMOTE', '')
            db_password = getattr(Config, 'DB_PROD_PASSWORD', '')
            db_port = getattr(Config, 'DB_PROD_PORT_TRADER', '')




        else:
            db_host = getattr(Config, 'DB_PROD_HOST', '')
            db_database = getattr(Config, 'DB_PROD_DATABASE', '')
            db_user = getattr(Config, 'DB_PROD_USER', '')
            db_password = getattr(Config, 'DB_PROD_PASSWORD', '')
            db_port = getattr(Config, 'DB_PROD_PORT', '')


        try:
            self.db = mysql.connector.connect(host=db_host,
                                         database=db_database,
                                         port=db_port,
                                         user=db_user,
                                         password=db_password,
                                         auth_plugin='mysql_native_password')
            self.cursor = self.db.cursor(buffered=True)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)

