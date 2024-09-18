import streamlit as st


st.set_page_config(page_title="Day Demo", page_icon="🌍")

st.markdown("# Day Demo")

subCol1, subCol2, subCol3 = st.columns([1 , 2, 3])
with subCol1:

    title = st.text_input("Ticker Symbol", "ticker")
with subCol2:
    number = st.number_input("Entry")
with subCol3:
    st.write("Risk ", number)