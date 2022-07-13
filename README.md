# gmail-cleanup
A python script that loads a JSON file full of Gmail labels and durations, and bins or archives them accordingly. 

## Requirements
Python 3.10 or later with `pip`
A [Google Cloud Platform project](https://developers.google.com/workspace/guides/create-project) and [credentials](https://developers.google.com/workspace/guides/create-credentials). Don't forget to add your account as a test user!

## Installation
 1. Install the requirements using `pip -r requirements.txt`
 2. Create the cloud platform project and download the credentials file. Call it `credentials.json` and place it in the same folder as `cleanup.py`
 3. Rename `labels.example.json` to `labels.json` and edit it as per the format below.
 4. Run `python cleanup.py`
 5. Check your inbox to make sure the changes were applied.

## Command line options
There's a few command line options you can use.

`--production` if this is NOT set, no emails will be changed, but instead it'll show you a preview of 5 messages for each label that would be changed if `--production` was set

`--labels` displays all your labels from Gmail.

`--example` creates a file called `labels.gmail.json` which has all of your labels in a JSON format. You just need to change `older_than` and the `actions` and rename to `labels.json`

`--maxresults` sets how many emails to modify at one time. Limited to 500 by Gmail. For example `--maxresults=250`

`--creds` sets the credentials filename to use. Defaults to `credentials.json`. For example `--creds=myfile.json`

`--scope` sets the Gmail scope(s) you want to use. Defaults to `https://www.googleapis.com/auth/gmail.modify`. Use it multiple times to specify multiple scopes. For example `--scope=A --scope=B --scope=C`

## labels.json

`labels.json` should contain a list of Gmail labels, and an action to take. For example:

```json
[
    {
        "labels": ["My/Nested/Label", "Some Other/Nested/Label"],
        "older_than": "14d",
        "actions": {
            "archive": true,
            "mark_as_read": true,
            "trash": false
        }
    },
    {
        "labels": ["Label Name"],
        "older_than": "1y",
        "actions": {
            "archive": false,
            "mark_as_read": true,
            "trash": true
        }
    }
]
```

`labels` is a list containing the names of the labels to modify, and can be either lowercase / hyphen separated as it appears in the search box, or separated with slashes. For example either `banking-bills-energy-use` or `Banking/Bills/Energy Use`
`older_than` specifies how old the email should be before it's acted upon. Valid values are `d`, `m` and `y`. For example `1d` for one day, or `6m` for six months
`actions` must contain the following booleans:
    `archive`: if `true`, removes the `INBOX` label (meaning it gets archived)
    `mark_as_read`: if `true`, removes the `UNREAD` label (meaning it gets marked as read)
    `trash`: if `true`, adds the `TRASH` label (meaning it gets moved to the bin)

