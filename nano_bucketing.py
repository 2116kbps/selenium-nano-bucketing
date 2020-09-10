import os
import sys
import csv
from datetime import datetime

import pymysql
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

timestamp = datetime.now().strftime("%Y-%m-%d_%I-%M-%S-%p")

# Retreive credentials
cwd = os.path.dirname(os.path.abspath(__file__))
keyfile = os.path.join(cwd, 'keys.txt')
chrome_exec = os.path.join(cwd, 'chromedriver')
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

# These variables will help construct error logs if an exception is raised
global_counter = 0
saved_index = 0

class InactiveClient(Exception):
    pass

class EmptyOrigin(Exception):
    pass

class NoBuckets(Exception):
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
            directory_name = timestamp + " - " + origin_name
            csv_file_name = origin_name + "_Not Bucketed.csv"

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
            not_bucketed.append(column_names)

            for row in rows:
                result.append(row)

        else:
            raise EmptyOrigin

    unique_media_groups = tuple(sorted(set(a for a,b,c,d in result)))
    if bool(unique_media_groups[0]) == False:
        raise NoBuckets

except ValueError:
    sys.exit("ERROR: Not a valid origin")
except InactiveClient:
    sys.exit("ERROR: Inactive client")
except EmptyOrigin:
    sys.exit("ERROR: Empty origin")
except NoBuckets:
    sys.exit("ERROR: Origin has not been sorted into buckets")
except:
    sys.exit("ERROR: Could not retrieve origin")

finally:
    db.close()


# User has to install webdriver for Chrome: https://chromedriver.chromium.org/downloads
browser = webdriver.Chrome(executable_path=chrome_exec)

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
    browser.find_element_by_css_selector('#MediaDialogSearchButton').click()
    WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder_Main_FilesContainer > table > tbody > tr:nth-child(250)')))

def select_track(filename):
    track = browser.find_element_by_xpath('//tr/td[(contains(text(),'+ '"' + filename + '"'+'))]/../td/input[@class="check_file"]')
    track.click()

# These will be looped over n times (n = number of media groups)

def load_all_media_groups():
    if client_name == "RED - Nano Client":
        browser.find_element_by_css_selector("td.tab:nth-child(7)").click()
        browser.find_element_by_xpath('/html/body/form/div[3]/div[3]/div[2]/div/div/select/option[4]').click()
        browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_searchButton').click()
    
    else:
        browser.find_element_by_css_selector("td.tab:nth-child(5)").click()
        browser.find_element_by_xpath('/html/body/form/div[3]/div[3]/div[2]/div/div/select/option[4]').click()

    # I would implement presence_of_element_located here (like with load_all_media) but clients don't all have > 200 buckets
    
def select_media_group(media_group):
    browser.find_element_by_link_text(media_group).click()
    
    if client_name == "RED - Nano Client":
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#AddToPlaylistButton'))).click()
    
    else:
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder_Main_AddToMediaGroup'))).click()
    
def save_media_group():
    # Previously used visibility_of_element_located, is this more reliable?
    WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder_Main_SelectMediaItemDialog_SaveButton'))).click()
    
    if client_name == "RED - Nano Client":
        WebDriverWait(browser, 20).until(EC.invisibility_of_element_located((By.ID, "dmpe_backgroundElement")))
        WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#SaveButton'))).click()

    else:
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.ID, 'ctl00_ContentPlaceHolder_Main_insertAtItems_ctl01_expandingRow'))).click()
        WebDriverWait(browser, 20).until(EC.invisibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder_Main_insertAtDialogExtender_backgroundElement")))
        WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder_Main_saveButton'))).click()
        
def add_media_to_media_group():
    # TO DO: Possible distinction between empty and full media groups?
        # if browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_mediaGroupItems > tbody > tr.empty_row > td > span > center'):
    counter = 0
    current_media_group = unique_media_groups[counter]
    select_media_group(current_media_group)

    # Previously used this to click "Add Media, but moved this to select_media_group()"
    #browser.find_element_by_css_selector('#ctl00_ContentPlaceHolder_Main_AddToMediaGroup').click()
    
    for index, item in enumerate(result):
        global_counter = index
        if item[0] == current_media_group:
            try:
                select_track(item[1])
            except:
                not_bucketed.append(result[index])
        else:
            save_media_group()
            counter += 1
            current_media_group = unique_media_groups[counter]
            load_all_media_groups()
            select_media_group(current_media_group)
            try:
                select_track(item[1])
            except:
                not_bucketed.append(result[index])

    save_media_group()
    saved_index = global_counter

def log_remaining_items():
    if saved_index < len(result):
        print("saved index: " + str(saved_index))
        for x in range(saved_index, len(result)):
            # not_bucketed.append(result[x])
            print(result[x])

# Execution
try:
    nano_login()
    client_select()
    load_all_media()
    load_all_media_groups()
    add_media_to_media_group()

except:
    print("Could not complete script - all unbucketed tracks added to " + csv_file_name)
    log_remaining_items()

if len(not_bucketed) > 1:
    os.mkdir(os.path.join(cwd,directory_name))
    origin_csv_file_path = os.path.join(cwd,directory_name,csv_file_name)

    with open(origin_csv_file_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in not_bucketed:
            csvwriter.writerow(row)

# browser.quit()