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
synapsemonitor update_activity -h

synapsemonitor update_activity syn4990358 --wiki 607852 -e 1-Dec-2020

```

### Create email notifications to changes

Monitors a projects for changes and sends an email through the synapse messaging system to the user specified when changes have been made to the project. Includes a list of changed files.

```
synapsemonitor monitor -h

usage: synapsemonitor monitor [-h] [--userid USERID]
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
