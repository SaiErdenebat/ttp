import streamlit as st
import requests
import pandas as pd

payload = {
    'username': "",
    'password': ""
}
##
## custom username and password text inputs and account number
##
#payload['username'] = st.text_input("Enter an email", type="default")
#payload['password']= st.text_input("Enter a password", type="password")
#accountNumber = st.selectbox("Choose an account number:", ("F", ""))


payload['username'] = st.secrets.db_username
payload['password'] = st.secrets.db_password

loginUrl=('https://api.tradethepool.com/user/login') 
tradesUrl = ("https://api.tradethepool.com/position/closed/" + str(st.secrets.account_number))


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
    df['cost'] = df['entry'] * df['quantity']
    df['percent'] = round((df['entry']-df['exit'])/df['entry']*100, 2)##.astype(str) + '%'
    df['closedDateOnly'] = df['closeDate'].str.slice(0, 10)
    #df = df.sort_values(by=['closedDateOnly'])
    df = df.sort_values(by=['closeDate'])
    df['balance'] = df['profitAndLoss'].cumsum()
    df = df.reset_index(drop=True)
    
    filtered = df[['createdAt', 'closeDate','closedDateOnly', 'symbol', 'quantity', 'entry', 'exit', 'percent', 'profitAndLoss', 'balance', 'cost']]


    st.header("Best Losers Win")
    lastTradedDay = filtered.iloc[-1]['closedDateOnly']
    tradedDays = filtered.closedDateOnly.unique()
    option = st.selectbox('Select a date', tradedDays, index=tradedDays.size-1)
    

    
    #print(lastTradedDay)
    lastDay = filtered[filtered['closedDateOnly'] == option]
    lastDay['cumulative'] = lastDay['profitAndLoss'].cumsum()
    lastDay = lastDay.reset_index(drop=True)
    st.dataframe(lastDay.iloc[:,3:],  hide_index=True)
    lastDayBalance = pd.concat([pd.Series([0]), lastDay['cumulative']]).reset_index(drop=True)
    st.line_chart(lastDayBalance)
    #st.dataframe(lastDayBalance)
    #st.bar_chart(lastDay['profitAndLoss'])
    #st.bar_chart(lastDay['cost'])
    
    st.bar_chart(
        lastDay, y=['cost','profitAndLoss'], color=["#a1c4a6", "#FF0000"]  # Optional
    )
    #st.bar_chart(lastDay['percent'])
    
    dailyProfit = filtered.groupby('closedDateOnly')['profitAndLoss'].sum()
    print(dailyProfit, dailyProfit.cumsum())
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
    st.header("Equity Curve")
    st.line_chart(filtered['balance'])
    st.dataframe(filtered, hide_index=True)
   # grouped = filtered.groupby('closedDateOnly').sum().reset_index()
    #print(grouped[['closedDateOnly', 'profitAndLoss']])
    #grouped[['closedDateOnly', 'profitAndLoss']].plot(kind='bar')
   # st.bar_chart(grouped[['profitAndLoss']])
    st.bar_chart(filtered['profitAndLoss'])
    
    
    sortedByPnL = filtered.sort_values(by=['profitAndLoss'])
    sortedByPnL = sortedByPnL.reset_index(drop=True)
    #st.dataframe(sortedByPnL.iloc[:,2:])
    #print(sortedByPnL['symbol'].tolist())
    st.bar_chart(sortedByPnL['profitAndLoss'])
    
    #print(filtered)
    st.bar_chart(
        filtered, x='closeDate', y=['profitAndLoss','cost'], color=["#FF0000", "#0000FF"]  # Optional
    )
    #st.bar_chart(filtered['percent'])
    #st.write(filtered)
    #st.dataframe(filtered, hide_index=True)

    
    
except KeyError:
    print("keyError") 
 