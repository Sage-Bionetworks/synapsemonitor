### Synapse Monitoring

Provides tools for monitoring and keeping track of changes in Synapse. There are two main features provided email notifications and activity feeds.

#### Creating activity feeds

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

#### Create email notifications to changes

Monitors a list of projects for changes and sends an email through the synapse messaging system to the user specified when changes have been made to the projects.  Includes a list of changed files.

```
usage: monitor.py [-h] [--userId USERID]
                  [--projects [projects [projects ...]]] [--days days]
                  [--updateProject] [--config file]

Checks for new/modified entities in a project.

optional arguments:
  -h, --help            show this help message and exit
  --userId USERID       User Id of individual to send report, defaults to
                        current user.
  --projects [projects [projects ...]], -p [projects [projects ...]]
                        Synapse IDs of projects to be monitored.
  --days days, -d days  Find modifications in the last days
  --updateProject       If set will modify the annotations by setting
                        lastAuditTimeStamp to the current time on each
                        project.
  --config file         Synapse config file with user credentials (overides
                        default ~/.synapseConfig)
```
