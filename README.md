## Synapse Monitoring
[![Get synapsemonitor from PyPI](https://img.shields.io/pypi/v/synapsemonitor.svg?style=for-the-badge&logo=pypi)](https://pypi.python.org/pypi/synapsemonitor)

Provides tools for monitoring modified Synapse entities.    

## Installation
```
pip install synapsemonitor
```

## Usage

```
usage: synapsemonitor [-h] [-c file] [--log {debug,info,warning,error}] {monitor,create} ...

Checks for new or modified Synapse entities. If a Project or Folder entity is specified, all File entity
descendants will be monitored. Users can create a Synapse File View to track the contents of Projects or
Folders with many file entities more efficiently. You can use the `create` function provided in this package
to create a File View.

optional arguments:
  -h, --help            show this help message and exit
  -c file, --synapse_config file
                        Synapse config file with user credentials: (default
                        /Users/hhunterzinck/.synapseConfig)
  --log {debug,info,warning,error}, -l {debug,info,warning,error}
                        Set logging output level (default: error)

commands:
  The following commands are available:

  {monitor,create}      For additional help: "synapsemonitor <COMMAND> -h"
    monitor             Find new or modified File entities.
    create              Creates a File View that will list all the File entities under the specified scopes
                        (Synapse Folders or Projects). This will allow you to query for the files contained in
                        your specified scopes. This will NOT track the other entities currently: PROJECT,
                        TABLE, FOLDER, VIEW, DOCKER.
```

### Monitor File entities and send email notifications

Monitors Synapse entities for modifications and sends an email through the Synapse messaging system to the user specified when modified entities are detected. Prints a list of modified File entities.  If the specified entity is a container (Project or Folder), all descendant File entities are monitored.  If the specified entity is a File View, all contained enties are monitored.  

```
usage: synapsemonitor monitor [-h] [--users USERS [USERS ...]] [--output OUTPUT] [--email_subject EMAIL_SUBJECT] [--rate rate] synapse_id

positional arguments:
  synapse_id            Synapse ID of entity to be monitored.

optional arguments:
  -h, --help            show this help message and exit
  --users USERS [USERS ...], -u USERS [USERS ...]
                        User Id or username of individuals to send report. If not specified, defaults to logged in Synapse user.
  --output OUTPUT, -o OUTPUT
                        Output modified entities into this csv file. (default: None)
  --email_subject EMAIL_SUBJECT, -e EMAIL_SUBJECT
                        Sets the subject heading of the email sent out. (default: New Synapse Files)
  --value value, -v value
                        Find modifications to File entities in the last
                        {value} {unit}. (default: 1)
  --unit unit, -t unit  Find modifications to File entities in the last
                        {value} {unit}. (default: 'day')
```

### Create File View

Creates a File View that will list all the File entities under the specified scopes (Synapse Folders or Projects). This will allow you to query for the files contained in your specified scopes. This will NOT track the other entities currently: PROJECT, TABLE, FOLDER, VIEW, DOCKER.

```
usage: synapsemonitor create [-h] --scope_ids SCOPE_IDS [SCOPE_IDS ...] NAME project_id

positional arguments:
  NAME                  File View name
  project_id            Synapse Project Id to store file view in

optional arguments:
  -h, --help            show this help message and exit
  --scope_ids SCOPE_IDS [SCOPE_IDS ...]
                        Synapse Folder / Project Ids
```

### Docker
There is a Docker repository that is automatically build: `sagebionetworks/synapsemonitor`.  See the available tags [here](https://hub.docker.com/r/sagebionetworks/synapsemonitor).  It is always recommended to use a tag other than `latest` because the `latest` tag can change.  This package requires authentication to Synapse and we highly recommend using a Synapse PAT.  For more information on the [PAT](https://help.synapse.org/docs/Managing-Your-Account.2055405596.html#ManagingYourAccount-PersonalAccessTokens).

```
docker run -e SYNAPSE_AUTH_TOKEN={your_auth_token_here} sagebionetworks/synapsemonitor:v0.0.2 -h
```

### Cronjobs
Often times you will want to run this code periodically to continuously track changes.  One way you can do this is to set up a cronjob. Follow this [beginners guide](https://ostechnix.com/a-beginners-guide-to-cron-jobs/).  Note: you will most likely want to create an ec2 to run your cronjob instead of your laptop.

There are also other technologies that support scheduled execution of code such as AWS lambdas, AWS batch, Kubernetes and etc.  The above is a way of setting a cronjob on your laptop or ec2.
