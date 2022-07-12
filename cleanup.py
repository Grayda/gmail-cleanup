from __future__ import print_function

import os.path
import json
import logging
import sys

# For rotating logs
from logging.handlers import TimedRotatingFileHandler

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Holds our credentials that we use to communicate with the Gmail API
credentials = None

# For logging
logger = None

# The Gmail API service. We use this to build and execute requests.
service = None

# Change this when you're sure that everything is running as expected. Maximum is 500
maxResults = 5

# The OAuth2 scope we want. By default we want full access because we want to delete emails. If you don't want to delete emails, just archive them, you can
# set the scope to https://www.googleapis.com/auth/gmail.labels which is much safer and only lets you add / remove labels
scopes = ['https://www.googleapis.com/auth/gmail.modify']


def main():
    """Looks through a JSON file that contains label names and durations.
    Then goes through each of those labels and gets all the emails, If the email is older than the duration,
    Removes the Inbox label. Basically cleans up your inbox without having to do it manually.
    """

    global credentials
    global service
    global logger

    logger = setupLogging()

    credentials, service = authorizeAPI(scopes)

    # Load the JSON file with labels and relative dates i nit
    json = loadJSON("labels.json")

    # Pass that data to the cleanupInbox function
    cleanupInbox(json)


def setupLogging():

    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.DEBUG)

    fileHandler = TimedRotatingFileHandler("results.log", when="d", interval=30, backupCount=6)
    streamHandler = logging.StreamHandler(sys.stdout)

    format = logging.Formatter(fmt="%(asctime)s - %(levelname)s: %(message)s")

    fileHandler.setFormatter(format)
    streamHandler.setFormatter(format)
    
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)


    return logger


def authorizeAPI(scopes):
    """Loads the token.json file if it's there, or creates it if it doesn't exist. Requires a Google account.
    If you get 403 errors when going through the OAuth2 workflow, be sure to add yourself as a test user to your OAuth2 consent screen.
    This function also returns a built service, so you can start making API calls right away. 
    """

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    return creds, service


def cleanupInbox(json):
    """Takes a JSON file that contains an array of objects with three properties: `name`, `date` and `action`. It then retrieves your Gmail labels,
    then loops through the JSON. If the label in your JSON is a label in Gmail, it loads the first 500 messages with that label and compares dates.
    If the date the mail was sent is OLDER than the relative time specified in the `date` property in the JSON, it performs the action in the JSON,
    which can be `archive` or `delete`    
    """
    for label in json:
        findEmails(label)


def findEmails(label):
    """Searches for emails that match the given label and age. 
    When the email is found, pass it to 
    """

    global maxResults

    try:
        # Call the Gmail API
        messages = service.users().messages().list(userId='me', q="in:inbox label:\"{label}\" older_than:{older_than}".format(
            label=label['label'], older_than=label['older_than']), maxResults=maxResults).execute().get('messages', [])

        if not messages:
            logger.warning('No messages found.')
            return

        handleEmails([m['id'] for m in messages], label)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        logger.error(f'An error occurred: {error}')

    return


def handleEmails(messages, label):

    global service

    addLabels = []
    removeLabels = []

    if label['actions']['mark_as_read'] == True:
        removeLabels.append('UNREAD')
    if label['actions']['archive'] == True:
        removeLabels.append('INBOX')
    if label['actions']['trash'] == True:
        addLabels.append('TRASH')

    if addLabels or removeLabels:
        body = {'ids': messages, 'removeLabelIds': removeLabels,
                'addLabelIds': addLabels}
        result = service.users().messages().batchModify(userId='me', body=body).execute()
        logger.info("Modified {num} emails with IDs of {ids} by adding these labels: {added} and removing these labels: {removed}".format(
            num=len(messages), ids=messages, added=addLabels, removed=removeLabels))

    return


def loadJSON(filename):
    jsonFile = open(filename)
    return json.load(jsonFile)


if __name__ == '__main__':
    main()
