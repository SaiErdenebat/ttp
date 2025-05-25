import plotly.io as pio

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import math
import http.client


st.set_page_config(
    layout="wide",
)
################################################

payload = {
    'username': "",
    'password': ""
}

##################################################
# functions
##################################################

def barChart(tempDf, x, y):
    if(y == 'profitAndLoss'):
        tempDf['positive'] = np.where(tempDf[y] >=0, True, False)
    else:   
        tempDf['positive'] = np.where(tempDf[x] >=0, True, False)
    fig = px.bar(tempDf, x=x, y=y, color='positive', color_discrete_map={True: 'green', False:'red'}, text_auto='.2s')
    fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    fig.update_xaxes(categoryorder='category ascending')
    st.plotly_chart(fig)
##################################################


def getMetrics(tempDf, pnl, fee):
    ###################################################################
    # Trade Metrics 
    ###################################################################
    numOfWinners = tempDf[tempDf[pnl] > 0].count()[0]
    numOfLosers = tempDf[tempDf[pnl] < 0].shape[0]
    totalTrades = numOfWinners + numOfLosers
    
    netProfitOrLoss = tempDf[pnl].sum().round()
    averageWin = (tempDf[tempDf[pnl] > 0][pnl].sum()/numOfWinners).round()
    averageLoss = (tempDf[tempDf[pnl] < 0][pnl].sum()/numOfLosers).round()
    commissions = tempDf[fee].sum().round()
    
    subCol1, subCol2, = st.columns(2)
    with subCol1: 
        metricData = [
            ['Net Profit / Loss', netProfitOrLoss], 
            ['Winners', numOfWinners], 
            ['Losers', numOfLosers],
            ['Average Win', averageWin],
            ['Average Loss', averageLoss],
            ['Commissions', commissions],
            ]
        metricDf = pd.DataFrame(metricData, columns=['Metrics', ""])
        st.dataframe(metricDf, hide_index=True)
    with subCol2: 
        winRate = "{:.1%}".format(numOfWinners/totalTrades)
        st.metric('Win Rate', winRate)
        pnlRatio = averageWin/averageLoss * -1
        st.metric('Profit/Loss Ratio', round(pnlRatio, 2))
        
        winPct = numOfWinners/totalTrades 
        LossPct = numOfLosers/totalTrades 
        expectancy = winPct * averageWin - LossPct * (averageLoss*-1)
        #st.metric('Expectancy', expectancy if(expectancy == 0) else round(expectancy))
       

        if not math.isnan(expectancy):
            st.metric('Expectancy', math.floor(expectancy))
        else:
            st.metric('Expectancy', expectancy)
        
        

