"""Monitor Synapse Project"""
import pandas as pd
import synapseclient
from synapseclient import EntityViewSchema, EntityViewType, Synapse


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


def find_modified_entities(syn: Synapse, view_id: str,
                           days: int = 1) -> pd.DataFrame:
    """Performs query to find modified entities in id and render columns
    These modified entities include newly uploaded ones

    Args:
        syn: Synapse connection
        view_id: Synapse View Id
        epochtime: Epoch time in milliseconds

    Returns:
        Dataframe with updated entities
    """
    query = ("select id, name, currentVersion, modifiedOn, modifiedBy, "
             f"createdOn, projectId, type from {view_id} where "
             f"modifiedOn > unix_timestamp(NOW() - INTERVAL {days} DAY)*1000")
    results = syn.tableQuery(query)
    resultsdf = results.asDataFrame()
    modified_on_dates = []
    created_on_dates = []
    users = []
    for _, row in resultsdf.iterrows():
        modified_on_dates.append(
            synapseclient.core.utils.from_unix_epoch_time(
                row['modifiedOn']
            ).strftime("%b/%d/%Y %H:%M")
        )
        created_on_dates.append(
            synapseclient.core.utils.from_unix_epoch_time(
                row['createdOn']
            ).strftime("%b/%d/%Y %H:%M")
        )
        users.append(syn.getUserProfile(row['modifiedBy'])['userName'])

    resultsdf['modifiedOn'] = modified_on_dates
    resultsdf['createdOn'] = created_on_dates
    resultsdf['modifiedBy'] = users

    return resultsdf


def _force_update_view(syn, view_id):
    """File views are not indexed unless someone queries them by
    going to the file view on Synapse or querying them via a function
    call.  This will force the update of the file view to ensure the most
    up to date fileview is used.

    Args:
        syn: Synapse connection
        view_id: Synapse ID of fileview to be monitored.
    """
    syn.tableQuery(f"select * from {view_id} limit 1")


def monitoring(syn: Synapse, view_id: str, user_ids: list = None,
               email_subject: str = "New Synapse Files",
               days: int = 1) -> pd.DataFrame:
    """Monitor the modifications of an entity scoped by a Fileview.

    Args:
        syn: Synapse connection
        synid: Synapse ID of fileview to be monitored.
        userid: User Ids of individual to send report.  If empty,
                defaults to current logged in Synapse user.
        email_subject: Sets the subject heading of the email sent out.
                       (default: 'New Synapse Files')
        days: Find modifications in the last N days (default: 1)

    Returns:
        Dataframe with files modified within last N days
    """

    entity = syn.get(view_id)
    # Code review decision to only allow file views so that
    # Users can decide where they want to store their own fileview
    # and can choose the scope of the fileview. (Scope meaning)
    # the entities they want to have tracked.
    if not isinstance(entity, synapseclient.EntityViewSchema):
        raise ValueError(f"{view_id} must be a Synapse File View")

    # get dataframe of files
    filesdf = find_modified_entities(syn, entity.id, days=days)
    # Filter out projects and folders
    print(f'Total number of entities = {len(filesdf.index)}')

    # get users
    if user_ids is None:
        users = [syn.getUserProfile()['ownerId']]
    else:
        users = [syn.getUserProfile(user)['ownerId'] for user in user_ids]

    # Prepare and send Message
    syn.sendMessage(users, email_subject,
                    filesdf.to_html(index=False),
                    contentType='text/html')
    return filesdf
