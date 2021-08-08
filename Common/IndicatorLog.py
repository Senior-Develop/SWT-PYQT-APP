class IndicatorLog:
    def __init__(self, IndicatorLogId=0
                 , Symbol=""
                 , CreatedDate=None
                 , CandleDate=None
                 , CurrentPrice=0
                 , R_ROC_Value=0
                 , R_ROC_Signal=False
                 , R_MPT_Value=0
                 , R_NV_BuyPercent=0
                 , R_NV_SellPercent=0
                 , R_NV_NetVolume=0
                 , R_ROC_MPT_Signal=False
                 , Trend_Signal=False
                 , EMAX_Signal=False
                 , VSTOP_Signal=False
                 , R_NV_Signal=False
                 , R_Signal=False
                 , F_ROC_Value=0
                 , F_ROC_Signal=False
                 , F_ROC_MPT_Signal=False
                 , F_NV_Signal=False
                 , F_Signal=False
                 , S_ROC_Value=0
                 , S_Rsi_Value=0
                 , S_Stoch_Value=0
                 , S_ROC_Signal=False
                 , S_Rsi_Signal=False
                 , S_Stoch_Signal=False
                 , S_Signal=False
                 , R_Open_Count=0
                 , F_Open_Count=0
                 , S_Open_Count=0
                 , BacktestId=0
                 ):

        self.IndicatorLogId = int(IndicatorLogId)
        self.Symbol = Symbol
        self.CreatedDate = CreatedDate
        self.CandleDate = CandleDate
        self.CurrentPrice = CurrentPrice
        self.R_ROC_Value = R_ROC_Value
        self.R_ROC_Signal = R_ROC_Signal
        self.R_NV_BuyPercent = R_NV_BuyPercent
        self.R_NV_SellPercent = R_NV_SellPercent
        self.R_NV_NetVolume = R_NV_NetVolume
        self.R_MPT_Value = R_MPT_Value
        self.R_ROC_MPT_Signal = R_ROC_MPT_Signal
        self.Trend_Signal = Trend_Signal
        self.EMAX_Signal = EMAX_Signal
        self.VSTOP_Signal = VSTOP_Signal
        self.R_NV_Signal = R_NV_Signal
        self.R_Signal = R_Signal
        self.F_ROC_Value = F_ROC_Value
        self.F_ROC_Signal = F_ROC_Signal
        self.F_ROC_MPT_Signal = F_ROC_MPT_Signal
        self.F_NV_Signal = F_NV_Signal
        self.F_Signal = F_Signal
        self.S_ROC_Value = S_ROC_Value
        self.S_Rsi_Value = S_Rsi_Value
        self.S_Stoch_Value = S_Stoch_Value
        self.S_ROC_Signal = S_ROC_Signal
        self.S_Rsi_Signal = S_Rsi_Signal
        self.S_Stoch_Signal = S_Stoch_Signal
        self.S_Signal = S_Signal
        self.R_Open_Count = R_Open_Count
        self.F_Open_Count = F_Open_Count
        self.S_Open_Count = S_Open_Count
        self.BacktestId = BacktestId


    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