try:
    
    
    loginUrl=('https://api.tradethepool.com/authentication/login') 
    payload['username'] = st.secrets.db_username
    payload['password'] = st.secrets.db_password


    s = requests.Session()
    p = s.post(loginUrl, data=payload)
    #token = p.json()['data']['token']
    
    
 
    #title = st.text_input("Account Number")

    accounts = [
        #title
        #"112135",
        "91674",
        "96001",
        "96588"
    ]
    
    df = pd.DataFrame()
    for account in accounts:
        tradesUrl = ("https://api.tradethepool.com/position/closed/" + str(account) + "?page=1&limit=10000&sort[field]=closeDate&sort[direction]=-1")
        #r = s.get(tradesUrl, headers={'Authorization': "Bearer {}".format(token)})
        r = s.get(tradesUrl)
        temp_df = pd.json_normalize(r.json()['data']['results'])
        df = pd.concat([df, temp_df])
    ###
    ### printing columns
    ###
    # Index(['_id', 'accountId', 'externalId', 'closeDate', 'createdAt', 'entry',
    #    'exit', 'fee', 'invalidReasons', 'isClosed', 'isValid', 'openDate',
    #    'profitAndLoss', 'quantity', 'routeId', 'side', 'swap', 'symbol',
    #    'tradableInstrumentId', 'updatedAt', 'id'],


    df['entry'] = round(df['entry'], 2)
    df['exit'] = round(df['exit'], 2)
    df['exposure'] = df['entry'] * df['quantity']
    df['percent'] = round((df['entry']-df['exit'])/df['entry']*100, 2)##.astype(str) + '%'
    df['closedDateOnly'] = df['closeDate'].str.slice(0, 10)
    df = df.sort_values(by=['closeDate'])
    df['balance'] = df['profitAndLoss'].cumsum()
    df = df.reset_index(drop=True)
    
    
    df['openDate'] = pd.to_datetime(df['openDate'])
    df['closeDate'] = pd.to_datetime(df['closeDate'])
    
    df['day_of_week'] = df['closeDate'].dt.day_name()
    
    df['openEST'] = df['openDate'].dt.tz_convert('America/New_york')     
    df['closeEST'] = df['closeDate'].dt.tz_convert('America/New_york')  
    
    df['holdTime'] = df['closeEST']-df['openEST']
    df['openDate'] = df['openEST'].dt.date
    df['closeDate'] = df['closeEST'].dt.date
  
    
    df['openTime'] = df['openEST'].dt.time
    df['closeTime'] = df['closeEST'].dt.time

    
   # df['holdTime'] = (df['closeTime'] - df['openTime']).dt.time
    filtered = df[['openDate', 'closeDate', 'openTime', 'closeTime', 'holdTime','symbol', 'quantity', 'entry', 'exit', 'percent', 'profitAndLoss', 'balance', 'exposure', 'fee', 'day_of_week']]
          
     
     
     
    
    ######################################################################################
    # Main
    ####################################################################################
    
    on = st.toggle("Toggle To see specific day stats")

    if not on:
        #st.write("Feature activated!")
        subCol1, subCol2, = st.columns([2, 3])
        with subCol1:
            getMetrics(filtered, 'profitAndLoss', 'fee')
        with subCol2:
            #################################################################
            # grouped by day of the week
            ##################################################################
            groupedByDay = filtered.groupby('day_of_week')
            #st.dataframe(groupedByDay)
            tempData = []
            for key, item in groupedByDay:
                #groupedByDate.get_group(key)
                
                ###################################################################
                # Trade Metrics 
                ###################################################################
                numOfWinners = item[item['profitAndLoss'] > 0].count()[0]
                numOfLosers = item[item['profitAndLoss'] < 0].shape[0]
                totalTrades = numOfWinners + numOfLosers
                
                netProfitOrLoss = item['profitAndLoss'].sum().round()
                averageWin = (item[item['profitAndLoss'] > 0]['profitAndLoss'].sum()/numOfWinners).round()
                averageLoss = (item[item['profitAndLoss'] < 0]['profitAndLoss'].sum()/numOfLosers).round()
                commissions = item['fee'].sum().round()
                
                winRate = "{:.1%}".format(numOfWinners/totalTrades)
                pnlRatio = round((averageWin/averageLoss * -1), 2) 
                
                winPct = numOfWinners/totalTrades 
                LossPct = numOfLosers/totalTrades 
                expectancy = winPct * averageWin - LossPct * (averageLoss * -1)
                
                if not math.isnan(expectancy):
                    expectancy =  math.floor(expectancy)
                
                data = {
                    'Day': key, 
                    '# of Trades': totalTrades, 
                    'Net PnL': netProfitOrLoss, 
                    'Win Rate': winRate,
                    'PnL ratio': pnlRatio,
                    'Expectancy': expectancy,
                    'Commissions': commissions
                    }
                #temp = pd.DataFrame(data)
                tempData.append(data)
            dayMetricDf = pd.DataFrame(tempData)
            dayMetricDf = dayMetricDf.sort_values(by=['Net PnL'])
        
            
            sorted_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            dayMetricDf['Day'] = pd.Categorical(dayMetricDf['Day'], sorted_weekdays)
            dayMetricDf = dayMetricDf.sort_values("Day")
            st.dataframe(dayMetricDf, hide_index=True)
            ##################################################################
        st.header("Equity curve")
        st.line_chart(filtered['balance'])

        
            
                    
            
            
        ###################################################################
        
        
        
        #st.bar_chart(filtered['profitAndLoss'])s
 
        
        ######################################################################
        st.header("Daily PnL")
        dailyProfit = filtered.groupby('closeDate')['profitAndLoss'].sum()
        dailyProfit = dailyProfit.reset_index()
        barChart(dailyProfit, 'closeDate', 'profitAndLoss')

        symbolSum = filtered.groupby('symbol')['profitAndLoss'].sum()
        symbolSum = symbolSum.reset_index()

        
        positive_symbolSum = symbolSum[symbolSum['profitAndLoss'] > 0]
        positive_symbolSum = positive_symbolSum.sort_values(by=['profitAndLoss'], ascending=True)
        
        negative_symbolSum = symbolSum[symbolSum['profitAndLoss'] < 0]
        negative_symbolSum = negative_symbolSum.sort_values(by=['profitAndLoss'], ascending=False)
        
        subCol1, subCol2, = st.columns(2)
        with subCol1: 
            barChart(negative_symbolSum, 'profitAndLoss', 'symbol')
        with subCol2:
            barChart(positive_symbolSum, 'profitAndLoss', 'symbol')
        symbols = symbolSum.symbol.unique()
        #print(symbols.sort())
        option = st.selectbox('Select a symbol', symbols)
        filteredSymbol = filtered[filtered['symbol'] == option]
        
        st.dataframe(filteredSymbol, hide_index=True)
        filtered['indexNum'] = filtered.index
        
        with st.expander('Show Trades'):
                st.dataframe(filtered,  hide_index=True)
                
        st.header("P/L") 
        barChart(filtered, 'indexNum', 'profitAndLoss')

        st.header("Exposure")
        barChart(filtered, 'indexNum', 'exposure')
        
        #barChart(filtered, 'indexNum', 'quantity')
        
        
        #df_scatter = filtered.sort_values(by=['closeTime'])
       
        
        
        
        df_scatter = filtered
        df_scatter['positive'] = np.where(df_scatter['profitAndLoss'] >=0, True, False)
        

        fig_scatter = px.scatter(df_scatter, x='closeTime', y='profitAndLoss', color='positive', color_discrete_map={True: 'green', False:'red'})
        
        fig_scatter.update_xaxes(categoryorder='category ascending')
        st.plotly_chart(fig_scatter)

    

  
    else:
    ##############################################################################################
        subCol1, subCol2 = st.columns(2)
        with subCol1:
            lastTradedDay = filtered.iloc[-1]['closeDate']
            tradedDays = filtered.closeDate.unique()
            option = st.selectbox('Select a date', tradedDays, index=tradedDays.size-1)
            #st.header(option) 

            
            #print(lastTradedDay)
            lastDay = filtered[filtered['closeDate'] == option]
            lastDay['cumulative'] = lastDay['profitAndLoss'].cumsum()
    
            lastDay = lastDay.reset_index(drop=True)
            # st.dataframe(lastDay.iloc[:,3:],  hide_index=True)

            lastDayBalance = pd.concat([pd.Series([0]), lastDay['cumulative']]).reset_index(drop=True)
            barChart(lastDay, 'closeTime', 'profitAndLoss')
            
            
            #st.scatter_chart(lastDay.query('profitAndLoss < 0')['percent'])
            #st.dataframe(lastDayBalance)
            #st.bar_chart(lastDay['profitAndLoss'])
            #st.bar_chart(lastDay['exposure'])
            
            #st.bar_chart(
            #    lastDay, y=['exposure','profitAndLoss'], color=["#a1c4a6", "#FF0000"]  # Optional
            #)
        with subCol2: 
            getMetrics(lastDay, 'profitAndLoss', 'fee')
            st.line_chart(lastDayBalance)
        
        with st.expander('Show Trades'):
                st.dataframe(lastDay,  hide_index=True)
        
        lastDay = lastDay.sort_values(by=['closeTime'])
        
        subCol1, subCol2 = st.columns(2)
        with subCol1:
            barChart(lastDay, 'symbol', 'profitAndLoss')
        with subCol2:
            lastDaySymbolGroupby = lastDay.groupby('symbol')['profitAndLoss'].sum()
            lastDaySymbolGroupby = lastDaySymbolGroupby.reset_index()
            barChart(lastDaySymbolGroupby, 'symbol', 'profitAndLoss')
        #st.header("Percent")
        #st.bar_chart(lastDay['percent'])
        

    
except KeyError:
    print("keyError") 
 
