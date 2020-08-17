import os
import sys
import csv
import pymysql
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Not using this right now, but may come in handy
# from selenium.webdriver import ActionChains

# Retreive credentials
cwd = os.path.dirname(os.path.abspath(__file__))
keyfile = os.path.join(cwd, 'keys.txt')
parsed_keyfile = open(keyfile, 'r')
NANO_LOGIN = parsed_keyfile.readline().rstrip()
NANO_PASSWORD = parsed_keyfile.readline().rstrip()
DB_HOST = parsed_keyfile.readline().rstrip()
DB_USER = parsed_keyfile.readline().rstrip()
DB_PASS = parsed_keyfile.readline().rstrip()
DB_NAME = parsed_keyfile.readline().rstrip()
parsed_keyfile.close()

# Empty lists for error logs
not_bucketed = []
expired = []

# Temporary list of filenames for testing
filenames = ['Andreas Moe_Borderline_SEBGA1500014_REDTID458.mp3', 'Beck_Turn Away_US3841400054_REDTID948.mp3', 'Beirut_Gibraltar_GBAFL1500029_REDTID974.mp3', 'Ben Abraham_I Belong to You_AUIXE1400003_REDTID985.mp3']

class InactiveClient(Exception):
    pass

class EmptyOrigin(Exception):
    pass

try:
    db = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME, cursorclass=pymysql.cursors.Cursor)

except:
    sys.exit("ERROR: Could not connect to database")

try:
    arg = sys.argv[1]
    if arg.isdigit():
        origin_id = arg
    else:
        raise ValueError

    with db.cursor() as cursor:
        cursor.execute("CALL SeleniumOriginName("+ origin_id +")")
        origin_name = cursor.fetchone()[0]
        if origin_name:
            origin_csv_file_path = os.path.join(cwd, origin_name + "_Full Origin.csv")

    with db.cursor() as cursor:
        cursor.execute("CALL SeleniumClientName("+ origin_id +")")
        client_name = cursor.fetchone()[0]
        if client_name == "Inactive Client":
            raise InactiveClient

    with db.cursor() as cursor:
        cursor.execute("CALL SeleniumBucket("+ origin_id +")")
        rows = cursor.fetchall()
        
        if rows:
            result = list()
            # Row name = first index in description tuple
            column_names = list()
            for i in cursor.description:
                column_names.append(i[0])
            result.append(column_names)
            not_bucketed.append(column_names)
            expired.append(column_names)

            for row in rows:
                result.append(row)

        else:
            raise EmptyOrigin

except ValueError:
    sys.exit("ERROR: Not a valid origin")
except InactiveClient:
    sys.exit("ERROR: Inactive client")
except EmptyOrigin:
    sys.exit("ERROR: Empty origin")
except:
    sys.exit("ERROR: Could not retrieve origin")

finally:
    db.close()

# TO DO: analyze and print bucket info

# User has to install webdriver
browser = webdriver.Firefox()

# These will be called once

def nano_login():
    browser.get("https://tools.nanonation.net/")
    browser.find_element_by_id("Login1_UserName").send_keys(NANO_LOGIN)
    browser.find_element_by_id ("Login1_Password").send_keys(NANO_PASSWORD)
    browser.find_element_by_id("Login1_LoginButton").click()

def client_select():
    digital_signage = browser.find_element_by_css_selector("#ctl00_ContentPlaceHolder_Main_ConsoleNav1_Inner_dvSignage21")
    digital_signage.click()
    client = browser.find_element_by_link_text(client_name)
    client.click()

def load_all_media():
    browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_ViewStyleList').click()
    # TO DO: implement webdriverwait?
    browser.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder_Main_MediaDialogMaximumResults"]/option[4]').click()
    rows_count = browser.execute_script("return document.getElementsByTagName('tr').length")
    print(rows_count)

# These will be looped over n times (n = number of media groups)

def load_all_media_groups():
    browser.find_element_by_css_selector("td.tab:nth-child(5)").click()
    # TO DO: implement webdriverwait?
    browser.find_element_by_xpath('/html/body/form/div[3]/div[3]/div[2]/div/div/select/option[4]').click()
    
def select_media_group(media_group):
    browser.find_element_by_link_text(media_group).click()

def select_track(filename):
    pass
    track = browser.find_element_by_xpath('//tr/td[(contains(text(),'+ '"' + filename + '"'+'))]/../td/input[@class="check_file"]')
    track.click()

def add_media():
    if browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_mediaGroupItems > tbody > tr.empty_row > td > span > center'):
        browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_AddToMediaGroup').click()
        for f in filenames:
            select_track(f)
        browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_SelectMediaItemDialog_SaveButton').click()
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.ID, 'ctl00_ContentPlaceHolder_Main_insertAtItems_ctl01_expandingRow'))).click()
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.ID, 'ctl00_ContentPlaceHolder_Main_mediaGroupItems_0_EditMediaGroupItemLink')))
        browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_saveButton').click()

# For testing: export CSV of 
# TO DO: export not_bucketed, expired csvs if lists are not empty
"""
with open(origin_csv_file_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in result:
        csvwriter.writerow(row)
"""

nano_login()
client_select()
load_all_media()
# set media group, loop through until it changes
load_all_media_groups()
select_media_group('TEST MEDIA GROUP')
add_media()

# browser.quit()
 
