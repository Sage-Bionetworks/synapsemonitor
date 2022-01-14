"""Monitor Synapse Project"""
import typing

import pandas as pd
import synapseclient
from synapseclient import EntityViewSchema, EntityViewType, Synapse


def create_file_view(
    syn: Synapse, name: str, project_id: str, scope_ids: typing.List[str]
) -> EntityViewSchema:
    """Creates a file view that will list all the File entities under
    the specified scopes (Synapse Folders or Projects). This will
    allow you to query for the files contained in your specified scopes.
    This will NOT track the other entities currently: PROJECT, TABLE,
    FOLDER, VIEW, DOCKER.

    Args:
        syn: Synapse connection
        name: File view name
        project_id: Synapse project id to store your file view
        scope_ids: List of Folder or Project synapse Ids

    Returns:
        Synapse file view
    """
    view = EntityViewSchema(
        name=name,
        parent=project_id,
        scopes=scope_ids,
        includeEntityTypes=[EntityViewType.FILE],
        add_default_columns=True,
        addAnnotationColumns=False,
    )
    return syn.store(view)


def _render_fileview(
    syn: Synapse, viewdf: pd.DataFrame, tz_name="US/Pacific"
) -> pd.DataFrame:
    """Renders file view values such as changing modifiedOn from
    Epoch time to US/Pacific datetime and Synapse userids to usernames

    Args:
        syn: Synapse connection
        viewdf: File view dataframe
        tz_name: Timezone database name
                 https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

    Returns:
        Rendered File view dataframe

    """
    viewdf["createdOn"] = (
        pd.to_datetime(viewdf["createdOn"], unit="ms")
        .dt.tz_localize("utc")
        .dt.tz_convert(tz_name)
    )
    viewdf["modifiedOn"] = (
        pd.to_datetime(viewdf["modifiedOn"], unit="ms")
        .dt.tz_localize("utc")
        .dt.tz_convert(tz_name)
    )
    users = [syn.getUserProfile(user)["userName"] for user in viewdf["modifiedBy"]]
    viewdf["modifiedBy"] = users
    return viewdf


def find_modified_entities_fileview(
    syn: Synapse, syn_id: str, days: int = 1
) -> pd.DataFrame:
    """Performs query to find modified entities in id and render columns
    These modified entities include newly uploaded ones

    Args:
        syn: Synapse connection
        view_id: Synapse View Id
        epochtime: Epoch time in milliseconds

    Returns:
        Dataframe with updated entities
    """
    # Update the view
    # _force_update_view(syn, view_id)
    query = (
        "select id, name, currentVersion, modifiedOn, modifiedBy, "
        f"createdOn, projectId, type from {syn_id} where "
        f"modifiedOn > unix_timestamp(NOW() - INTERVAL {days} DAY)*1000"
    )
    results = syn.tableQuery(query)
    resultsdf = results.asDataFrame()
    return _render_fileview(syn, viewdf=resultsdf)


def find_modified_entities_file(syn: Synapse, syn_id: str, days: int = 1):
    raise NotImplementedError


def find_modified_entities_container(syn: Synapse, syn_id: str, days: int = 1):
    raise NotImplementedError


def _force_update_view(syn: Synapse, view_id: str):
    """File views are not indexed unless someone queries them by
    going to the file view on Synapse or querying them via a function
    call.  This will force the update of the file view to ensure the most
    up to date fileview is used.

    Args:
        syn: Synapse connection
        view_id: Synapse ID of fileview to be monitored.
    """
    syn.tableQuery(f"select * from {view_id} limit 1")


def _get_user_ids(syn: Synapse, users: list = None):
    """Get users ids from list of user ids or usernames.  This will also
    confirm that the users specified exist in the system

    Args:
        syn: Synapse connection
        users: List of Synapse user Ids or usernames

    Returns:
        List of Synapse user Ids.
    """
    if users is None:
        user_ids = [syn.getUserProfile()["ownerId"]]
    else:
        user_ids = [syn.getUserProfile(user)["ownerId"] for user in users]
    return user_ids


def determine_monitoring_strategy(
    syn: Synapse, syn_id: str
) -> find_modified_entities_fileview | find_modified_entities_file | find_modified_entities_container:
    """Determine how to get modified entities based on the type of the input"""
    entity = syn.get(syn_id, downloadFile=False)
    if isinstance(entity, synapseclient.EntityViewSchema):
        return find_modified_entities_fileview
    # elif isinstance(entity, synapseclient.File):
    #     return find_modified_entities_file
    # elif isinstance(entity, (synapseclient.Folder, synapseclient.Project)):
    #     return find_modified_entities_container
    else:
        raise NotImplementedError(f"{type(entity)} not supported")


def monitoring(
    syn: Synapse,
    syn_id: str,
    users: list = None,
    email_subject: str = "New Synapse Files",
    days: int = 1,
) -> pd.DataFrame:
    """Monitor the modifications of an entity scoped by a Fileview.

    Args:
        syn: Synapse connection
        synid: Synapse ID of fileview to be monitored.
        users: User Id or usernames of individual to send report.
               If empty, defaults to current logged in Synapse user.
        email_subject: Sets the subject heading of the email sent out.
                       (default: 'New Synapse Files')
        days: Find modifications in the last N days (default: 1)

    Returns:
        Dataframe with files modified within last N days
    """
    # Determine way to get updated entities
    find_modified_entities = determine_monitoring_strategy(syn=syn, syn_id=syn_id)

    # get dataframe of files
    filesdf = find_modified_entities(syn=syn, syn_id=syn_id, days=days)
    # Filter out projects and folders
    print(f"Total number of entities = {len(filesdf.index)}")

    # get user ids
    user_ids = _get_user_ids(syn, users)

    # TODO: Add function to beautify email message

    # Prepare and send Message
    if not filesdf.empty:
        syn.sendMessage(
            user_ids,
            email_subject,
            filesdf.to_html(index=False),
            contentType="text/html",
        )
    return filesdf
