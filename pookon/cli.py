import os
import yaml
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pydantic import BaseModel
import click
import pickle

# Pydantic model
class Contact(BaseModel):
    name: str
    email: str

# Google API setup
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

def get_google_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('creds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

# Sync function
def sync_contacts_to_markdown(contacts, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for contact in contacts:
        filename = f"{contact.name.replace(' ', '_')}.md"
        filepath = os.path.join(output_folder, filename)
        yaml_data = yaml.dump(contact.dict())
        with open(filepath, 'w') as f:
            f.write('---\n')
            f.write(yaml_data)
            f.write('---\n')

# Sync function
def sync_contacts_to_markdown_raw(contacts, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for contact in contacts:
        names = contact.get('names', [])    

        try:
            name = names[0]['displayName']
        except:
            # get a random name
            name = f"nameless {contact['resourceName'].replace('people/', '')}"


        filename = f"{name.replace(' ', '_')}.md"
        filepath = os.path.join(output_folder, filename)
        yaml_data = yaml.dump(contact)
        try:
            with open(filepath, 'w') as f:
                f.write('---\n')
                f.write(yaml_data)
                f.write('---\n')
        except:
            # use uuid as filename
            filename = f"{contact['resourceName'].replace('people/', '')}.md"
            filepath = os.path.join(output_folder, filename)
            with open(filepath, 'w') as f:
                f.write('---\n')
                f.write(yaml_data)
                f.write('---\n')

# CLI command
@click.command()
@click.option('--output-folder', default='contacts', help='Folder to store the Markdown files')
def main(output_folder):
    creds = get_google_credentials()
    service = build('people', 'v1', credentials=creds)
    all_fields = "addresses,ageRanges,biographies,birthdays,calendarUrls,clientData,coverPhotos,emailAddresses,events,externalIds,genders,imClients,interests,locales,locations,memberships,metadata,miscKeywords,names,nicknames,occupations,organizations,phoneNumbers,photos,relations,sipAddresses,skills,urls,userDefined"
    results = service.people().connections().list(resourceName='people/me', pageSize=100, personFields=all_fields).execute()
    connections = results.get('connections', [])

    contacts = []
    while True:
        page_token = results.get('nextPageToken')
        if not page_token:
            break
        results = service.people().connections().list(resourceName='people/me', pageSize=100, pageToken=page_token, personFields='names,emailAddresses').execute()
        connections.extend(results.get('connections', []))

    for person in connections:
        contacts.append(person)
        # names = person.get('names', [])
        # emails = person.get('emailAddresses', [])
        # if names and emails:
        #     # contact = Contact(name=names[0]['displayName'], email=emails[0]['value'])
        #     contact = Contact(name=names, email=emails)

        #     contacts.append(contact)
    

    # sync_contacts_to_markdown(contacts, output_folder)
    sync_contacts_to_markdown_raw(contacts, output_folder)


if __name__ == '__main__':
    main()
