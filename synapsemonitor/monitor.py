"""Monitor Synapse Project"""
from datetime import datetime, timedelta
from dateutil import tz
import logging
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


def _find_modified_entities_fileview(syn: Synapse, syn_id: str, days: int = 1) -> list:
    """Finds entities scoped in a fileview modified in the past N number of days

    Args:
        syn: Synapse connection
        syn_id: Synapse Fileview Id
        days: N number of days

    Returns:
        List of synapse ids
    """
    # Update the view
    # _force_update_view(syn, view_id)
    query = (
        f"select id from {syn_id} where "
        f"modifiedOn > unix_timestamp(NOW() - INTERVAL {days} DAY)*1000"
    )
    results = syn.tableQuery(query)
    resultsdf = results.asDataFrame()
    return resultsdf["id"].tolist()


def _find_modified_entities_file(syn: Synapse, syn_id: str, days: int = 1) -> list:
    """Determines if entity was modified in the past N number of days

    Args:
        syn: Synapse connection
        syn_id: Synapse File Id
        days: N number of days

    Returns:
        List of synapse ids
    """
    entity = syn.get(syn_id, downloadFile=False)
    # Entity modified on returns UTC time
    utc_mod = datetime.strptime(entity["modifiedOn"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=tz.tzutc()
    )
    utc_now = datetime.now().replace(tzinfo=tz.tzutc())
    if utc_mod > utc_now - timedelta(days=days):
        return [syn_id]
    return []


def _traverse(
    syn: Synapse,
    synid_root: str,
    include_types: typing.List = ["file"],
) -> list:
    """Traverse Synapse entity hierarchy to gather all descendant
    entities of a root entity.
    Args:
        syn: Synapse connection
        synid_root: Synapse ID of root entity.
        include_types: Must be a list of entity types (ie. [“folder”,”file”])
            which can be found here:
            http://docs.synapse.org/rest/org/sagebionetworks/repo/model/EntityType.html
    Returns:
        List of descendant Synapse IDs without root Synapse ID
    """

    synid_desc = []

    # full traverse depends on examining folder entities, even if not requested
    include_types_mod = set(include_types)
    include_types_mod.add("folder")
    include_types_mod = list(include_types_mod)

    synid_children = syn.getChildren(parent=synid_root, includeTypes=include_types_mod)
    for synid_child in synid_children:
        entity_type = synid_child["type"].split(".")[-1].lower().replace("entity", "")
        if entity_type == "folder":
            synid_desc.extend(
                _traverse(
                    syn=syn, synid_root=synid_child["id"], include_types=include_types
                )
            )
        if entity_type in include_types:
            synid_desc.append(synid_child["id"])

    return synid_desc


def _traverse_root(
    syn: Synapse,
    synid_root: str,
    include_types: typing.List = ["file"],
) -> list:
    """Wrapper for call traverse to include root.

    Args:
        syn (Synapse): Synapse connection
        synid_root (str): Synapse ID of root entity.
        include_types (typing.List, optional): Must be a list of entity types (ie. [“folder”,”file”])
            which can be found here:
            http://docs.synapse.org/rest/org/sagebionetworks/repo/model/EntityType.html

    Returns:
        list: List of descendant Synapse IDs with root Synapse ID
    """
    synid_desc = _traverse(syn, synid_root, include_types)
    entity = syn.get(synid_root, downloadFile=False)
    entity_type = entity["concreteType"].split(".")[-1].lower().replace("entity", "")
    if entity_type in include_types:
        synid_desc.append(synid_root)

    return synid_desc


def _find_modified_entities_container(syn: Synapse, syn_id: str, days: int = 1) -> list:
    """Finds entities in a folder or project modified in the past N number of days

    Args:
        syn: Synapse connection
        syn_id: Synapse Folder or Project Id
        days: N number of days

    Returns:
        List of synapse ids
    """
    syn_id_mod = []
    syn_id_children = _traverse_root(syn, syn_id)

    for syn_id_child in syn_id_children:
        syn_id_res = _find_modified_entities_file(syn, syn_id_child, days)
        if syn_id_res:
            syn_id_mod.extend(syn_id_res)

    return syn_id_mod


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


def find_modified_entities(syn: Synapse, syn_id: str, days: int) -> list:
    """Find modified entities based on the type of the input

    Args:
        syn: Synapse connection
        syn_id: Synapse Entity Id
        days: N number of days

    Returns:
        List of synapse ids
    """
    entity = syn.get(syn_id, downloadFile=False)
    if isinstance(entity, synapseclient.EntityViewSchema):
        return _find_modified_entities_fileview(syn=syn, syn_id=syn_id, days=days)
    elif isinstance(entity, (synapseclient.File, synapseclient.Schema)):
        return _find_modified_entities_file(syn=syn, syn_id=syn_id, days=days)
    elif isinstance(entity, (synapseclient.Folder, synapseclient.Project)):
        return _find_modified_entities_container(syn=syn, syn_id=syn_id, days=days)
    else:
        raise ValueError(f"{type(entity)} not supported")


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
    # get dataframe of files
    modified_entities = find_modified_entities(syn=syn, syn_id=syn_id, days=days)
    # Filter out projects and folders
    logging.info(f"Total number of entities = {len(modified_entities)}")

    # get user ids
    user_ids = _get_user_ids(syn, users)

    # TODO: Add function to beautify email message

    # Prepare and send Message
    if modified_entities:
        syn.sendMessage(
            user_ids,
            email_subject,
            ", ".join(modified_entities),
            contentType="text/html",
        )
    return modified_entities
