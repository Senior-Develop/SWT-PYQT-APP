# test, trader, col, opt, optremote, traderremote, traderremotenat
CURRENT_ENVIRONMENT = 'test'
CURRENT_VERSION = '210612-1'
# Run this on terminal, when building an exe file:
# pyinstaller --onefile Main.spec
# pyinstaller --onefile Collector.spec

#local test settings
DB_TEST_HOST = '127.0.0.1'
DB_TEST_PORT = '3307'
DB_TEST_DATABASE = 'swtdb'
DB_TEST_USER = 'root'
DB_TEST_PASSWORD = 'SwTdbServer'



# to build trader,collector
DB_PROD_HOST = '127.0.0.1'

# to build optimizer
DB_PROD_HOST_OPTIMIZER = '10.0.0.15'

DB_PROD_HOST_NAT_EXTIP = '98.196.14.69'
DB_PROD_USER_REMOTE = 'oktar'
DB_PROD_USER_REMOTE_NAT = 'nat3'



DB_PROD_PORT = '3306'
DB_PROD_PORT_TRADER = '3307' # to build trader
DB_PROD_PORT_OPT_COL = '3308' # to build optimizer,collector
DB_PROD_PORT_OPT = '3309'

DB_PROD_DATABASE = 'swtdb'
DB_PROD_USER = 'root'
DB_PROD_PASSWORD = 'SwTdbServer'

# 76.30.48.224 nat home
# 5.189.173.207 vps
# Optimizer: 3309, 10.0.0.13
# Collector: 3308, 10.0.0.15
# Trader: 3307, 10.0.0.10
# Falcon: 3306, 10.0.0.8

# MySql Version: 5.6.20

# To give Optimizer access to Collector Db. Run this on Collector:
# GRANT ALL PRIVILEGES ON swtdb.* TO 'root'@'OPTIMIZER' IDENTIFIED BY 'SwTdbServer' WITH GRANT OPTION;
# DB_PROD_HOST = '10.0.0.15' # bu collector local ip

# To change password:
# SET PASSWORD FOR 'root'@'localhost' = PASSWORD('SwTdbServer');

# for collector, optimizer
# run mysql-connection-error-fix.reg file on db server

# to remotely connect to the db"
#CREATE USER 'oktar'@'24.133.236.40' IDENTIFIED BY 'SwTdbServer';
#GRANT ALL PRIVILEGES ON swtdb.* TO 'oktar'@'24.133.236.40' IDENTIFIED BY 'SwTdbServer' WITH GRANT OPTION;

#CREATE USER 'test1'@'98.196.14.41' IDENTIFIED BY 'SwTdbServer';
#GRANT ALL PRIVILEGES ON swtdb.* TO 'test1'@'98.196.14.41' IDENTIFIED BY 'SwTdbServer' WITH GRANT OPTION;

#CREATE USER 'nat'@'76.30.48.224' IDENTIFIED BY 'SwTdbServer';
#GRANT ALL PRIVILEGES ON swtdb.* TO 'nat'@'76.30.48.224' IDENTIFIED BY 'SwTdbServer' WITH GRANT OPTION;

# Mysql 8 :
#CREATE USER 'nat3'@'%' IDENTIFIED BY 'SwTdbServer';
#GRANT ALL PRIVILEGES ON *.* TO 'nat3'@'%' WITH GRANT OPTION;