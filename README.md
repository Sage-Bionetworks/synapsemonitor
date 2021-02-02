## Synapse Monitoring
[![Get synapsemonitor from PyPI](https://img.shields.io/pypi/v/synapsemonitor.svg?style=for-the-badge&logo=pypi)](https://pypi.python.org/pypi/synapsemonitor)

Provides tools for monitoring and keeping track of File entity changes in Synapse with the use of File Views. Learn more about [File Views](https://docs.synapse.org/articles/views.html)

## Installation
```
pip install synapsemonitor
```

### Monitor Fileview and send email notifications

Monitors a project or entities provided in the scope of a File View for changes and sends an email through the Synapse messaging system to the user specified when changes have been made to the project. Includes a list of changed files.  Please see [Create File View](#create-file-view) if you do not have a File View.

```
usage: synapsemonitor view [-h] [--user_ids USER_IDS [USER_IDS ...]]
                           [--output OUTPUT] [--email_subject EMAIL_SUBJECT]
                           [--days days]
                           id

positional arguments:
  id                    Synapse ID of fileview to be monitored.

optional arguments:
  -h, --help            show this help message and exit
  --user_ids USER_IDS [USER_IDS ...]
                        User Id of individuals to send report. If not
                        specified will defaults to logged in Synapse user.
  --output OUTPUT       Output modified entities into this csv file.
  --email_subject EMAIL_SUBJECT
                        Sets the subject heading of the email sent
                        out.(default: New Synapse Files)
  --days days, -d days  Find modifications to entities in the last N
                        days.(default: 1)
```

### Create File View

Creates a file view that will list all the File entities under the specified scopes (Synapse Folders or Projects). This will allow you to query for the files contained in your specified scopes. This will NOT track the other entities currently: PROJECT, TABLE, FOLDER, VIEW, DOCKER.

```
synapsemonitor create-file-view -h
usage: synapsemonitor create-file-view [-h] --scope_ids SCOPE_IDS
                                       [SCOPE_IDS ...]
                                       NAME project_id

positional arguments:
  NAME                  File View name
  project_id            Synapse Project Id to store file view in

optional arguments:
  -h, --help            show this help message and exit
  --scope_ids SCOPE_IDS [SCOPE_IDS ...]
                        Synapse Folder / Project Ids
```

<!--

### Creating activity feeds

The command updateActivityFeed.py can be used to create a weekly or monthly activity feeds.  For example to create an activity log of changes in the progenitor cell biology consortium project (syn1773109 ) and storing the output the wiki with id 69074 you would run:

```
updateActivityFeed.py -i week syn1773109 -w 69074
```


Usage:

```
usage: updateActivityFeed.py [-h] [--wiki wikiId] [-i interval]
                             [--earliest date] [--config file]
                             project

Looks for changes to project in defined time ranges and updates a wiki

positional arguments:
  project               Synapse ID of projects to be monitored.

optional arguments:
  -h, --help            show this help message and exit
  --wiki wikiId, -w wikiId
                        Optional sub-wiki id where to store change-log
                        (defaults to project wiki)
  -i interval, --interval interval
                        divide changesets into either "week" or "month" long
                        intervals (default week)
  --earliest date, -e date
                        The start date for which changes will be searched
                        (defaults to 1-January-2014)
  --config file         Synapse config file with user credentials (overides
                        default ~/.synapseConfig)
``` -->
