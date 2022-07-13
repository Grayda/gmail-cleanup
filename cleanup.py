from __future__ import print_function

import os.path
import json
import logging
import sys
import argparse
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# For rotating logs
from logging.handlers import TimedRotatingFileHandler

# For the Gmail API
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

# Our command line arguments
config = None

def main():
    """Looks through a JSON file that contains label names and durations.
    Then goes through each of those labels and gets all the emails, If the email is older than the duration,
    Removes the Inbox label. Basically cleans up your inbox without having to do it manually.
    """

    global credentials
    global service
    global logger

    # Set up logging. This handles logging to stdout and also to a rotating log ile. 
    logger = setupLogging()

    # Gets our command line arguments. 
    getArgs()
    
    # Loads token.json if present, otherwise prompts the user to complete the OAuth flow.
    credentials, service = authorizeAPI(config['scope'])

    # If we just want to output the labels, do so and then quit
    if config['labels']:
        for label in getLabels():
            print(label)
        exit()

    # If we want to generate a sample file containing the user's labels, do that and quit
    if config['example']:
        generateLabelsJSON()
        exit()

    # Limit to 5 if doing a dry run, because if you're going for 500 emails (the maximum), that's a hell of a lot of API calls and would take forever
    if not config['production']:
        config['maxresults'] = 5

    # Load the JSON file with labels and relative dates in it
    json = loadJSON(config["json"], config['schema'])

    # Pass the JSON data to the cleanupInbox function
    cleanupInbox(json)

def getArgs():
    """Gets arguments and set up command line stuff.
    We use this to set production mode, get labels etc.
    """
    global config 
 
    parser = argparse.ArgumentParser(description="Script that archives or trashes emails in Gmail based on time rules",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--creds", type=str, help="the credentials file to use", default="credentials.json")
    parser.add_argument("-e", "--example", action="store_true", help="gets all your labels and makes a JSON file")
    parser.add_argument("-j", "--json", type=str, help="the JSON file to load", default="labels.json")
    parser.add_argument("-l", "--labels", action="store_true", help="displays all labels")
    parser.add_argument("-m", "--maxresults", help="maximum number of emails to process in one go. Maximum is 500", type=int, default=500)
    parser.add_argument("-p", "--production", action="store_true", help="production mode (actually changes data)")
    parser.add_argument("-s", "--scope", action='append', help="the gmail API scopes to use. Use multiple times to specify multiple scopes")
    parser.add_argument("-sch", "--schema", type=str, help="The schema file to validate against", default="labels.json.schema")    

    args = parser.parse_args()
    config = vars(args) 

    # If you set a default value for the "append" action in argparse, the default value is always there.
    # We don't want that because if you're calling `--scope`, you want to override the default.
    if not config['scope']:
        config['scope'] = ["https://www.googleapis.com/auth/gmail.modify"]

    # Sanity check for the maxresults flag
    if config['maxresults'] > 500 or config['maxresults'] <= 0:
        print("Max results flag needs to be between 1 and 500 due to Gmail API limitations")
        exit()

def setupLogging():
    """Sets up logging using a rotating log.
    Also logs to the screen if running interactively.
    """

    logger = logging.getLogger("Rotating Log")
    
    # TODO: Make this changeable so you don't get info logs and such clogging up your system in production. 
    logger.setLevel(logging.DEBUG)

    # TODO: Change this so the user can set the log filename and rotation options as they see fit
    fileHandler = TimedRotatingFileHandler("results.log", when="d", interval=30, backupCount=6)

    # Create a handler to log to stdout
    streamHandler = logging.StreamHandler(sys.stdout)

    # Add the date, time and level to the messages being logged
    format = logging.Formatter(fmt="%(asctime)s - %(levelname)s: %(message)s")

    # Set the formatters for both log types, and add the handlers to the logger
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

    global config

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
                config['creds'], scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    return creds, service

def generateLabelsJSON(filename="labels.gmail.json"):
    """Downloads the user's labels from Gmail and makes a JSON file they can edit.
    Defaults to archiving messages older than 99 years, so no harm is done if the values aren't changed
    """
    
    # Retrieve the labels from Gmail
    labels = getLabels()

    logger.info("Downloaded {num} labels from Gmail".format(num=len(labels)))

    jsonFile = []

    # Change this to change the defaults used in the example JSON
    template = {
        "labels": [],
        "older_than": "99y",
        "actions": {
            "archive": True,
            "mark_as_read": True,
            "trash": False
        }
    }

    for label in labels:
        # Make a copy of the template, otherwise all the labels in the JSON file will be exactly the same
        toAdd = template.copy()
        toAdd['labels'] = [label]
        jsonFile.append(toAdd)

    # Save the file and indent it for niceness
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jsonFile, f, ensure_ascii=False, indent=4)

    logger.info("{filename} saved successfully".format(filename=filename))

    return

