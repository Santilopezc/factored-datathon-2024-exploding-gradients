import boto3
import os
import requests
import zipfile
import io
import pandas as pd
from parsel import Selector
from datetime import datetime

credentials = pd.read_csv('Data_Storage/isabelmorar_accessKeys.csv')
access_key_id = credentials['Access key ID'][0]
secret_access_key = credentials['Secret access key'][0]

# AWS S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id= access_key_id,        
    aws_secret_access_key= secret_access_key,
    region_name='us-east-1' 
)

bucket_name = 'datathonfactored2024' 
folder_name = 'GDELT GKG Files/'

gkg_url = 'http://data.gdeltproject.org/gkg/index.html'
response = requests.get(gkg_url)
sel = Selector(text = response.text)

start_date = datetime(2024, 8, 1) #Cambiar para que se upload todos
end_date = datetime(2024, 8, 13)

# Get the links as a url that can be downloaded later
links = sel.xpath('//a/@href').extract()

gkg_links = []
gkgcounts_links = []
base = "http://data.gdeltproject.org/gkg/"

for link in links:
    if link.endswith('.zip'):
        date_str = link.split('.')[0]
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if start_date <= file_date <= end_date:
                if 'gkgcounts' in link:
                    gkgcounts_links.append(base + link)
                else:
                    gkg_links.append(base + link)
        except ValueError:
            continue

# GKG Complete Files
for link in gkg_links:
    file_name = link.split('/')[-1]

    # Download the file into memory
    response = requests.get(link)
    file_content = io.BytesIO(response.content)
    
    # Extract the zip file contents in memory and upload each file directly to S3
    with zipfile.ZipFile(file_content, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            with zip_ref.open(file_info) as extracted_file:

                date = file_info.filename.split('.')[0]
                file_name = f"{date}.gkg.csv"
                s3_key = folder_name + file_name

                s3_client.upload_fileobj(extracted_file, bucket_name, s3_key)
                print(f"Uploaded {file_name} to S3 bucket {bucket_name} with key {s3_key}")

print("All GKG files downloaded and uploaded to S3 directly. \n")

# GKG Counts
folder_name = 'GDELT GKG Files/gkgcounts/'
for link in gkgcounts_links:
    file_name = link.split('/')[-1]

    # Download the file into memory
    response = requests.get(link)
    file_content = io.BytesIO(response.content)
    
    # Extract the zip file contents in memory and upload each file directly to S3
    with zipfile.ZipFile(file_content, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            with zip_ref.open(file_info) as extracted_file:

                date = file_info.filename.split('.')[0]
                file_name = f"{date}.gkgcounts.csv"
                s3_key = folder_name + file_name

                s3_client.upload_fileobj(extracted_file, bucket_name, s3_key)
                print(f"Uploaded {file_name} to S3 bucket {bucket_name} with key {s3_key}")

print("All gkgcounts files downloaded and uploaded to S3 directly. \n")