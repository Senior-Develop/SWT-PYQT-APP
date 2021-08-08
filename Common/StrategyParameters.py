class StrategyParameters:





    def __init__(self
                 , StrategyParametersId=0
                 , Name=""
                 , OptimizationId=0
                 , Timeframe=""
                 , Symbol = ""

                 , ROC_IndicatorEnabled=False
                 , ROC_AppliedPrice_R="close"
                 , ROC_AppliedPrice_F="close"
                 , ROC_Period_R=0
                 , ROC_Smoothing_R=0
                 , ROC_Period_F=0
                 , ROC_R_BuyIncreasePercentage=0
                 , ROC_F_BuyDecreasePercentage=0
                 , MPT_IndicatorEnabled=False
                 , MPT_AppliedPrice="close"
                 , MPT_ShortMAPeriod=0
                 , MPT_LongMAPeriod=0
                 , NV_IndicatorEnabled=False
                 , NV_IncreasePercentage=0
                 , NV_MinNetVolume=0
                 , TREND_IndicatorEnabled=False
                 , TREND_AppliedPrice="close"
                 , TREND_LongEmaPeriod=0
                 , TREND_ShortEmaPeriod=0
                 , EMAX_IndicatorEnabled=False
                 , EMAX_AppliedPrice="close"
                 , EMAX_LongEmaPeriod=0
                 , EMAX_ShortEmaPeriod=0
                 , VSTOP_IndicatorEnabled=False
                 , VSTOP_AppliedPrice="close"
                 , VSTOP_Period=0
                 , VSTOP_Factor=0
                 , SELL_IndicatorEnabled=False
                 , SELL_DecreasePercentage=0
                 , SELL_Period=0
                 , ROC_Smoothing_S=0
                 , SELL_RSI_AppliedPrice="close"
                 , SELL_RSI_Period=0
                 , SELL_RSI_UpperLevel=0
                 , SELL_RSI_LowerLevel=0
                 , SELL_Stoch_AppliedPrice="closeclose"
                 , SELL_Stoch_KPeriod=0
                 , SELL_Stoch_DPeriod=0
                 , SELL_Stoch_Slowing=0
                 , SELL_Stoch_UpperLevel=0
                 , SELL_Stoch_LowerLevel=0
                 , R_TradingEnabled=False
                 , R_SL1Percentage=0
                 , R_SL2Percentage=0
                 , R_SLTimerInMinutes=0
                 , R_TSLActivationPercentage=0
                 , R_TSLTrailPercentage=0
                 , F_TradingEnabled=False
                 , F_SL1Percentage=0
                 , F_SL2Percentage=0
                 , F_SLTimerInMinutes=0
                 , F_TSLActivationPercentage=0
                 , F_TSLTrailPercentage=0
                 , S_TradingEnabled=False
                 , S_SL1Percentage=0
                 , S_SL2Percentage=0
                 , S_SLTimerInMinutes=0
                 , S_TSLActivationPercentage=0
                 , S_TSLTrailPercentage=0

                 , TargetPercentage=0
                 , RebuyTimeInSeconds=0
                 , RebuyPercentage=0
                 , RebuyMaxLimit=0
                 , PullbackEntryPercentage=0
                 , PullbackEntryWaitTimeInSeconds=0

                 , PLPercentage=0
                 , ST_IndicatorEnabled=False
                 , ST_AppliedPrice="close"
                 , ST_AtrPeriod=0
                 , ST_AtrMultiplier=0
                 , ST_UseWicks=0




                 ):
        self.StrategyParametersId = int(StrategyParametersId)
        self.Name = Name
        self.OptimizationId = OptimizationId
        self.Timeframe = Timeframe
        self.Symbol = Symbol


        self.ROC_IndicatorEnabled = ROC_IndicatorEnabled
        self.ROC_AppliedPrice_R = ROC_AppliedPrice_R
        self.ROC_AppliedPrice_F = ROC_AppliedPrice_F
        self.ROC_Period_R = ROC_Period_R
        self.ROC_Smoothing_R = ROC_Smoothing_R
        self.ROC_Period_F = ROC_Period_F
        self.ROC_R_BuyIncreasePercentage = ROC_R_BuyIncreasePercentage
        self.ROC_F_BuyDecreasePercentage = ROC_F_BuyDecreasePercentage
        self.MPT_IndicatorEnabled = MPT_IndicatorEnabled
        self.MPT_AppliedPrice = MPT_AppliedPrice
        self.MPT_ShortMAPeriod = MPT_ShortMAPeriod
        self.MPT_LongMAPeriod = MPT_LongMAPeriod
        self.NV_IndicatorEnabled = NV_IndicatorEnabled
        self.NV_IncreasePercentage = NV_IncreasePercentage
        self.NV_MinNetVolume = NV_MinNetVolume

        self.TREND_IndicatorEnabled = TREND_IndicatorEnabled
        self.TREND_AppliedPrice = TREND_AppliedPrice
        self.TREND_LongEmaPeriod = TREND_LongEmaPeriod
        self.TREND_ShortEmaPeriod = TREND_ShortEmaPeriod

        self.EMAX_IndicatorEnabled = EMAX_IndicatorEnabled
        self.EMAX_AppliedPrice = EMAX_AppliedPrice
        self.EMAX_LongEmaPeriod = EMAX_LongEmaPeriod
        self.EMAX_ShortEmaPeriod = EMAX_ShortEmaPeriod

        self.ST_IndicatorEnabled = ST_IndicatorEnabled
        self.ST_AppliedPrice = ST_AppliedPrice
        self.ST_AtrPeriod = ST_AtrPeriod
        self.ST_AtrMultiplier = ST_AtrMultiplier
        self.ST_UseWicks = ST_UseWicks

        self.VSTOP_IndicatorEnabled = VSTOP_IndicatorEnabled
        self.VSTOP_AppliedPrice = VSTOP_AppliedPrice
        self.VSTOP_Period = VSTOP_Period
        self.VSTOP_Factor = VSTOP_Factor

        self.SELL_IndicatorEnabled = SELL_IndicatorEnabled
        self.SELL_DecreasePercentage = SELL_DecreasePercentage
        self.SELL_Period = SELL_Period


        self.SELL_RSI_AppliedPrice = SELL_RSI_AppliedPrice
        self.SELL_RSI_Period = SELL_RSI_Period
        self.ROC_Smoothing_S = ROC_Smoothing_S
        self.SELL_RSI_UpperLevel = SELL_RSI_UpperLevel
        self.SELL_RSI_LowerLevel = SELL_RSI_LowerLevel

        self.SELL_Stoch_AppliedPrice = SELL_Stoch_AppliedPrice
        self.SELL_Stoch_KPeriod = SELL_Stoch_KPeriod
        self.SELL_Stoch_DPeriod = SELL_Stoch_DPeriod
        self.SELL_Stoch_Slowing = SELL_Stoch_Slowing
        self.SELL_Stoch_UpperLevel = SELL_Stoch_UpperLevel
        self.SELL_Stoch_LowerLevel = SELL_Stoch_LowerLevel

        self.R_TradingEnabled = R_TradingEnabled
        self.R_SL1Percentage = R_SL1Percentage
        self.R_SL2Percentage = R_SL2Percentage
        self.R_SLTimerInMinutes = R_SLTimerInMinutes
        self.R_TSLActivationPercentage = R_TSLActivationPercentage
        self.R_TSLTrailPercentage = R_TSLTrailPercentage

        self.F_TradingEnabled = F_TradingEnabled
        self.F_SL1Percentage = F_SL1Percentage
        self.F_SL2Percentage = F_SL2Percentage
        self.F_SLTimerInMinutes = F_SLTimerInMinutes
        self.F_TSLActivationPercentage = F_TSLActivationPercentage
        self.F_TSLTrailPercentage = F_TSLTrailPercentage

        self.S_TradingEnabled = S_TradingEnabled
        self.S_SL1Percentage = S_SL1Percentage
        self.S_SL2Percentage = S_SL2Percentage
        self.S_SLTimerInMinutes = S_SLTimerInMinutes
        self.S_TSLActivationPercentage = S_TSLActivationPercentage
        self.S_TSLTrailPercentage = S_TSLTrailPercentage

        self.TargetPercentage = TargetPercentage
        self.RebuyTimeInSeconds = RebuyTimeInSeconds
        self.RebuyPercentage = RebuyPercentage
        self.RebuyMaxLimit = RebuyMaxLimit
        self.PullbackEntryPercentage = PullbackEntryPercentage
        self.PullbackEntryWaitTimeInSeconds = PullbackEntryWaitTimeInSeconds

        self.PLPercentage = PLPercentage


    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