def getLabels():
    """Downloads the user's labels from Gmail.
    This only returns user labels, not system labels. 
    """
    labels = service.users().labels().list(userId='me').execute().get('labels')

    if not labels:
        logger.warn('No labels found')

    labels = sorted((l['name'] for l in labels if l['type'] == 'user'))

    return labels

def cleanupInbox(json):
    """Takes a JSON file that contains an array of objects with three properties: `labels`, `older_than` and `actions`. It then searches
    Gmail for the specified labels, then performs the necessary action on them. 
    """
    
    for label in json:
        messages = findEmails(label)
        if not messages:
            continue
        handleEmails(messages, label)


def findEmails(labels):
    """Searches for emails that match the given label and age. 
    When the email is found, pass it to 
    """

    if type(labels['labels']) is list:
        formattedLabels = " OR ".join(f'label:"{l}"' for l in labels['labels'])
    else:
        formattedLabels = 'label:"{l}"'.format(l=labels['labels'])

    try:
        logger.info("Retrieving emails with these labels: {labels}".format(labels=labels['labels']))
        # Call the Gmail API to get all messages that are in the inbox and have the specified label, and are older than the specified date
        messages = service.users().messages().list(userId='me', q="in:inbox {labels} older_than:{older_than}".format(labels=formattedLabels, older_than=labels['older_than']), maxResults=config['maxresults']).execute().get('messages', [])

        # If there are no messages, warn, and return
        if not messages:
            logger.warning('No messages found for labels: {labels}'.format(labels=labels['labels']))
            return

        # Go through and pluck all the IDs from the messages, then return those
        return [m['id'] for m in messages]

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        logger.error(f'An error occurred: {error}')

    return


def handleEmails(messages, label):
    """Takes a list of message IDs and updates the labels on them. 
    """

    global service
    global config

    # The labels we're going to add and remove from the specified messages
    addLabels = []
    removeLabels = []

    if label['actions']['mark_as_read'] == True:
        removeLabels.append('UNREAD')
    if label['actions']['archive'] == True:
        removeLabels.append('INBOX')
    if label['actions']['trash'] == True:
        addLabels.append('TRASH')

    # Only take action if we've got labels to add or remove
    if addLabels or removeLabels:
        body = {'ids': messages, 'removeLabelIds': removeLabels,
                'addLabelIds': addLabels}
        
        # Only take action if we're in production
        if config['production']:
            result = service.users().messages().batchModify(userId='me', body=body).execute()
        else:
            logger.warning("Skipping modification step due to production flag not being set")
            for message in messages:
                # Retrieve details about the messages from Gmail and show a snippet.
                # This helps you work out if you've typed the labels correctly.
                details = getEmailDetails(message)
                logger.info("Preview of {id}: {snippet}".format(id=message, snippet=details['snippet']))
        
        logger.info("Modified {num} emails with IDs of {ids} by adding these labels: {added} and removing these labels: {removed}".format(
            num=len(messages), ids=messages, added=addLabels, removed=removeLabels))

    return

def getEmailDetails(mail):
    """Loads information about a specific email from Gmail
    """
    
    return service.users().messages().get(userId='me', id=mail).execute()    

def loadJSON(filename, schema):
    """Loads a JSON file if it exists"""
    
    if os.path.exists(schema):
        schemaFile = json.load(open(schema))

    # TODO: Specify an (optional?) schema for verification purposes
    if os.path.exists(filename):
        jsonFile = json.load(open(filename))

        try:
            print("Validating")
            validate(jsonFile, schemaFile)
        except ValidationError as error:
            logger.error(f"Schema validation failed! {error.message}")
            exit()

        return jsonFile 
    else:
        logger.error("Unable to find {filename}!".format(filename=filename))
        exit()

if __name__ == '__main__':
    main()
