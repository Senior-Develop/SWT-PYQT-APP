from Common.StrategyParameters import StrategyParameters
from DAL.DNBase import DNBase
import traceback
import Config


class DNStrategyParameters(DNBase):

    def __init__(self, mode=""):
        DNBase.__init__(self,mode)

        # Only columns in this list will be fetched from the db.
        self.columns = (
            'StrategyParametersId', 'Name', 'OptimizationId', 'Timeframe', 'Symbol',
            'ROC_IndicatorEnabled', 'ROC_AppliedPrice_R', 'ROC_AppliedPrice_F', 'ROC_Period_R', 'ROC_Smoothing_R',
            'ROC_Period_F', 'ROC_R_BuyIncreasePercentage', 'ROC_F_BuyDecreasePercentage', 'MPT_IndicatorEnabled',
            'MPT_AppliedPrice','MPT_ShortMAPeriod', 'MPT_LongMAPeriod', 'NV_IndicatorEnabled', 'NV_IncreasePercentage',
            'NV_MinNetVolume', 'TREND_IndicatorEnabled', 'TREND_AppliedPrice', 'TREND_LongEmaPeriod', 'TREND_ShortEmaPeriod',
            'EMAX_IndicatorEnabled', 'EMAX_AppliedPrice', 'EMAX_LongEmaPeriod', 'EMAX_ShortEmaPeriod', 'VSTOP_IndicatorEnabled'
            ,'VSTOP_AppliedPrice', 'VSTOP_Period', 'VSTOP_Factor', 'SELL_IndicatorEnabled', 'SELL_DecreasePercentage',
            'SELL_Period', 'ROC_Smoothing_S', 'SELL_RSI_AppliedPrice', 'SELL_RSI_Period', 'SELL_RSI_UpperLevel',
            'SELL_RSI_LowerLevel', 'SELL_Stoch_AppliedPrice', 'SELL_Stoch_KPeriod', 'SELL_Stoch_DPeriod', 'SELL_Stoch_Slowing',
            'SELL_Stoch_UpperLevel', 'SELL_Stoch_LowerLevel', 'R_TradingEnabled', 'R_SL1Percentage', 'R_SL2Percentage',
            'R_SLTimerInMinutes', 'R_TSLActivationPercentage', 'R_TSLTrailPercentage', 'F_TradingEnabled', 'F_SL1Percentage',
            'F_SL2Percentage', 'F_SLTimerInMinutes', 'F_TSLActivationPercentage', 'F_TSLTrailPercentage', 'S_TradingEnabled',
            'S_SL1Percentage', 'S_SL2Percentage', 'S_SLTimerInMinutes', 'S_TSLActivationPercentage', 'S_TSLTrailPercentage',
            'TargetPercentage', 'RebuyTimeInSeconds', 'RebuyPercentage', 'RebuyMaxLimit', 'PullbackEntryPercentage',
            'PullbackEntryWaitTimeInSeconds', 'PLPercentage', 'ST_IndicatorEnabled', 'ST_AppliedPrice', 'ST_AtrPeriod',
            'ST_AtrMultiplier', 'ST_UseWicks'
        )
        self.select_string = ','.join(self.columns)

    def getStrategyParameters(self, timeframe, name="", optimizationId=0):
        strategyParameters = None
        try:
            sql = f"SELECT {self.select_string} FROM StrategyParameters WHERE Symbol = '' AND Name = %s AND OptimizationId = %s AND Timeframe = %s "
            values = (name, optimizationId, timeframe,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                result = dict(zip(self.columns, result))
                #print(result) # TODO: Remove.
                strategyParameters = StrategyParameters(**result)
        except:
            print(traceback.format_exc())
        return strategyParameters

    def getStrategyParametersById(self, spId):
        strategyParameters = None
        try:
            sql = f"SELECT {self.select_string} FROM StrategyParameters WHERE StrategyParametersId = %s"
            values = (spId,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                result = dict(zip(self.columns, result))
                print(result)  # TODO: Remove.
                strategyParameters = StrategyParameters(**result)
        except:
            print(traceback.format_exc())
        return strategyParameters

    def getStrategyParametersForBacktester(self, timeframe):
        strategyParameters = None
        try:
            sql = f"SELECT {self.select_string} FROM StrategyParameters WHERE Name = 'min' AND OptimizationId = 0 AND Timeframe = %s AND Symbol = '' "
            values = (timeframe,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                result = dict(zip(self.columns, result))
                print(result) # TODO: Remove.
                strategyParameters = StrategyParameters(**result)
        except:
            print(traceback.format_exc())
        return strategyParameters

    def getStrategyParametersBySymbolForTrader(self, timeframe, symbol):
        strategyParameters = None
        try:
            sql = f"SELECT {self.select_string} FROM StrategyParameters WHERE Name = '' AND OptimizationId = 0 AND Timeframe = %s AND Symbol = %s "
            values = (timeframe,symbol,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                result = dict(zip(self.columns, result))
                print(result)  # TODO: Remove.
                strategyParameters = StrategyParameters(**result)
        except:
            print(traceback.format_exc())
        return strategyParameters

    #Name='' are used by trader only
    def listStrategyParameters(self, timeframe):
        strategyParameters = None
        try:
            sql = f"SELECT {self.select_string} FROM StrategyParameters WHERE Timeframe = %s and Name = '' "
            values = (timeframe,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                strategyParameters = [StrategyParameters(**dict(zip(self.columns, result))) for result in results]

            """
            else:
                sql = "SELECT * FROM StrategyParameters WHERE Timeframe = %s"
                values = ("Default",)
                self.cursor.execute(sql, values)
                result = self.cursor.fetchone()
                if result:
                    strategyParameters = StrategyParameters(*result)
            """

        except:
            print(traceback.format_exc())
        return strategyParameters

    """
    def listStrategyParametersForBacktest(self, timeframe):
        strategyParameters = None
        try:
            sql = "SELECT * FROM StrategyParameters WHERE Timeframe = %s"
            values = (timeframe,)
            self.cursor.execute(sql, values)
            result = self.cursor.fetchone()
            if result:
                strategyParameters = StrategyParameters(*result)
            else:
                sql = "SELECT * FROM StrategyParameters WHERE Timeframe = %s"
                values = ("Default",)
                self.cursor.execute(sql, values)
                result = self.cursor.fetchone()
                if result:
                    strategyParameters = StrategyParameters(*result)

        except:
            print(traceback.format_exc())
        return strategyParameters
    """

    def listStrategyParametersForOptimization(self, optimizationId):
        strategyParameters = None
        try:
            sql = f"SELECT {self.select_string} FROM StrategyParameters WHERE OptimizationId = %s ORDER BY StrategyParametersId asc"
            values = (optimizationId,)
            self.cursor.execute(sql, values)
            results = self.cursor.fetchall()
            if results:
                strategyParameters = [StrategyParameters(**dict(zip(self.columns, result))) for result in results]
        except:
            print(traceback.format_exc())
        return strategyParameters


    def insertStrategyParameters(self, sp):
        spId = 0
        try:
            sql = "INSERT INTO StrategyParameters ("
            sql = sql + "Name, OptimizationId, Timeframe, Symbol, ROC_IndicatorEnabled, ROC_AppliedPrice_R, ROC_AppliedPrice_F, ROC_Period_R, ROC_Smoothing_R, ROC_Period_F,"
            sql = sql + "ROC_R_BuyIncreasePercentage, ROC_F_BuyDecreasePercentage, MPT_IndicatorEnabled, MPT_AppliedPrice, MPT_ShortMAPeriod,"
            sql = sql + "MPT_LongMAPeriod, NV_IndicatorEnabled, NV_IncreasePercentage, NV_MinNetVolume, TREND_IndicatorEnabled, TREND_AppliedPrice, TREND_LongEmaPeriod, TREND_ShortEmaPeriod, "
            sql = sql + "EMAX_IndicatorEnabled, EMAX_AppliedPrice, EMAX_LongEmaPeriod, EMAX_ShortEmaPeriod, "
            sql = sql + "VSTOP_IndicatorEnabled, VSTOP_AppliedPrice, VSTOP_Period, VSTOP_Factor, "
            sql = sql + "SELL_IndicatorEnabled, SELL_DecreasePercentage, SELL_Period, ROC_Smoothing_S, SELL_RSI_AppliedPrice, SELL_RSI_Period, SELL_RSI_UpperLevel,"
            sql = sql + "SELL_RSI_LowerLevel, SELL_Stoch_AppliedPrice, SELL_Stoch_KPeriod, SELL_Stoch_DPeriod, SELL_Stoch_Slowing,"
            sql = sql + "SELL_Stoch_UpperLevel, SELL_Stoch_LowerLevel, R_TradingEnabled, R_SL1Percentage, R_SL2Percentage,"
            sql = sql + "R_SLTimerInMinutes, R_TSLActivationPercentage, R_TSLTrailPercentage, F_TradingEnabled, F_SL1Percentage,"
            sql = sql + "F_SL2Percentage, F_SLTimerInMinutes, F_TSLActivationPercentage, F_TSLTrailPercentage, S_TradingEnabled,"
            sql = sql + "S_SL1Percentage, S_SL2Percentage, S_SLTimerInMinutes, S_TSLActivationPercentage, S_TSLTrailPercentage,"
            sql = sql + "TargetPercentage, RebuyTimeInSeconds, RebuyPercentage, RebuyMaxLimit, PullbackEntryPercentage, PullbackEntryWaitTimeInSeconds"

            sql = sql + ") "
            sql = sql + "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"




#69
            val = (
            sp.Name, sp.OptimizationId, sp.Timeframe, sp.Symbol, sp.ROC_IndicatorEnabled, sp.ROC_AppliedPrice_R, sp.ROC_AppliedPrice_F, sp.ROC_Period_R, sp.ROC_Smoothing_R, sp.ROC_Period_F,
            sp.ROC_R_BuyIncreasePercentage, sp.ROC_F_BuyDecreasePercentage, sp.MPT_IndicatorEnabled,
            sp.MPT_AppliedPrice, sp.MPT_ShortMAPeriod, sp.MPT_LongMAPeriod, sp.NV_IndicatorEnabled, sp.NV_IncreasePercentage, sp.NV_MinNetVolume,
            sp.TREND_IndicatorEnabled, sp.TREND_AppliedPrice, sp.TREND_LongEmaPeriod, sp.TREND_ShortEmaPeriod,
            sp.EMAX_IndicatorEnabled, sp.EMAX_AppliedPrice,sp.EMAX_LongEmaPeriod,sp.EMAX_ShortEmaPeriod,
            sp.VSTOP_IndicatorEnabled, sp.VSTOP_AppliedPrice, sp.VSTOP_Period, sp.VSTOP_Factor,
            sp.SELL_IndicatorEnabled, sp.SELL_DecreasePercentage, sp.SELL_Period, sp.ROC_Smoothing_S, sp.SELL_RSI_AppliedPrice,
            sp.SELL_RSI_Period, sp.SELL_RSI_UpperLevel, sp.SELL_RSI_LowerLevel, sp.SELL_Stoch_AppliedPrice,
            sp.SELL_Stoch_KPeriod, sp.SELL_Stoch_DPeriod, sp.SELL_Stoch_Slowing, sp.SELL_Stoch_UpperLevel,
            sp.SELL_Stoch_LowerLevel, sp.R_TradingEnabled, sp.R_SL1Percentage, sp.R_SL2Percentage,
            sp.R_SLTimerInMinutes, sp.R_TSLActivationPercentage, sp.R_TSLTrailPercentage, sp.F_TradingEnabled,
            sp.F_SL1Percentage, sp.F_SL2Percentage, sp.F_SLTimerInMinutes, sp.F_TSLActivationPercentage,
            sp.F_TSLTrailPercentage, sp.S_TradingEnabled, sp.S_SL1Percentage, sp.S_SL2Percentage, sp.S_SLTimerInMinutes,
            sp.S_TSLActivationPercentage, sp.S_TSLTrailPercentage,
            sp.TargetPercentage, sp.RebuyTimeInSeconds, sp.RebuyPercentage, sp.RebuyMaxLimit, sp.PullbackEntryPercentage, sp.PullbackEntryWaitTimeInSeconds,

            )

            self.cursor.execute(sql, val)
            spId = self.cursor.lastrowid
            self.db.commit()

        except:
            print(traceback.format_exc())
        return spId

    def updateStrategyParameters(self, sp):
        strategyParameters = None

        try:
            sql = "UPDATE StrategyParameters SET "

            sql = sql + "ROC_IndicatorEnabled = %s, ROC_AppliedPrice_R = %s, ROC_AppliedPrice_F = %s, ROC_Period_R = %s, ROC_Smoothing_R = %s, ROC_Period_F = %s, ROC_R_BuyIncreasePercentage = %s, ROC_F_BuyDecreasePercentage = %s, "
            sql = sql + "MPT_IndicatorEnabled = %s, MPT_AppliedPrice = %s, MPT_ShortMAPeriod = %s, MPT_LongMAPeriod = %s, "
            sql = sql + "NV_IndicatorEnabled = %s, NV_IncreasePercentage = %s, NV_MinNetVolume = %s, "
            sql = sql + "TREND_IndicatorEnabled = %s, TREND_AppliedPrice = %s, TREND_LongEmaPeriod = %s, TREND_ShortEmaPeriod = %s, "
            sql = sql + "EMAX_IndicatorEnabled = %s, EMAX_AppliedPrice = %s, EMAX_LongEmaPeriod = %s, EMAX_ShortEmaPeriod = %s, "
            sql = sql + "VSTOP_IndicatorEnabled = %s, VSTOP_AppliedPrice = %s, VSTOP_Period = %s, VSTOP_Factor = %s, "
            sql = sql + "SELL_IndicatorEnabled = %s, SELL_DecreasePercentage = %s,SELL_Period = %s, ROC_Smoothing_S = %s, "
            sql = sql + "SELL_RSI_AppliedPrice = %s, SELL_RSI_Period = %s, SELL_RSI_UpperLevel = %s, SELL_RSI_LowerLevel = %s, "
            sql = sql + "SELL_Stoch_AppliedPrice = %s, SELL_Stoch_KPeriod = %s, SELL_Stoch_DPeriod = %s, SELL_Stoch_Slowing = %s, SELL_Stoch_UpperLevel = %s, SELL_Stoch_LowerLevel = %s, "
            sql = sql + "R_TradingEnabled = %s, R_SL1Percentage = %s, R_SL2Percentage = %s, R_SLTimerInMinutes = %s, R_TSLActivationPercentage = %s, R_TSLTrailPercentage = %s, "
            sql = sql + "F_TradingEnabled = %s, F_SL1Percentage = %s, F_SL2Percentage = %s, F_SLTimerInMinutes = %s, F_TSLActivationPercentage = %s, F_TSLTrailPercentage = %s,"
            sql = sql + "S_TradingEnabled = %s, S_SL1Percentage = %s, S_SL2Percentage = %s, S_SLTimerInMinutes = %s, S_TSLActivationPercentage = %s, S_TSLTrailPercentage = %s,"
            sql = sql + "TargetPercentage = %s, RebuyTimeInSeconds = %s, RebuyPercentage = %s, RebuyMaxLimit = %s, PullbackEntryPercentage = %s, PullbackEntryWaitTimeInSeconds = %s"

            sql = sql + " WHERE OptimizationId = %s AND Name = %s AND Timeframe = %s AND Symbol = %s"

            val = (
            sp.ROC_IndicatorEnabled, sp.ROC_AppliedPrice_R, sp.ROC_AppliedPrice_F, sp.ROC_Period_R, sp.ROC_Smoothing_R, sp.ROC_Period_F,
            sp.ROC_R_BuyIncreasePercentage, sp.ROC_F_BuyDecreasePercentage, sp.MPT_IndicatorEnabled,
            sp.MPT_AppliedPrice, sp.MPT_ShortMAPeriod, sp.MPT_LongMAPeriod, sp.NV_IndicatorEnabled, sp.NV_IncreasePercentage, sp.NV_MinNetVolume,
            sp.TREND_IndicatorEnabled, sp.TREND_AppliedPrice, sp.TREND_LongEmaPeriod, sp.TREND_ShortEmaPeriod,
            sp.EMAX_IndicatorEnabled, sp.EMAX_AppliedPrice, sp.EMAX_LongEmaPeriod, sp.EMAX_ShortEmaPeriod,
            sp.VSTOP_IndicatorEnabled, sp.VSTOP_AppliedPrice, sp.VSTOP_Period, sp.VSTOP_Factor,
            sp.SELL_IndicatorEnabled, sp.SELL_DecreasePercentage, sp.SELL_Period, sp.ROC_Smoothing_S, sp.SELL_RSI_AppliedPrice,
            sp.SELL_RSI_Period, sp.SELL_RSI_UpperLevel, sp.SELL_RSI_LowerLevel, sp.SELL_Stoch_AppliedPrice,
            sp.SELL_Stoch_KPeriod, sp.SELL_Stoch_DPeriod, sp.SELL_Stoch_Slowing, sp.SELL_Stoch_UpperLevel,
            sp.SELL_Stoch_LowerLevel, sp.R_TradingEnabled, sp.R_SL1Percentage, sp.R_SL2Percentage,
            sp.R_SLTimerInMinutes, sp.R_TSLActivationPercentage, sp.R_TSLTrailPercentage, sp.F_TradingEnabled,
            sp.F_SL1Percentage, sp.F_SL2Percentage, sp.F_SLTimerInMinutes, sp.F_TSLActivationPercentage,
            sp.F_TSLTrailPercentage, sp.S_TradingEnabled, sp.S_SL1Percentage, sp.S_SL2Percentage, sp.S_SLTimerInMinutes,
            sp.S_TSLActivationPercentage, sp.S_TSLTrailPercentage,
            sp.TargetPercentage, sp.RebuyTimeInSeconds, sp.RebuyPercentage,sp.RebuyMaxLimit, sp.PullbackEntryPercentage, sp.PullbackEntryWaitTimeInSeconds,  sp.OptimizationId,  sp.Name, sp.Timeframe, sp.Symbol,

            )

            self.cursor.execute(sql, val)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return strategyParameters


    def deleteStrategyParameters(self, timeframe, name="min", optimizationId=0, symbol=""):
        strategyParameters = None
        try:
            sql = "DELETE FROM StrategyParameters WHERE Name = %s AND OptimizationId = %s AND Timeframe = %s AND Symbol = %s "
            values = (name, optimizationId, timeframe,symbol)
            self.cursor.execute(sql, values)
            self.db.commit()

        except:
            print(traceback.format_exc())
        return strategyParameters

    def set(self, sp, convertAppliedPrices):
        strPar = StrategyParameters()

        strPar.StrategyParametersId = sp.StrategyParametersId
        strPar.Name = sp.Name
        strPar.OptimizationId = sp.OptimizationId
        strPar.Timeframe = sp.Timeframe
        strPar.Symbol = sp.Symbol

        strPar.ROC_IndicatorEnabled = sp.ROC_IndicatorEnabled
        strPar.ROC_AppliedPrice_R = sp.ROC_AppliedPrice_R
        strPar.ROC_AppliedPrice_F = sp.ROC_AppliedPrice_F
        strPar.ROC_Period_R = sp.ROC_Period_R
        strPar.ROC_Smoothing_R = sp.ROC_Smoothing_R
        strPar.ROC_Period_F = sp.ROC_Period_F
        strPar.ROC_R_BuyIncreasePercentage = sp.ROC_R_BuyIncreasePercentage
        strPar.ROC_F_BuyDecreasePercentage = sp.ROC_F_BuyDecreasePercentage
        strPar.MPT_IndicatorEnabled = sp.MPT_IndicatorEnabled
        strPar.MPT_AppliedPrice = sp.MPT_AppliedPrice
        strPar.MPT_ShortMAPeriod = sp.MPT_ShortMAPeriod
        strPar.MPT_LongMAPeriod = sp.MPT_LongMAPeriod
        strPar.NV_IndicatorEnabled = sp.NV_IndicatorEnabled
        strPar.NV_IncreasePercentage = sp.NV_IncreasePercentage
        strPar.NV_MinNetVolume = sp.NV_MinNetVolume

        strPar.TREND_IndicatorEnabled = sp.TREND_IndicatorEnabled
        strPar.TREND_AppliedPrice = sp.TREND_AppliedPrice
        strPar.TREND_LongEmaPeriod = sp.TREND_LongEmaPeriod
        strPar.TREND_ShortEmaPeriod = sp.TREND_ShortEmaPeriod

        strPar.EMAX_IndicatorEnabled = sp.EMAX_IndicatorEnabled
        strPar.EMAX_AppliedPrice = sp.EMAX_AppliedPrice
        strPar.EMAX_LongEmaPeriod = sp.EMAX_LongEmaPeriod
        strPar.EMAX_ShortEmaPeriod = sp.EMAX_ShortEmaPeriod

        strPar.VSTOP_IndicatorEnabled = sp.VSTOP_IndicatorEnabled
        strPar.VSTOP_AppliedPrice = sp.VSTOP_AppliedPrice
        strPar.VSTOP_Period = sp.VSTOP_Period
        strPar.VSTOP_Factor = sp.VSTOP_Factor

        strPar.SELL_IndicatorEnabled = sp.SELL_IndicatorEnabled
        strPar.SELL_DecreasePercentage = sp.SELL_DecreasePercentage
        strPar.SELL_Period = sp.SELL_Period
        strPar.ROC_Smoothing_S = sp.ROC_Smoothing_S

        strPar.SELL_RSI_AppliedPrice = sp.SELL_RSI_AppliedPrice
        strPar.SELL_RSI_Period = sp.SELL_RSI_Period
        strPar.SELL_RSI_UpperLevel = sp.SELL_RSI_UpperLevel
        strPar.SELL_RSI_LowerLevel = sp.SELL_RSI_LowerLevel

        strPar.SELL_Stoch_AppliedPrice = sp.SELL_Stoch_AppliedPrice
        strPar.SELL_Stoch_KPeriod = sp.SELL_Stoch_KPeriod
        strPar.SELL_Stoch_DPeriod = sp.SELL_Stoch_DPeriod
        strPar.SELL_Stoch_Slowing = sp.SELL_Stoch_Slowing
        strPar.SELL_Stoch_UpperLevel = sp.SELL_Stoch_UpperLevel
        strPar.SELL_Stoch_LowerLevel = sp.SELL_Stoch_LowerLevel

        strPar.R_TradingEnabled = sp.R_TradingEnabled
        strPar.R_SL1Percentage = sp.R_SL1Percentage
        strPar.R_SL2Percentage = sp.R_SL2Percentage
        strPar.R_SLTimerInMinutes = sp.R_SLTimerInMinutes
        strPar.R_TSLActivationPercentage = sp.R_TSLActivationPercentage
        strPar.R_TSLTrailPercentage = sp.R_TSLTrailPercentage

        strPar.F_TradingEnabled = sp.F_TradingEnabled
        strPar.F_SL1Percentage = sp.F_SL1Percentage
        strPar.F_SL2Percentage = sp.F_SL2Percentage
        strPar.F_SLTimerInMinutes = sp.F_SLTimerInMinutes
        strPar.F_TSLActivationPercentage = sp.F_TSLActivationPercentage
        strPar.F_TSLTrailPercentage = sp.F_TSLTrailPercentage

        strPar.S_TradingEnabled = sp.S_TradingEnabled
        strPar.S_SL1Percentage = sp.S_SL1Percentage
        strPar.S_SL2Percentage = sp.S_SL2Percentage
        strPar.S_SLTimerInMinutes = sp.S_SLTimerInMinutes
        strPar.S_TSLActivationPercentage = sp.S_TSLActivationPercentage
        strPar.S_TSLTrailPercentage = sp.S_TSLTrailPercentage

        strPar.TargetPercentage = sp.TargetPercentage
        strPar.RebuyTimeInSeconds = sp.RebuyTimeInSeconds
        strPar.RebuyPercentage = sp.RebuyPercentage
        strPar.RebuyMaxLimit = sp.RebuyMaxLimit
        strPar.PullbackEntryPercentage = sp.PullbackEntryPercentage
        strPar.PullbackEntryWaitTimeInSeconds = sp.PullbackEntryWaitTimeInSeconds
        strPar.PLPercentage = sp.PLPercentage

        if convertAppliedPrices:
            strPar.ROC_AppliedPrice_R = self.convertAppliedPrice(strPar.ROC_AppliedPrice_R)
            strPar.ROC_AppliedPrice_F = self.convertAppliedPrice(strPar.ROC_AppliedPrice_F)
            strPar.MPT_AppliedPrice = self.convertAppliedPrice(strPar.MPT_AppliedPrice)
            strPar.TREND_AppliedPrice = self.convertAppliedPrice(strPar.TREND_AppliedPrice)
            strPar.EMAX_AppliedPrice = self.convertAppliedPrice(strPar.EMAX_AppliedPrice)
            strPar.VSTOP_AppliedPrice = self.convertAppliedPrice(strPar.VSTOP_AppliedPrice)
            strPar.SELL_RSI_AppliedPrice = self.convertAppliedPrice(strPar.SELL_RSI_AppliedPrice)



        return strPar

    def convertAppliedPrice(self, value):
        if value == "0":
            return "close"
        if value == "1":
            return "open"
        if value == "2":
            return "high"
        if value == "3":
            return "low"
        return value

    def convertStrategyParametersToString(self, sp):
        result = ""

        result = result + "ROC_IndicatorEnabled"  + ":" + str(sp.ROC_IndicatorEnabled) + ", "
        result = result + "ROC_AppliedPrice_R" + ":" + str(sp.ROC_AppliedPrice_R) + ", "
        #result = result + "ROC_AppliedPrice_F" + ":" + str(sp.ROC_AppliedPrice_F) + ", "
        result = result + "ROC_Period_R" + ":" + str(sp.ROC_Period_R) + ", "
        result = result + "ROC_Smoothing_R" + ":" + str(sp.ROC_Smoothing_R) + ", "
        #result = result + "ROC_Period_F" + ":" + str(sp.ROC_Period_F) + ", "
        result = result + "ROC_R_BuyIncreasePercentage" + ":" + str(sp.ROC_R_BuyIncreasePercentage) + ", "
        #result = result + "ROC_F_BuyDecreasePercentage" + ":" + str(sp.ROC_F_BuyDecreasePercentage) + ", "
        result = result + "MPT_IndicatorEnabled" + ":" + str(sp.MPT_IndicatorEnabled) + ", "
        result = result + "MPT_AppliedPrice" + ":" + str(sp.MPT_AppliedPrice) + ", "
        result = result + "MPT_ShortMAPeriod" + ":" + str(sp.MPT_ShortMAPeriod) + ", "
        result = result + "MPT_LongMAPeriod" + ":" + str(sp.MPT_LongMAPeriod) + ", "
        #result = result + "NV_IndicatorEnabled" + ":" + str(sp.NV_IndicatorEnabled) + ", "
        #result = result + "NV_IncreasePercentage" + ":" + str(sp.NV_IncreasePercentage) + ", "
        #result = result + "NV_MinNetVolume" + ":" + str(sp.NV_MinNetVolume) + ", "

        result = result + "TREND_IndicatorEnabled" + ":" + str(sp.TREND_IndicatorEnabled) + ", "
        result = result + "TREND_AppliedPrice" + ":" + str(sp.TREND_AppliedPrice) + ", "
        result = result + "TREND_LongEmaPeriod" + ":" + str(sp.TREND_LongEmaPeriod) + ", "
        result = result + "TREND_ShortEmaPeriod" + ":" + str(sp.TREND_ShortEmaPeriod) + ", "

        result = result + "EMAX_IndicatorEnabled" + ":" + str(sp.EMAX_IndicatorEnabled) + ", "
        result = result + "EMAX_AppliedPrice" + ":" + str(sp.EMAX_AppliedPrice) + ", "
        result = result + "EMAX_LongEmaPeriod" + ":" + str(sp.EMAX_LongEmaPeriod) + ", "
        result = result + "EMAX_ShortEmaPeriod" + ":" + str(sp.EMAX_ShortEmaPeriod) + ", "

        result = result + "VSTOP_IndicatorEnabled" + ":" + str(sp.VSTOP_IndicatorEnabled) + ", "
        result = result + "VSTOP_AppliedPrice" + ":" + str(sp.VSTOP_AppliedPrice) + ", "
        result = result + "VSTOP_Period" + ":" + str(sp.VSTOP_Period) + ", "
        result = result + "VSTOP_Factor" + ":" + str(sp.VSTOP_Factor) + ", "

        result = result + "SELL_IndicatorEnabled" + ":" + str(sp.SELL_IndicatorEnabled) + ", "
        result = result + "SELL_DecreasePercentage" + ":" + str(sp.SELL_DecreasePercentage) + ", "
        result = result + "SELL_Period" + ":" + str(sp.SELL_Period) + ", "
        result = result + "ROC_Smoothing_S" + ":" + str(sp.ROC_Smoothing_S) + ", "

        result = result + "SELL_RSI_AppliedPrice" + ":" + str(sp.SELL_RSI_AppliedPrice) + ", "
        #result = result + "SELL_RSI_Period" + ":" + str(sp.SELL_RSI_Period) + ", "
        #result = result + "SELL_RSI_UpperLevel" + ":" + str(sp.SELL_RSI_UpperLevel) + ", "
        #result = result + "SELL_RSI_LowerLevel" + ":" + str(sp.SELL_RSI_LowerLevel) + ", "

        #result = result + "SELL_Stoch_AppliedPrice" + ":" + str(sp.SELL_Stoch_AppliedPrice) + ", "
        #result = result + "SELL_Stoch_KPeriod" + ":" + str(sp.SELL_Stoch_KPeriod) + ", "
        #result = result + "SELL_Stoch_DPeriod" + ":" + str(sp.SELL_Stoch_DPeriod) + ", "
        #result = result + "SELL_Stoch_Slowing" + ":" + str(sp.SELL_Stoch_Slowing) + ", "
        #result = result + "SELL_Stoch_UpperLevel" + ":" + str(sp.SELL_Stoch_UpperLevel) + ", "
        #result = result + "SELL_Stoch_LowerLevel" + ":" + str(sp.SELL_Stoch_LowerLevel) + ", "

        result = result + "R_TradingEnabled" + ":" + str(sp.R_TradingEnabled) + ", "
        result = result + "R_SL1Percentage" + ":" + str(sp.R_SL1Percentage) + ", "
        result = result + "R_SL2Percentage" + ":" + str(sp.R_SL2Percentage) + ", "
        result = result + "R_SLTimerInMinutes" + ":" + str(sp.R_SLTimerInMinutes) + ", "
        result = result + "R_TSLActivationPercentage" + ":" + str(sp.R_TSLActivationPercentage) + ", "
        result = result + "R_TSLTrailPercentage" + ":" + str(sp.R_TSLTrailPercentage) + ", "

        #result = result + "F_TradingEnabled" + ":" + str(sp.F_TradingEnabled) + ", "
        #result = result + "F_SL1Percentage" + ":" + str(sp.F_SL1Percentage) + ", "
        #result = result + "F_SL2Percentage" + ":" + str(sp.F_SL2Percentage) + ", "
        #result = result + "F_SLTimerInMinutes" + ":" + str(sp.F_SLTimerInMinutes) + ", "
        #result = result + "F_TSLActivationPercentage" + ":" + str(sp.F_TSLActivationPercentage) + ", "
        #result = result + "F_TSLTrailPercentage" + ":" + str(sp.F_TSLTrailPercentage) + ", "

        result = result + "S_TradingEnabled" + ":" + str(sp.S_TradingEnabled) + ", "
        result = result + "S_SL1Percentage" + ":" + str(sp.S_SL1Percentage) + ", "
        result = result + "S_SL2Percentage" + ":" + str(sp.S_SL2Percentage) + ", "
        result = result + "S_SLTimerInMinutes" + ":" + str(sp.S_SLTimerInMinutes) + ", "
        result = result + "S_TSLActivationPercentage" + ":" + str(sp.S_TSLActivationPercentage) + ", "
        result = result + "S_TSLTrailPercentage" + ":" + str(sp.S_TSLTrailPercentage) + ", "

        #result = result + "TargetPercentage" + ":" + str(sp.TargetPercentage) + ", "
        result = result + "RebuyTimeInSeconds" + ":" + str(sp.RebuyTimeInSeconds) + ", "
        result = result + "RebuyPercentage" + ":" + str(sp.RebuyPercentage) + ", "
        result = result + "RebuyMaxLimit" + ":" + str(sp.RebuyMaxLimit) + ", "
        #result = result + "PullbackEntryPercentage" + ":" + str(sp.PullbackEntryPercentage) + ", "
        #result = result + "PullbackEntryWaitTimeInSeconds" + ":" + str(sp.PullbackEntryWaitTimeInSeconds) + ", "

        return result
