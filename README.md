## Synapse Monitoring

Provides tools for monitoring and keeping track of changes in Synapse. There are two main features provided email notifications and activity feeds. 


## Installation
```
git clone https://github.com/Sage-Bionetworks/synapseMonitor.git
cd synapse-monitor
pip install .
```

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
```

### Create email notifications to changes

Monitors a projects for changes and sends an email through the synapse messaging system to the user specified when changes have been made to the project. Includes a list of changed files.

```
synapsemonitor project -h

usage: synapsemonitor project [-h] [--userid USERID]
                              [--email_subject EMAIL_SUBJECT] [--days days]
                              [--update_project]
                              projectid

positional arguments:
  projectid             Synapse ID of project to be monitored.

optional arguments:
  -h, --help            show this help message and exit
  --userid USERID       User Id of individual to send report, defaults to
                        current user.
  --email_subject EMAIL_SUBJECT
                        Sets the subject heading of the email sent out
                        (defaults to New Synapse Files)
  --days days, -d days  Find modifications in the last days
  --update_project      If set will modify the annotations by setting
                        lastAuditTimeStamp to the current time on each
                        project.
```
