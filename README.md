# gmail-cleanup
A python script that loads a JSON file full of Gmail labels and durations, and bins or archives them accordingly. 

## Requirements
Python 3.10 or later with `pip`
A [Google Cloud Platform project](https://developers.google.com/workspace/guides/create-project) and [credentials](https://developers.google.com/workspace/guides/create-credentials). Don't forget to add your account as a test user!

## Installation
 1. Install the requirements using `pip -r requirements.txt`
 2. Create the cloud platform project and download the credentials file. Call it `credentials.json` and place it in the same folder as `cleanup.py`
 3. Run `python cleanup.py --example` to download all your Gmail labels and create a JSON file you can edit (optional)
 4. Rename `labels.gmail.json` to `labels.json` and edit it. If you didn't do step 3, then just rename `labels.example.json` and edit that instead.
 5. Run `python cleanup.py` to do a dry run and make sure everything works
 6. Run `python cleanup.py --production` to do an actual run
 7. Check your inbox to make sure the changes were applied.

## Command line options
There's a few command line options you can use.

`--help` shows the help, as well as the defaults. 

`--production` if this is NOT set, no emails will be changed, but instead it'll show you a preview of 5 messages for each label that would be changed if `--production` was set

`--labels` displays all your labels from Gmail.

`--json` specifies the file or URL to load the labels and times from. If passing a URL, it needs to be obtainable with via an unauthenticated GET request

`--example` creates a file called `labels.gmail.json` which has all of your labels in a JSON format. You just need to change `older_than` and the `actions` and rename to `labels.json`

`--maxresults` sets how many emails to modify at one time. Limited to 500 by Gmail. For example `--maxresults=250`

`--creds` sets the credentials filename to use. Defaults to `credentials.json`. For example `--creds=myfile.json`

`--scope` sets the Gmail scope(s) you want to use. Defaults to `https://www.googleapis.com/auth/gmail.modify`. Use it multiple times to specify multiple scopes. For example `--scope=A --scope=B --scope=C`

`--schema` is the schema file to validate `labels.json` against. Defaults to `labels.json.schema`

`--log-level` is the minimum logging level. Choices are `DEBUG`, `INFO`, `WARNING`, `ERROR` and `CRITICAL`. Defaults to `INFO`

`--log-file` is the file to log to. Defaults to `results.log`

`--log-interval` determines how long to log for before rotating the log file. Defaults to `30` days

`--log-backup-count` determines how many log files to keep before overwriting the oldest one. Defaults to `6` (so you get 6*30 = 180 days before the oldest log gets overwritten)

## labels.json

`labels.json` should contain a list or string of Gmail labels, or a list or string of a Gmail query, and the actions to take. For example:

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
        "labels": "Some/Label",
        "older_than": "14d",
        "actions": {
            "archive": true,
            "mark_as_read": true,
            "trash": false
        }
    },
    {
        "query": ["has:attachment", "older_than:2y", "larger:10M"],
        "actions": {
            "archive": false,
            "mark_as_read": true,
            "trash": true
        }
    },
    {
        "query": "from:user@example.com older_than:6m",
        "actions": {
            "archive": false,
            "mark_as_read": true,
            "trash": true
        }
    }, {
        "query": "label:Sample/Label",
        "actions": {
            "add": [
                "TRASH"
            ],
            "remove": [
                "INBOX"
            ]
        }
    }
]
```

`labels` is an array or string containing the name(s) of the labels to modify. This is useful for grouping multiple labels under one timeframe. 

`older_than` specifies how old the email should be before it's acted upon. Valid values are `d`, `m` and `y`. For example `1d` for one day, or `6m` for six months. 

`query` is an array or a string that represents a [Gmail query](https://support.google.com/mail/answer/7190?hl=en). **NOTE: If you use a query, DO NOT include the `older_than` property in your JSON. Instead, add it inline. For example `["from:user@example.com", "older_than:2m"]`. If you have both `query` and `older_than`, you'll get an error!**

`actions` is a list of actions to take. You can either pass named actions, or a list of labels to add or remove

If you want to use named actions, then:

`archive`: if `true`, removes the `INBOX` label (meaning it gets archived)

`mark_as_read`: if `true`, removes the `UNREAD` label (meaning it gets marked as read)

`trash`: if `true`, adds the `TRASH` label (meaning it gets moved to the bin)

If you want to list the labels, then:

`add`: Must be a list of labels to add.

`remove`: Must be a list of labels to remove

NOTE: If you have named actions, you can't have `add` and `remove`. If you have `add` and `remove`, you can't have named actions. 

## Notes

While this has been tested on my own Gmail inbox, it hasn't been tested thoroughly. There may be bugs, or ways you can archive or delete more than you intended to. Use this script at your own risk!

And when writing Gmail queries, be careful, because no sanity checks are done, meaning that just using a query that is nothing but `older_than:1d` has the potential to trash your entire inbox. You have been warned!