import plotly.io as pio

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px




st.set_page_config(
    page_title="Main",
    page_icon="👋",
    layout="wide",
)
################################################

payload = {
    'username': "",
    'password': ""
}
##
## custom username and password text inputs and account number
##
#payload['username'] = st.text_input("Enter an email", type="default")
#payload['password']= st.text_input("Enter a password", type="password")


accountNumber = st.selectbox("Choose an account number:", (
    "FEBP13020502",
    "12014517",
    "12016374",
    "F12016374",
    "12020109",
    "F12020109",
    #"12025061",
    #"13000402",
    "13000809",
    "E13002593",
    "F13002878",
    #"E13005910",
    #"E13006961",
    #"E13009393",
    "E13009422",
    "E13010054",
    "F13011327",
    "EEBP13017137",
    "EEBP13017274",
    ))

payload['username'] = st.secrets.db_username
payload['password'] = st.secrets.db_password

loginUrl=('https://api.tradethepool.com/user/login') 
tradesUrl = ("https://api.tradethepool.com/position/closed/" + str(accountNumber))

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
        st.metric('Expectancy', round(expectancy))

try:
    s = requests.Session()
    p = s.post(loginUrl, data=payload)
    token = p.json()['data']['token']


    r = s.get(tradesUrl, headers={'Authorization': "Bearer {}".format(token)})
    
    df = pd.json_normalize(r.json()['data']['results'])

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
    filtered = df[['openTime', 'closeTime', 'holdTime','symbol', 'quantity', 'entry', 'exit', 'percent', 'profitAndLoss', 'balance', 'exposure', 'openDate', 'closeDate', 'fee', 'day_of_week']]
     
     
     
     
    
    ######################################################################################
    # Main
    ####################################################################################
    on = st.toggle("Main dashboard")

    if on:
        #st.write("Feature activated!")
        subCol1, subCol2, = st.columns([2, 3])
        with subCol1:
            getMetrics(filtered, 'profitAndLoss', 'fee')
            st.write(filtered['profitAndLoss'].sum()/16000*100)
        with subCol2:
            ##################################################################
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
                
                data = {
                    'Day': key, 
                    '# of Trades': totalTrades, 
                    'Net PnL': netProfitOrLoss, 
                    'Win Rate': winRate,
                    'PnL ratio': pnlRatio,
                    'Expectancy': round(expectancy),
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
        
        
            
                    
            
            
        ###################################################################
        
        
        
        #st.bar_chart(filtered['profitAndLoss'])s
        st.header("Daily PnL")
        dailyProfit = filtered.groupby('closeDate')['profitAndLoss'].sum()
        dailyProfit = dailyProfit.reset_index()
        barChart(dailyProfit, 'closeDate', 'profitAndLoss')


        ######################################################################

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
        
        st.dataframe(filteredSymbol)
        filtered['indexNum'] = filtered.index 
        barChart(filtered, 'indexNum', 'profitAndLoss')

        
        #df_scatter = filtered.sort_values(by=['closeTime'])
        df_scatter = filtered
        df_scatter['positive'] = np.where(df_scatter['profitAndLoss'] >=0, True, False)
        

        fig_scatter = px.scatter(df_scatter, x='closeTime', y='profitAndLoss', color='positive', color_discrete_map={True: 'green', False:'red'})
        
        fig_scatter.update_xaxes(categoryorder='category ascending')
        st.plotly_chart(fig_scatter)
        
        st.header("Equity Curve")
        st.area_chart(filtered['balance'])
    

        #print(dailyProfit, dailyProfit.cumsum())
        #st.dataframe(dailyProfit, hide_index=True)
        #dailyProfit_sorted = dailyProfit.sort_values(by=['profitAndLoss'])
        #dailyProfit_sorted = dailyProfit_sorted.reset_index(drop=True)
        
        
        
        #dailyProfit['color'] = np.where(dailyProfit['profitAndLoss'] >=0, 'green', 'red')
        
        #st.plotly_chart(px.bar(dailyProfit, x=dailyProfit.index, y='profitAndLoss', text_auto=True, color='color'))

        
        #st.plotly_chart(px.bar(dailyProfit_sorted, x=dailyProfit_sorted.index, y='profitAndLoss'))
        #st.bar_chart(dailyProfit)
        #st.bar_chart(dailyProfit_sorted)
        #st.line_chart(dailyProfit)
        
        #print(filtered.to_string())
        #filtered['profitAndLoss'].plot(kind='bar')
        
        #filtered['balance'].plot.line()
        #st.bar_chart(filtered['profitAndLoss'])
        
        #st.area_chart(filtered['balance'], color=["#075d85"]) 

        #st.scatter_chart(filtered.query('profitAndLoss > 0')['exposure'],color=["#17910c"])
        #st.scatter_chart(filtered.query('profitAndLoss < 0')['exposure'], color=["#FF0000"])
        #st.dataframe(filtered.sort_values(by=['profitAndLoss']), hide_index=True)
        
        #grouped = filtered.groupby('closedDateOnly').sum().reset_index()
        #print(grouped[['closedDateOnly', 'profitAndLoss']])
        #grouped[['closedDateOnly', 'profitAndLoss']].plot(kind='bar')
        #st.bar_chart(grouped[['profitAndLoss']])
        
        
        #sortedByPnL = filtered.sort_values(by=['profitAndLoss'])
        #sortedByPnL = sortedByPnL.reset_index(drop=True)
        #st.dataframe(sortedByPnL.iloc[:,2:])
        #print(sortedByPnL['symbol'].tolist())
        #st.bar_chart(sortedByPnL['profitAndLoss'])
        
        #print(filtered)
        #st.bar_chart(
        #    filtered, x='closeDate', y=['profitAndLoss','exposure'], color=["#FF0000", "#0000FF"]  # Optional
        #)
        #st.bar_chart(filtered['percent'])
        #st.write(filtered)
        #st.dataframe(filtered, hide_index=True)

    
        
  
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
            st.area_chart(lastDayBalance)
        
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
 
