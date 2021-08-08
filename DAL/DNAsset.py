from Common.Asset import Asset
from DAL.DNBase import DNBase
import traceback
from datetime import datetime


class DNAsset(DNBase):
    def getAsset(self, asset_name):
        asset = None
        try:
            sql = "SELECT * FROM Asset WHERE AssetName = %s"
            values = (asset_name,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                asset = Asset(*result)
        except:
            print(traceback.format_exc())
        return asset

    def listAsset(self):
        assets = None
        try:
            sql = "SELECT * FROM Asset"
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if results:
                assets = [Asset(*result) for result in results]
        except:
            print(traceback.format_exc())
        return assets

    def insertAsset(self, asset):
        assetId = 0
        try:
            sql = "INSERT INTO Asset ("
            sql = sql + "AssetName, BalanceFree, BalanceLocked, ModifiedDate"
            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s)"

            values = (asset.AssetName, asset.BalanceFree, asset.BalanceLocked, asset.ModifiedDate)

            self.cursor.execute(sql, values)
            assetId = self.cursor.lastrowid
            self.db.commit()

        except:
            print(traceback.format_exc())
        return assetId

    def updateAsset(self, asset):
        assets = None
        try:
            sql = "UPDATE Asset SET "
            sql = sql + "BalanceFree = %s, BalanceLocked = %s, ModifiedDate = %s"
            sql = sql + " WHERE AssetName = %s"

            values = (asset.BalanceFree, asset.BalanceLocked, asset.ModifiedDate, asset.AssetName)

            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return assets

    def deleteAsset(self, asset_id):
        asset = None
        try:
            sql = "DELETE FROM Asset WHERE AssetId = %s"
            values = (asset_id,)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return asset

    def resetAllAssets(self):
        try:
            sql = 'UPDATE Asset SET ' \
                  'BalanceFree = 0, ' \
                  'BalanceLocked = 0, ' \
                  'ModifiedDate = %s'
            values = (datetime.now(),)
            self.cursor.execute(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())

    def updateAssets(self, assets):
        try:
            sql = 'INSERT INTO Asset ' \
                  '(AssetName, BalanceFree, BalanceLocked, ModifiedDate) ' \
                  'VALUES (%s, %s, %s, %s) '\
                  'ON DUPLICATE KEY UPDATE ' \
                  'BalanceFree=VALUES(BalanceFree), ' \
                  'BalanceLocked=VALUES(BalanceLocked), ' \
                  'ModifiedDate=VALUES(ModifiedDate)'
            values = [(asset.AssetName,
                       asset.BalanceFree,
                       asset.BalanceLocked,
                       asset.ModifiedDate) for asset in assets]
            self.cursor.executemany(sql, values)
            self.db.commit()
        except:
            print(traceback.format_exc())