import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import os 
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


# Find all mentioned links on page by iterating over the root path and finding all html tags of <a href> which indicates a link
def get_links_on_page(root_url):
    links = set()
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    page = requests.get(root_url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    for a in soup.find_all('a'):
        link = a.get('href')
        if link != None:
            if  not link.startswith( 'https://www.canyon.com'):
                link = 'https://www.canyon.com' + link
            links.add(link)
    return links

# takes in a string @url and returns the html content as a string with some cleaning done
def get_page_contents(url):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    contents = requests.get(url, headers=headers).text
    contents = contents.replace("\\n", " ")
    contents = contents.replace('\n', " ")
    return contents

# Return the name of the bike based upon the url by some regex matching
def get_bike_model_name(url):
    first_match_pattern = re.search( '/outlet-bikes/road-bikes/(.*)/', url)
    second_match_pattern = re.search( '/endurace/cf-sl/(.*)/', url)
    return first_match_pattern or second_match_pattern

# Return the size of the bike based upon the html content and regex patterns to find the size info for
def get_size_info(content, size_html_pattern1, size_html_pattern2, size_options):
    output_sizes = []
    # find index locations of the bike sizes in the html string
    size_indices1  = [m.start() for m in re.finditer(size_html_pattern1, content)]
    size_indices2  = [m.start() for m in re.finditer(size_html_pattern2, content)]
    size_indices = size_indices1 + size_indices2
    size_indices.sort()
    for size_idx in size_indices:
        # update the index since the content we're looking for starts at the end of the pattern
        if size_idx in size_indices1:
            new_idx = size_idx + len(size_html_pattern1)
        else:
            new_idx = size_idx + len(size_html_pattern2)

        size_string = content[new_idx: new_idx+100].replace(' ', '').replace("</div>", '')
        if any(size_string.find(size_option) > -1 for size_option in size_options):
            output_sizes.append(size_string)
        else:
            print("invalid size")

    return output_sizes

# Return whether the bike is available or sold out based upon the html contnet and a regex pattern indicating where to find this info
def get_availability_info(content, stock_string_pattern):
    # find index locations of availability status 
    available_indices = [m.start() for m in re.finditer(stock_string_pattern, content)]
    output_availability = []
    for availability_idx in available_indices:
        # update the index since the content we're looking for starts at the end of the pattern
        new_idx = availability_idx + len(stock_string_pattern)
        stock_string = content[new_idx: new_idx+1000].lower().replace('  ', '')
        #print(stock_string)
        stock_status = ""
        if "coming soon" in stock_string:
            stock_status = "Coming Soon"
        elif "sold out" in stock_string:
            stock_status = "Sold Out"
        elif "low stock" in stock_string or "left in stock" in stock_string or "in-stock" in stock_string or 'saleprice' in stock_string:
            stock_status = "In-Stock"

        output_availability.append(stock_status)

    return output_availability

# Return a dataframe containing information about the bike sizes and availabilities for each bike
def make_dataframe(model, bike_sizes, bike_availabilities, url):
    output_df = pd.DataFrame(index = range(0,len(bike_sizes)), columns = ['model', 'bike_size', 'availability', 'expected_arrival', 'date_checked', 'url'])
    output_df['model'] = model
    output_df['bike_size'] = bike_sizes
    output_df['availability'] = bike_availabilities
    output_df['date_checked'] = datetime.now()
    output_df['isCurrentlyAvailable'] = False
    output_df['url'] = url
    output_df.loc[output_df.availability == 'Low Stock', 'isCurrentlyAvailable'] = True
    output_df.loc[output_df.availability == 'In-Stock', 'isCurrentlyAvailable'] = True
    return output_df


def get_email_information(keyVaultName, email_password_secret_name, sender_email_address_secret_name, receiver_email_address_secret_name):
    
    # Grab azure keyvault secret for authorizing email
    KVUri = f"https://{keyVaultName}.vault.azure.net"

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KVUri, credential=credential)

    # Return passwords and email addresses
    sender_email_address= client.get_secret(sender_email_address_secret_name).value
    sender_email_password = client.get_secret(email_password_secret_name).value
    receiver_email_address = client.get_secret(receiver_email_address_secret_name).value

    return sender_email_address, sender_email_password, receiver_email_address

def main():

    # Find all endurance CF SL bike URLs (since there are multiple models) by iterating over the root path and finding relevant links
    urls = []
    all_cf_sl_links = get_links_on_page('https://www.canyon.com/en-us/road-bikes/endurance-bikes/endurace/cf-sl/#sections-products')
    for link in all_cf_sl_links:
        if 'endurace-cf-sl'  in link:
            urls.append(link)

    # Find all bike URLs in the outlet page (Previous years models that we still care about)
    all_outlet_links = get_links_on_page('https://www.canyon.com/en-us/outlet-bikes/road-bikes/')
    for link in all_outlet_links:
        if '/en-us/outlet-bikes/road-bikes/'  in link and 'html' in link:
            urls.append(link)

    # Regex patterns to look for information about the size of the bike
    size_string_pattern1 = '<div class="productConfiguration__variantType js-productConfigurationVariantType">'
    size_string_pattern2 = '<div class="productConfiguration__variantType">' 
    
    # Valid size options to validated against
    size_options = ['2XS', 'XS', 'S', 'M', 'L', 'XL', '2XL']

    # Regex pattern to look for info about the availability of the bike
    stock_string_pattern = '<div class="productConfiguration__availabilityMessage'

    # Iterate over every bike URL gathered to find out the different sizes and availability
    all_outputs = []
    for bike_url in urls:
        model = get_bike_model_name(bike_url).group(1)
        print("Processing model: " + model)
        contents = get_page_contents(bike_url)
        output_sizes = get_size_info(contents, size_string_pattern1, size_string_pattern2, size_options)
        output_availability = get_availability_info(contents, stock_string_pattern)
        if len(output_sizes) != len(output_availability):
            print("Data not matching") 

        each_output_df = make_dataframe(model, output_sizes, output_availability, bike_url)    
        all_outputs.append(each_output_df)

    output_df = pd.concat(all_outputs)

    # Filter to any smalls in stock and send an email report if there are any
    SIZE_WANTED = 'S'
    in_stock_models =  output_df[(output_df['bike_size'] == SIZE_WANTED) & (output_df.isCurrentlyAvailable == True)]
    send_email = in_stock_models.shape[0] > 0 

    # grab email addresses and passwords from Azure KeyVault
    keyVaultName = "bikealertkeyvault"
    email_password_secret_name = "emailSenderPassword"
    sender_email_address_secret_name = 'SenderEmailAddress'
    receiver_email_address_secret_name = 'ScottsEmailAddress' # change this later to Henry's email. And add it as a secret to KV
    sender_email_address, sender_email_password, receiver_email_address = get_email_information(keyVaultName, 
    email_password_secret_name, sender_email_address_secret_name, receiver_email_address_secret_name
    )

    # Create email message
    msg = MIMEMultipart()
    msg['Subject'] = "Canyon Bike Alert"
    msg['From'] = sender_email_address


    html = """\
    <html>
    <head></head>
    <body>
        {0}
    </body>
    </html>
    """.format(in_stock_models.to_html())

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    # Send email report if there's stock using gmail 
    if send_email:
        port = 465  # For SSL

        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email_address, sender_email_password)
            server.sendmail(sender_email_address, receiver_email_address, msg.as_string())

    else:
        print("Size not available")
    


if __name__ == "__main__":
    main()
    print('test')