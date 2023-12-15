import csv
import json
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

def init_driver():
    driver = webdriver.Chrome()
    driver.wait = WebDriverWait(driver, 5)
    return driver

def login(driver, username, password):
    time.sleep(5)
    url = 'https://www.instagram.com/'
    driver.get(url)
    print('Initializing a driver (done)')
    time.sleep(2)
    print('Importing the login credentials (done)')
    time.sleep(2)
    username_input = driver.find_element(By.NAME, "username")
    username_input.send_keys(username)
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)
    time.sleep(2)  
    login_button = driver.find_element(By.CSS_SELECTOR, "button._acan._acap._acas._aj1-._ap30")
    login_button.click()
    time.sleep(10)
    print('Logged successfully')

import re

from bs4 import BeautifulSoup

def get_comments_and_replies(html): 
    soup = BeautifulSoup(html, 'html.parser')
    comment_blocks = soup.find_all('div', class_='x1uhb9sk')  # Sélecteur pour les blocs de commentaires

    all_comments = []
    for block in comment_blocks:
        try:
            # Extraction du commentaire principal
            user_link = block.find('a', class_='x1i10hfl')
            username = user_link.get('href').strip('/') if user_link else ""
            comment_text_span = block.find('span', class_='x1lliihq')
            comment_text = comment_text_span.text.strip() if comment_text_span else ""

            comment_data = {'username': username, 'comment': comment_text, 'replies': []}

            # Extraction des réponses
            reply_blocks = block.find_all('div', class_='x540dpk')  # Sélecteur pour les réponses
            for reply in reply_blocks:
                reply_user_link = reply.find('a', class_='x1i10hfl')
                reply_username = reply_user_link.get('href').strip('/') if reply_user_link else ""
                reply_text_span = reply.find('span', class_='x1lliihq')
                reply_text = reply_text_span.text.strip() if reply_text_span else ""

                if reply_username and reply_text:
                    comment_data['replies'].append({'username': reply_username, 'comment': reply_text})

            all_comments.append(comment_data)

        except AttributeError:
            continue

    return all_comments


def scroll_comments_section(driver, post_address):
    driver.get(post_address)
    time.sleep(3)
    
    comments_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6"))
    )

    last_height = driver.execute_script("return arguments[0].scrollHeight", comments_container)

    while True:
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", comments_container)
        time.sleep(2)  
        
        new_height = driver.execute_script("return arguments[0].scrollHeight", comments_container)
        if new_height == last_height:
            break  
        last_height = new_height

    return driver.page_source

def save_comments_with_replies_to_file(comments, filename="comments.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        for comment in comments:
            if comment['comment']:  # Vérifier si le commentaire principal n'est pas vide
                file.write(f"{comment['username']}: {comment['comment']}\n")
                for reply in comment['replies']:
                    if reply['comment']:  # Vérifier si la réponse n'est pas vide
                        file.write(f"\t{reply['username']}: {reply['comment']}\n")
                file.write("\n")  # Ajouter une ligne vide entre les groupes de commentaires pour la clarté

def clean_comments_file(file_path):
    unique_comments = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Ajouter des lignes uniques à l'ensemble
            unique_comments.add(line)

    with open(file_path, 'w', encoding='utf-8') as file:
        for comment in unique_comments:
            file.write(comment)

def remove_duplicate_lines_and_merge(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    unique_lines = set()
    cleaned_lines = []
    previous_line = ""

    for line in lines:
        # Suppression des doublons
        if line not in unique_lines:
            unique_lines.add(line)
            
            # Fusion avec la ligne précédente si elle commence par ':'
            if line.startswith(':'):
                cleaned_lines[-1] = cleaned_lines[-1].strip() + ' ' + line.lstrip(':').strip() + '\n'
            else:
                cleaned_lines.append(line)
                previous_line = line

    with open(filename, 'w', encoding='utf-8') as file:
        file.writelines(cleaned_lines)

import csv
import pandas as pd

def convert_txt_to_csv(txt_file, csv_file):
    with open(txt_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Username', 'Comment', 'Reply Username', 'Reply Comment'])

        current_username = ''
        current_comment = ''
        for line in lines:
            line = line.strip()
            if line:
                if not line.startswith('\t'):  # Nouveau commentaire
                    if current_username and current_comment:  # Écrire le commentaire précédent
                        writer.writerow([current_username, current_comment, '', ''])
                    parts = line.split(': ', 1)
                    current_username = parts[0]
                    current_comment = parts[1] if len(parts) > 1 else ''
                else:  # Réponse au commentaire
                    reply_parts = line.strip('\t').split(': ', 1)
                    reply_username = reply_parts[0]
                    reply_comment = reply_parts[1] if len(reply_parts) > 1 else ''
                    writer.writerow([current_username, current_comment, reply_username, reply_comment])
                    current_comment = ''  # Réinitialiser le commentaire actuel après avoir écrit la réponse

        # Écrire le dernier commentaire si nécessaire
        if current_username and current_comment:
            writer.writerow([current_username, current_comment, '', ''])


if __name__ == "__main__":
    
    with open('credentials.json', 'r') as file:
        credentials = json.load(file)

    username = credentials['username']
    password = credentials['password']
    post_address = credentials['post_address']

    driver = init_driver()

    login(driver, username, password)

    expanded_page_source = scroll_comments_section(driver, post_address)
    
    time.sleep(10)

    comments_data = get_comments_and_replies(expanded_page_source)

    save_comments_with_replies_to_file(comments_data)

    remove_duplicate_lines_and_merge('comments.txt')

    convert_txt_to_csv('comments.txt', 'comments.csv')

    df = pd.read_csv('comments.csv')
    print(df.head())

    driver.quit()
