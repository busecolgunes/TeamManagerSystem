# Import necessary libraries
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
import yagmail
import datetime

# Load data (marketers and customers) from CSV files
marketers_df = pd.read_csv('marketers.csv')
customers_df = pd.read_csv('customers.csv')

# Define credentials for authentication
credentials = {
    "usernames": {
        row['Email']: {
            "name": row['Name'],
            "password": row['Password'],
            "role": row['Role']
        }
        for index, row in marketers_df.iterrows()
    }
}

# Authentication setup
authenticator = stauth.Authenticate(credentials, "team_app", "random_key", cookie_expiry_days=30)
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.write(f"Welcome {name}!")
    
    # Admin Dashboard
    if credentials["usernames"][username]["role"] == "Admin":
        st.sidebar.success("You are an admin.")
        
        st.title("Admin Dashboard")
        st.subheader("Marketers Performance Overview")
        st.write(customers_df)  # Show all customers data
        
        if st.checkbox('Edit Marketers'):
            st.write(marketers_df)
        
        if st.checkbox('Edit Customers'):
            st.write(customers_df)
            
    # Marketer Dashboard
    else:
        st.sidebar.success("You are a marketer.")
        
        st.title("Marketer Dashboard")
        
        # Filter data for the current marketer
        marketer_customers = customers_df[customers_df['Marketer ID'] == username]
        st.subheader("Your Customers")
        st.write(marketer_customers)
        
        # Add new customer
        if st.checkbox('Add New Customer'):
            with st.form(key="customer_form"):
                customer_name = st.text_input('Customer Name')
                brand_name = st.text_input('Brand Name')
                rate_meeting = st.slider('Rate Meeting', 1, 10)
                next_meeting = st.date_input('Next Meeting Date')
                sold_product = st.radio('Did you sell a product?', ('Yes', 'No'))
                if sold_product == 'Yes':
                    amount_sold = st.number_input('Amount Sold', min_value=0.0)
                    product_name = st.text_input('Product Name')
                else:
                    amount_sold = 0
                    product_name = None
                
                submitted = st.form_submit_button('Add Customer')
                if submitted:
                    new_customer = {
                        "Customer ID": len(customers_df) + 1,
                        "Marketer ID": username,
                        "Customer Name": customer_name,
                        "Brand Name": brand_name,
                        "Meeting Rate": rate_meeting,
                        "Next Meeting": next_meeting,
                        "Sold Product": sold_product,
                        "Amount Sold": amount_sold,
                        "Product Name": product_name
                    }
                    customers_df = customers_df.append(new_customer, ignore_index=True)
                    customers_df.to_csv('customers.csv', index=False)
                    st.success("Customer added successfully!")
                    
        # Performance chart for marketers
        performance_df = customers_df.groupby('Marketer ID').agg({
            'Meeting Rate': 'mean',
            'Amount Sold': 'sum',
            'Customer ID': 'count'
        }).reset_index()
        
        performance_df.columns = ['Marketer ID', 'Average Meeting Rate', 'Total Amount Sold', 'Customer Count']
        
        fig = px.bar(performance_df, x='Marketer ID', y=['Average Meeting Rate', 'Total Amount Sold', 'Customer Count'],
                     title="Marketer Performance Comparison", barmode='group')
        st.plotly_chart(fig)
        
# Reminder email setup
def send_email_reminder(email, customer_name, next_meeting):
    yag = yagmail.SMTP('your_email@gmail.com', 'your_password')
    yag.send(
        to=email,
        subject="Meeting Reminder",
        contents=f"Reminder: You have a meeting with {customer_name} on {next_meeting}"
    )

# Send reminders for meetings scheduled for tomorrow
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
upcoming_meetings = customers_df[customers_df['Next Meeting'] == tomorrow]

for index, row in upcoming_meetings.iterrows():
    marketer_email = marketers_df[marketers_df['ID'] == row['Marketer ID']]['Email'].values[0]
    send_email_reminder(marketer_email, row['Customer Name'], row['Next Meeting'])

# Authentication logout
authenticator.logout("Logout", "sidebar")
