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
#accountNumber = st.selectbox("Choose an account number:", ("F13011327", ""))


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
    
    filtered = df[['createdAt', 'closeDate','closedDateOnly', 'symbol', 'quantity', 'entry', 'exit', 'percent', 'profitAndLoss', 'cost', 'balance']]

    
    #print(filtered.to_string())
<<<<<<< HEAD
=======
    #filtered['profitAndLoss'].plot(kind='bar')
    
    #filtered['balance'].plot.line()
    #st.bar_chart(filtered['profitAndLoss'])
    #st.line_chart(filtered['balance'])
>>>>>>> 7d02a7b6f1ca0143bc8ce6c25c9237ed5fa86e8f

    st.line_chart(filtered['balance'])

    grouped = filtered.groupby('closedDateOnly').sum().reset_index()
    st.bar_chart(filtered['profitAndLoss'])
    #print(filtered)
    st.bar_chart(
        filtered, x='closeDate', y=['profitAndLoss','cost'], color=["#FF0000", "#0000FF"]  # Optional
    )
    st.bar_chart(filtered['percent'])
    st.bar_chart(grouped, x='closedDateOnly', y=['profitAndLoss'])
    #print(filtered.groupby('closedDateOnly')['symbol'].nunique())


    grouped_df = filtered.groupby('closedDateOnly')
    st.scatter_chart(filtered['profitAndLoss'])
    for key, item in grouped_df:
        temp = grouped_df.get_group(key)
        print(temp.to_string(index=False))
        temp_symbol = temp['symbol']
        print(temp_symbol.nunique(), temp_symbol.unique())
        print(round(temp['profitAndLoss'].sum(), 2))

        st.dataframe(temp.iloc[:, 2:], column_config={"percent": st.column_config.NumberColumn(format="%d %%")}, hide_index=True)
        st.text(temp_symbol.nunique())
        st.text(temp_symbol.unique())
        st.text(round(temp['profitAndLoss'].sum(), 2))
        st.bar_chart(temp, x='symbol', y=['profitAndLoss'])
    
    st.dataframe(grouped['profitAndLoss'])
    
except KeyError:
    print("keyError") 
