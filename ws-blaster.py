import streamlit as st
import pandas as pd
import random
import re
import time
import os
from datetime import datetime
from urllib.parse import quote 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import pyperclip
from pathlib import Path
import shutil
from os import listdir
from os.path import isfile, join

# Hide streamlit header and footer
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

def save_uploadedfile(uploadedfile, file_name, path):
    '''
    Save uploaded file to path directory

    uploadedfile: Uploaded file
    file_name: File name of the uploaded file
    path: Path directory on where to save the file
    '''
    with open(os.path.join(path,file_name),"wb") as f:
        f.write(uploadedfile.getbuffer())

def clean_numbers(df, col):
    '''
    Clean numbers to required format for whatsapp search

    df: Dataframe [pandas dataframe]
    col: Column name containing the numbers to blast [str]
    
    returns dataframe with cleaned numbers
    '''
    df[col] = df[col].astype(str)
    df[col] = [re.sub("[^0-9]", "", x) for x in df[col]]
    df = df[df[col] != '']
    df[col] = ['60' + x if (x[0] == '1' and 8 < len(x) < 11) else x for x in df[col]]
    df[col] = ['6' + x if (x[0] == '0' and 9 < len(x) < 12) else x for x in df[col]]
    df[col] = ['' if (x[2] != '1' or len(x) > 12 or len(x) < 11) else x for x in df[col]]
    df = df[df[col] != '']
    df = df.drop_duplicates(subset = col)
    df = list(df[col])
    return df

