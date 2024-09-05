import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

payload = {
    'username': "",
    'password': ""
}
##
## custom username and password text inputs and account number
##
#payload['username'] = st.text_input("Enter an email", type="default")
#payload['password']= st.text_input("Enter a password", type="password")


accountNumber = st.sidebar.selectbox("Choose an account number:", (
    "EEBP13017274",
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
    "EEBP13017137"
    ))

payload['username'] = st.secrets.db_username
payload['password'] = st.secrets.db_password

loginUrl=('https://api.tradethepool.com/user/login') 
tradesUrl = ("https://api.tradethepool.com/position/closed/" + str(accountNumber))


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

    #print(df['id'])
    df['entry'] = round(df['entry'], 2)
    df['exit'] = round(df['exit'], 2)
    df['exposure'] = df['entry'] * df['quantity']
    df['percent'] = round((df['entry']-df['exit'])/df['entry']*100, 2)##.astype(str) + '%'
    df['closedDateOnly'] = df['closeDate'].str.slice(0, 10)
    #df = df.sort_values(by=['closedDateOnly'])
    df = df.sort_values(by=['closeDate'])
    df['balance'] = df['profitAndLoss'].cumsum()
    df = df.reset_index(drop=True)
    
    
    df['openDate'] = pd.to_datetime(df['openDate'])
    df['closeDate'] = pd.to_datetime(df['closeDate'])

    # Convert UTC to EST (Eastern Standard Time)
    #df['openDate'] = df['openDate'].dt.tz_localize('UTC')
    #df['closeDate'] = df['closeDate'].dt.tz_localize('UTC')
    
    df['openEST'] = df['openDate'].dt.tz_convert('America/New_york')     
    df['closeEST'] = df['closeDate'].dt.tz_convert('America/New_york')  
  
    df['openDate'] = df['openEST'].dt.date
    df['closeDate'] = df['closeEST'].dt.date
  
    
    df['openTime'] = df['openEST'].dt.time
    df['closeTime'] = df['closeEST'].dt.time
   
   # df['holdTime'] = (df['closeTime'] - df['openTime']).dt.time
    filtered = df[['openTime', 'closeTime', 'symbol', 'quantity', 'entry', 'exit', 'percent', 'profitAndLoss', 'balance', 'exposure', 'openDate', 'closeDate']]
     
    filtered['color'] = np.where(filtered['profitAndLoss'] >=0, 'green', 'red')
    fig = px.bar(filtered, x=df.index, y='profitAndLoss', color='color')
    ### converting to EST
    #df['utc_time'] = pd.to_datetime(df['utc_time'])

    # Convert UTC to EST (Eastern Standard Time)
    #df['est_time'] = df['utc_time'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')     
    ##
    
    
    col1, col2 = st.columns(2)
    with col1: 
    
        st.header("Equity Curve")
        st.line_chart(filtered['balance'])
        #st.bar_chart(filtered['profitAndLoss'])
        st.plotly_chart(fig)
        with st.expander('Data Preview'):
            st.dataframe(filtered, hide_index=True)
        st.write(filtered[filtered['profitAndLoss'] > 0].count()[0])
        st.write(filtered[filtered['profitAndLoss'] < 0].shape[0])
           ###################################################################
        dailyProfit = filtered.groupby('closeDate')['profitAndLoss'].sum()
        #print(dailyProfit, dailyProfit.cumsum())
        #st.dataframe(dailyProfit, hide_index=True)
        dailyProfit_sorted = dailyProfit.sort_values(ascending=False)
        dailyProfit_sorted = dailyProfit_sorted.reset_index(drop=True)
        st.header("Daily PnL")
        st.bar_chart(dailyProfit)
        st.bar_chart(dailyProfit_sorted)
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
        
        
        sortedByPnL = filtered.sort_values(by=['profitAndLoss'])
        sortedByPnL = sortedByPnL.reset_index(drop=True)
        #st.dataframe(sortedByPnL.iloc[:,2:])
        #print(sortedByPnL['symbol'].tolist())
        st.bar_chart(sortedByPnL['profitAndLoss'])
        
        #print(filtered)
        #st.bar_chart(
        #    filtered, x='closeDate', y=['profitAndLoss','exposure'], color=["#FF0000", "#0000FF"]  # Optional
        #)
        #st.bar_chart(filtered['percent'])
        #st.write(filtered)
        #st.dataframe(filtered, hide_index=True)

     
        
    
    with col2:
        ##############################################################################################
        st.header("Choose a specific day:") 
        lastTradedDay = filtered.iloc[-1]['closeDate']
        tradedDays = filtered.closeDate.unique()
        option = st.selectbox('Select a date', tradedDays, index=tradedDays.size-1)
        #st.header(option) 

        
        #print(lastTradedDay)
        lastDay = filtered[filtered['closeDate'] == option]
        lastDay['cumulative'] = lastDay['profitAndLoss'].cumsum()
        lastDay = lastDay.reset_index(drop=True)
        # st.dataframe(lastDay.iloc[:,3:],  hide_index=True)
        with st.expander('Trades'):
            st.dataframe(lastDay,  hide_index=True)
        lastDayBalance = pd.concat([pd.Series([0]), lastDay['cumulative']]).reset_index(drop=True)
        st.line_chart(lastDayBalance)
        
        #st.scatter_chart(lastDay.query('profitAndLoss < 0')['percent'])
        #st.dataframe(lastDayBalance)
        #st.bar_chart(lastDay['profitAndLoss'])
        #st.bar_chart(lastDay['exposure'])
        
        #st.bar_chart(
        #    lastDay, y=['exposure','profitAndLoss'], color=["#a1c4a6", "#FF0000"]  # Optional
        #)
        st.header("Profit and Loss")
        st.bar_chart(lastDay['profitAndLoss'])
        st.header("Percent")
        st.bar_chart(lastDay['percent'])
            
        

            
    
except KeyError:
    print("keyError") 
 
