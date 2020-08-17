import os
import sys
import pymysql
from selenium import webdriver

# Not using these right now, but may come in handy
import csv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# User has to install webdriver
browser = webdriver.Firefox()

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

try:
    db = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME, cursorclass=pymysql.cursors.Cursor)

except:
    print("ERROR: Could not connect to database")

try:
    arg = sys.argv[1]
    if arg.isdigit():
        origin_id = arg

    with db.cursor() as cursor:
        cursor.execute("CALL SeleniumOriginName("+ origin_id +")")
        origin_name = cursor.fetchone()[0]
        origin_csv_file_path = os.path.join(cwd, origin_name + "_Full Origin.csv")

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
            for row in rows:
                result.append(row)

        else:
            sys.exit("ERROR: No rows found")

except:
    print("ERROR: Could not retrieve origin")

finally:
    db.close()

def nano_login():
    browser.get("https://tools.nanonation.net/")
    browser.find_element_by_id("Login1_UserName").send_keys(NANO_LOGIN)
    browser.find_element_by_id ("Login1_Password").send_keys(NANO_PASSWORD)
    browser.find_element_by_id("Login1_LoginButton").click()

def client_select():
    digital_signage = browser.find_element_by_css_selector("#ctl00_ContentPlaceHolder_Main_ConsoleNav1_Inner_dvSignage21")
    digital_signage.click()
    client = browser.find_element_by_css_selector("tr.alternate:nth-child(12) > td:nth-child(1) > a:nth-child(1)")
    client.click()

def load_all_media():
    browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_ViewStyleList').click()
    browser.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder_Main_MediaDialogMaximumResults"]/option[4]').click()

def load_all_media_groups():
    browser.find_element_by_css_selector("td.tab:nth-child(5)").click()
    browser.find_element_by_xpath('/html/body/form/div[3]/div[3]/div[2]/div/div/select/option[4]').click()
    
def select_media_group():
    browser.find_element_by_link_text('TEST MEDIA GROUP').click()

def select_track(filename):
    pass
    # TO DO: Get path to parent element from child's <td> text, click associated checkbox
        # If this is a wild goose chase, maybe keep media in icon layout rather than list
            # Icons have more ideal structure with filename = title, but checkboxes are hidden
        # Possibly need to scroll stuff into view:
            # browser.execute_script("arguments[0].scrollIntoView();", ELEMENT)

def add_media():
    browser.find_element_by_css_selector("#ctl00_ContentPlaceHolder_Main_AddToMediaGroup").click()
    for f in filenames:
        select_track(f)
    # TO DO: submit, add to media group, save

# For testing: export CSV of 
# TO DO: export not_bucketed, expired csvs if lists are not empty
with open(origin_csv_file_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in result:
        csvwriter.writerow(row)

nano_login()
client_select()
load_all_media()
load_all_media_groups()
select_media_group()
add_media()

# browser.quit()
 