def open_driver(user_path, headless = True):
    '''
    Opens chromedriver and initialize Whatsapp web

    user_path: Path where user credentials are located
    headless: Decides whether to run on headless mode or otherwise

    Returns a chromedriver instance
    '''
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(user_path)
    chrome_options.add_argument("--disable-notifications")
    if headless:
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--headless")
        # Specify user-agent to allow headless mode
        chrome_options.add_argument("user-agent=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    driver = webdriver.Chrome('/Users/amerwafiy/Downloads/chromedriver',chrome_options=chrome_options)
    driver.get('https://web.whatsapp.com/')
    driver.execute_script("window.onbeforeunload = function() {};")
    return driver


image = Image.open('/Users/amerwafiy/Desktop/Projects/scraper-webapp/invoke_logo.jpg')
st.sidebar.title('Whatsapp Blaster')
st.sidebar.image(image)
option1 = st.sidebar.selectbox('Select option', ('Blast Messages', 'Account Management'))

if option1 == 'Blast Messages':
    st.image('/Users/amerwafiy/Desktop/ws-blasting/ws-logo.png')

    option2 = st.selectbox('How do you to want define your contacts to blast?', ('Upload contact file (csv/xlsx)', 'Manual input',))
    
    if option2 == 'Upload contact file (csv/xlsx)':
        contacts = st.file_uploader("")
        if contacts:
            if contacts.name[-3:] == 'csv':
                contacts = pd.read_csv(contacts, na_filter = False)
            else:
                contacts = pd.read_excel(contacts, na_filter = False)
            col = st.selectbox('Select phone number column', [''] + list(contacts.columns))
            if col != '':
                contacts = clean_numbers(contacts, col)

    else:
        contacts = st.text_area("Key in phone number(s) to blast (Separate multiple phone numbers with a ',' e.g. 601111111111,601222222222)")
        contacts = contacts.split(',')
        contacts = [x.strip() for x in contacts]
        contacts = pd.DataFrame({'phone':contacts})
        contacts = clean_numbers(contacts, 'phone')
        if len(contacts) == 0 :
            st.write('Please make sure your numbers are in the right format')


    if type(contacts) == list and len(contacts) > 0:
        st.subheader('Number of contact(s) to blast: ' + str(len(contacts)))
        option3 = st.selectbox('Number of files/pictures to send', ('0', '1', '2', '3', '4'))
        if option3 != '0':
            path = ".../Desktop/ws-blasting/" #Define path where the files are stored
            save_path = Path(path)
            imgs = []
            for i in range(int(option3)):
                img = st.file_uploader("Upload an image", key = i)
                if img:
                    st.write(img.name)
                    imgs.append(path + img.name)
                    save_uploadedfile(img, img.name, save_path)

        option4 = st.selectbox('How many variations of the same message do you have?', ('', '1', '2', '3', '4', '5'))
        if option4 != '':
            s = []
            for i in range(int(option4)):
                m = st.text_area("Enter message:", key = i)
                s.append(m)
            option5 = st.selectbox('Choose set of accounts to blast from', ('', 'meniaga','AyuhMalaysia', 'Burner Accounts'))
            if option5 != '':
                if option5 == 'Burner Accounts':
                    option5 = 'burner'
                mypath = '.../Desktop/ws-blasting/Users/amerwafiy/Library/Application Support/Google/Chrome/' + option5 + '/'
                driver_ls = [f for f in listdir(mypath)]
                if ".DS_Store" in driver_ls:
                    driver_ls.remove(".DS_Store")
                st.write('Blasting from: ' + ', '.join(driver_ls))
                option6 = st.button('Start Blasting')
                if option6:
                    with st.spinner('Blasting Messages...'):
                        driver_dict = {}
                        user_path ='user-data-dir=Users/amerwafiy/Library/Application Support/Google/Chrome/' + option5 +'/'
                        for acc in driver_ls:
                            driver = open_driver(user_path + acc)
                            driver_dict[acc] = driver
                            time.sleep(10)
                        drivers = list(driver_dict.values())
                        count = 0
                        unsuccessful = []

                        driver_count = len(drivers)
                        drivers_idx = 0
                        i = 0
                        start = datetime.now()
                        while i < len(contacts):
                            num = contacts[i]
                            driver = drivers[drivers_idx]
                            url = 'https://web.whatsapp.com/send?phone=' + str(num)
                            try:
                                # Open new chat
                                driver.get(url)
                                driver.execute_script("window.onbeforeunload = function() {};")
                                time.sleep(5)
                                # Send pictures
                                f = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH,'//*[@data-testid="clip"]'))).click()
                                if option3 != '0':
                                    for p in range(int(option3)):
                                        f = driver.find_element_by_css_selector("input[type='file']").send_keys(imgs[p])
                                        f = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH,'//*[@class="_165_h _2HL9j"]'))).click()
                                # Click type box and send input
                                f = WebDriverWait(driver, 6).until(EC.visibility_of_element_located((By.XPATH,'//*[@class="p3_M1"]')))
                                time.sleep(1)
                                key = random.randint(0,int(option4) - 1)
                                if len(s[key]) == 0:
                                    count += 1
                                else:
                                    #Copy clipboard and paste it to the chat to prevent any missing characters
                                    pyperclip.copy(s[key])
                                    ActionChains(driver).key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
                                time.sleep(1)
                                try:
                                    # Send message
                                    f = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH,'//*[@data-testid="send"]')))
                                    f.click()
                                except:
                                    # Handles error and send message
                                    f = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH,'//*[@class="_20C5O _2Zdgs"]')))
                                    f.click()
                                    f = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH,'//*[@data-testid="send"]')))
                                    f.click()
                                count += 1
                            except:
                                # Close driver that became unavailable when blasting is ongoing
                                elems = driver.find_elements(by=By.PARTIAL_LINK_TEXT, value='Need help to get started?')
                                if len(elems) > 0 and elems[0].is_displayed():
                                    drivers[drivers_idx].quit()
                                    st.subheader('*** Driver-- ' + str(driver_ls[drivers_idx]) + ' is unavailable ***')
                                    del driver_ls[drivers_idx]
                                    del drivers[drivers_idx]
                                    driver_count = len(drivers)
                                    if driver_count == 0:
                                        st.subheader('### ALL ACCOUNTS ARE CURRENTLY UNAVAILABLE! BLASTING STOPPED AT INDEX: ' + str(i) + '###')
                                        break
                                    else:
                                        i -= 1
                                        st.subheader('*** Drivers left: ' + str(driver_count) + ' ***')
                                else:
                                    unsuccessful.append(num)
                            # Loop through all the available drivers
                            drivers_idx = (drivers_idx + 1) % driver_count

                            # Apply some random wait time to lower the risk of accounts gettig banned
                            if i % 300 == 0 and i != 0:
                                time.sleep(random.randint(500,1000))
                            elif i % 10 == 0 and i!= 0:
                                time.sleep(random.randint(5,10))
                                st.write('Numbers gone through: ' + str(i) + ', Messages sent: ' + str(count) + ', Time elapsed: ' + str(datetime.now() - start)[:7])
                            else:
                                time.sleep(random.randint(2,5))
                            i += 1
                        if count > 0 :
                            st.balloons()
                        
                        st.subheader('Message sent: ' + str(count))
                        st.subheader('Time taken: ' + str(datetime.now() - start))
                        
                        # Remove save files from the directory after blasting is done
                        for p in range(int(option3)):
                            os.remove(imgs[p])

