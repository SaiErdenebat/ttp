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

    
    #print(filtered.to_string())
    #filtered['profitAndLoss'].plot(kind='bar')
    
    #filtered['balance'].plot.line()
    #st.bar_chart(filtered['profitAndLoss'])
    st.line_chart(filtered['balance'])

   # grouped = filtered.groupby('closedDateOnly').sum().reset_index()
    #print(grouped[['closedDateOnly', 'profitAndLoss']])
    #grouped[['closedDateOnly', 'profitAndLoss']].plot(kind='bar')
   # st.bar_chart(grouped[['profitAndLoss']])
    st.bar_chart(filtered['profitAndLoss'])
    #print(filtered)
    st.bar_chart(
        filtered, x='closeDate', y=['profitAndLoss','cost'], color=["#FF0000", "#0000FF"]  # Optional
    )
    #st.bar_chart(filtered['percent'])
    #st.write(filtered)
    st.dataframe(filtered, hide_index=True)
    st.dataframe(filtered.groupby('closedDateOnly')['profitAndLoss'].sum(), hide_index=True)
except KeyError:
    print("keyError") 
