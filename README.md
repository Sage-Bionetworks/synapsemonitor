## Synapse Monitoring
[![Get synapsemonitor from PyPI](https://img.shields.io/pypi/v/synapsemonitor.svg?style=for-the-badge&logo=pypi)](https://pypi.python.org/pypi/synapsemonitor)

Provides tools for monitoring and keeping track of File entity changes in Synapse with the use of File Views. Learn more about [File Views](https://docs.synapse.org/articles/views.html)

## Installation
```
pip install synapsemonitor
```

## Usage

### Monitor Fileview and send email notifications

Monitors a project or entities provided in the scope of a File View for changes and sends an email through the Synapse messaging system to the user specified when changes have been made to the project. Includes a list of changed files.  Please see [Create File View](#create-file-view) if you do not have a File View.

```
usage: synapsemonitor monitor [-h] [--users USERS [USERS ...]] [--output OUTPUT] [--email_subject EMAIL_SUBJECT] [--days days] [--log level] synapse_id

positional arguments:
  synapse_id            Synapse ID of fileview to be monitored.

optional arguments:
  -h, --help            show this help message and exit
  --users USERS [USERS ...], -u USERS [USERS ...]
                        User Id or username of individuals to send report. If not specified will defaults to logged in Synapse user.
  --output OUTPUT, -o OUTPUT
                        Output modified entities into this csv file. (default: None)
  --email_subject EMAIL_SUBJECT, -e EMAIL_SUBJECT
                        Sets the subject heading of the email sent out. (default: New Synapse Files)
  --days days, -d days  Find modifications to entities in the last N days. (default: 1)
  --log level, -l level
                        Set logging output level (default: error)
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

### Docker
There is a Docker repository that is automatically build: `sagebionetworks/synapsemonitor`.  See the available tags [here](https://hub.docker.com/r/sagebionetworks/synapsemonitor).  It is always recommended to use a tag other than `latest` because the `latest` tag can change.  This package requires authentication to Synapse and we highly recommend using a Synapse PAT.  For more information on the [PAT](https://help.synapse.org/docs/Managing-Your-Account.2055405596.html#ManagingYourAccount-PersonalAccessTokens).

```
docker run -e SYNAPSE_AUTH_TOKEN={your_auth_token_here} sagebionetworks/synapsemonitor:v0.0.2 -h
```

### Cronjobs
Often times you will want to run this code periodically to continuously track changes.  One way you can do this is to set up a cronjob. Follow this [beginners guide](https://ostechnix.com/a-beginners-guide-to-cron-jobs/).  Note: you will most likely want to create an ec2 to run your cronjob instead of your laptop.

There are also other technologies that support scheduled execution of code such as AWS lambdas, AWS batch, Kubernetes and etc.  The above is a way of setting a cronjob on your laptop or ec2.