if option1 == 'Account Management':
    st.image('/Users/amerwafiy/Desktop/ws-blasting/ws-logo.png')
    option2 = st.selectbox('Select option', ('Add new account(s)','Check available account(s)', 'Delete unavailable account(s)'))
    
    if option2 == 'Check available account(s)':
        option3 = st.selectbox('Select set of accounts to check', ('', 'meniaga','AyuhMalaysia','Burner Accounts'))
        if option3 != '':
            if option3 == 'Burner Accounts':
                option3 = 'burner'
            mypath = '/Users/amerwafiy/Desktop/ws-blasting/Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
            accs = [f for f in listdir(mypath)]
            if ".DS_Store" in accs:
                accs.remove(".DS_Store")
            mypath = 'user-data-dir=Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
            available = []
            not_available = []
            with st.spinner('Checking Accounts...'):
                for acc in accs:
                    driver = open_driver(mypath + acc)
                    try:
                        elems = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT,'Need help to get started?')))
                        not_available.append(acc)
                    except:
                        available.append(acc)
                    driver.quit()
            
            if len(available) == 0:
                st.subheader('All accounts are not available!')
                st.subheader('Unavailable accounts: ', ', '.join(not_available))
            elif len(not_available) == 0:
                st.subheader('All accounts are available!')
                st.subheader('Available accounts: ' + str(', '.join(available)))
            else:
                st.subheader('Available account(s): ' + str(', '.join(available)))
                st.subheader('Unavailable account(s): ' + str(', '.join(not_available)))

    elif option2 == 'Add new account(s)':
        option3 = st.selectbox('Where do you want to add the account(s)?', ('meniaga','AyuhMalaysia','Burner Accounts'))
        if option3 == 'Burner Accounts':
            option3 = 'burner'
        mypath = '/Users/amerwafiy/Desktop/ws-blasting/Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
        accs = [f for f in listdir(mypath)]
        if ".DS_Store" in accs:
            accs.remove(".DS_Store")
        name = st.text_area("Enter Whatsapp account name:")
        name = name.split(',')
        name = [x.strip() for x in name]
        taken = [x for x in name if x in accs]
        if len(taken) == 0:
            option4 = st.button('Add Account(s)')
            if option4:
                mypath = 'user-data-dir=Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
                for n in name:
                    driver = open_driver(mypath + n, headless = False)
                    try:
                        f = WebDriverWait(driver, 300).until(EC.visibility_of_element_located((By.XPATH,'//*[@title="Search input textbox"]')))
                        st.subheader(n + ' added!')
                        time.sleep(1)
                        driver.quit()
                    except:
                        driver.quit()
                        st.subheader('Unable to link account(' + n + '). Please try again!')
                        mypath = '/Users/amerwafiy/Desktop/ws-blasting/Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
                        path_delete = mypath + n
                        shutil.rmtree(path_delete)
        
        elif len(taken) == 1:
            st.write('Account name--' + str(taken[0]) + ' is not available. Please choose another name!')
        
        else:
            st.write(str(', '.join(taken)) + ' are not available. Please choose another name!')
    
    elif option2 == 'Delete unavailable account(s)':
        option3 = st.selectbox('From which set of account(s) do you want to delete?', ('', 'meniaga','AyuhMalaysia','Burner Accounts'))
        if option3 != '':
            if option3 == 'Burner Accounts':
                option3 = 'burner'
            mypath = '/Users/amerwafiy/Desktop/ws-blasting/Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
            accs = [f for f in listdir(mypath)]
            if ".DS_Store" in accs:
                accs.remove(".DS_Store")
            st.subheader('Accounts: ' + ', '.join(accs))
            mypath = 'user-data-dir=Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
            available = []
            not_available = []
            with st.spinner('Deleting Accounts...'):
                for acc in accs:
                    driver = open_driver(mypath + acc)
                    try:
                        elems = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT,'Need help to get started?')))
                        not_available.append(acc)
                    except:
                        available.append(acc)
                    driver.quit()
            
                if len(not_available) == 0:
                    st.subheader('No account(s) to delete!')
                else:
                    st.subheader('Unavailable account(s): ' + str(', '.join(not_available)))
                    mypath = '/Users/amerwafiy/Desktop/ws-blasting/Users/amerwafiy/Library/Application Support/Google/Chrome/' + option3 + '/'
                    for n in not_available:
                        path_delete = mypath + n
                        shutil.rmtree(path_delete)
                    st.subheader('Succesfully deleted unavailable account(s)!')
            
