"""Monitor Synapse Project"""
import time

import pandas as pd
import synapseclient
from synapseclient import EntityViewSchema, EntityViewType, Synapse

ONEDAY = 86400000 # milliseconds, default delta t is 10 days prior


def create_file_view(syn: Synapse, project_id: str) -> EntityViewSchema:
    """Creates file view for project

    Args:
        syn: Synapse connection
        project_id: Synapse project id

    Returns:
        Synapse file view"""
    view = EntityViewSchema(name="(monitor) project files",
                            parent=project_id,
                            scopes=project_id,
                            includeEntityTypes=[EntityViewType.FILE],
                            add_default_columns=True,
                            addAnnotationColumns=False)
    return syn.store(view)


def find_new_files(syn: Synapse, view_id: str,
                   epochtime: int = None) -> pd.DataFrame:
    """Performs query to find changed entities in id and render columns

    Args:
        syn: Synapse connection
        view_id: Synapse View Id
        epochtime: Epoch time in milliseconds

    Returns:
        Dataframe with updated entities
    """
    query = ("select id, name, currentVersion, modifiedOn, modifiedBy, createdOn"
             "projectId, type "
             f"from {view_id} where modifiedOn > {epochtime}")
    results = syn.tableQuery(query)
    resultsdf = results.asDataFrame()
    dates = []
    users = []
    for _, row in resultsdf.iterrows():
        dates.append(
            synapseclient.core.utils.from_unix_epoch_time(
                row['modifiedOn']
            ).strftime("%b/%d/%Y %H:%M")
        )
        users.append(syn.getUserProfile(row['modifiedBy'])['userName'])

    resultsdf['modifiedOn'] = dates
    resultsdf['modifiedBy'] = users

    return resultsdf


def _get_audit_time(current_time, days, view, use_last_audit_time=False):
    """Get the epoch time in milliseconds of when to start auditing.

    Args:
        syn: Synapse connection
        view: Synapse EntityViewSchema
        days: Number of days to look for updates.
        use_last_audit_time: Use the last audit time. This value is stored
                             as an annotation on the file view.
                             Default to False.

    Returns:
        Epoch time of current time minus X number of days
    """
    # By default the audit time starts from the day before
    epochtime = current_time - ONEDAY
    # If days is specified, calculate epochtime
    if days is not None:
        epochtime = current_time - days * ONEDAY
    # If use_last_audit_time, check lastAuditTimeStamp
    if use_last_audit_time:
        last_audit_time = view.get("lastAuditTimeStamp")
        if last_audit_time is not None:
            epochtime = last_audit_time[0]
    return epochtime


def get_audit_time(syn, view, days, use_last_audit_time=False):
    """Get the epoch time in milliseconds of when to start auditing and
    store lastAuditTimeStamp annotation on view.

    Args:
        syn: Synapse connection
        view: Synapse EntityViewSchema
        days: Number of days to look for updates.
        use_last_audit_time: Use the last audit time. This value is stored
                             as an annotation on the file view.
                             Default to False.

    Returns:
        Epoch time of current time minus X number of days
    """
    current_time = time.time()*1000
    epochtime = _get_audit_time(current_time, days, view, use_last_audit_time)
    try:
        syn.store(view)
    except synapseclient.core.exceptions.SynapseHTTPError:
        pass

    return epochtime


def monitoring(syn: Synapse, synid: str, userid: str = None,
               email_subject: str = "New Synapse Files",
               days: int = None, use_last_audit_time: bool = False):
    """Monitor a Synapse Project or Fileview.

    Args:
        syn: Synapse connection
        synid: Synapse ID of project or fileview to be monitored.
        userid: User Id of individual to send report
                (Defaults to current user.)
        email_subject: Sets the subject heading of the email sent out.
                       (Defaults to 'New Synapse Files')
        days: Find modifications in the last days
        use_last_audit_time: Use the last audit time. This value is stored
                             as an annotation on the file view.
                             (Default to False)
    """

    entity = syn.get(synid)
    if isinstance(entity, synapseclient.Project):
        # Creates file view
        view = create_file_view(syn, synid)
    elif isinstance(entity, synapseclient.EntityViewSchema):
        view = entity
    else:
        raise ValueError(f"{synid} must be a Synapse Project or File View")

    # Get epoch time for audit start time
    epochtime = get_audit_time(syn, view, days,
                               use_last_audit_time=use_last_audit_time)
    # get dataframe of files
    filesdf = find_new_files(syn, view.id, epochtime=epochtime)
    # Filter out projects and folders
    print(f'Total number of entities = {len(filesdf.index)}')

    # get default user
    userid = syn.getUserProfile()['ownerId'] if userid is None else userid
    # Prepare and send Message
    syn.sendMessage([userid], email_subject,
                    filesdf.to_html(index=False),
                    contentType='text/html')
    return filesdf
