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

`--dry` does a dry run. It won't modify your emails, but will show you a small preview of the emails it finds. 

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

