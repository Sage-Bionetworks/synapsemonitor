"""Monitor Synapse Project"""
import time

import pandas as pd
import synapseclient
from synapseclient import EntityViewSchema, EntityViewType, Project, Schema, Synapse

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


def find_new_files(syn: Synapse, project: Project, view_id: str,
                   epochtime: int = None) -> pd.DataFrame:
    """Performs query to find changed entities in id and render columns

    Args:
        syn: Synapse connection
        project_id: Synapse Project Id
        view_id: Synapse View Id
        epochtime: Epoch time in milliseconds

    Returns:
        Dataframe with updated entities
    """
    query = ("select id, name, currentVersion, modifiedOn, modifiedBy, type "
             f"from {view_id} where modifiedOn > {epochtime}")
    results = syn.tableQuery(query)
    resultsdf = results.asDataFrame()
    # Add in project and project name
    resultsdf['project'] = project.id
    resultsdf['projectName'] = project.name
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


def get_epoch_start(project: Project, current_time: int,
                    days: int = None) -> int:
    """Calculate the epoch time of current time minus X number of days.

    Args:
        project: Synapse Project
        current_time: Current time in epoch milliseconds
        days: Number of days to look for updates

    Returns:
        Epoch time of current time minus X number of days
    """
    # Determine the last audit time or overide with lastTime
    if days is None:  # No time specified
        days = project.get('lastAuditTimeStamp', None)
        if days is None:  # No time specified and no lastAuditTimeStamp set
            days = current_time - ONEDAY*1.1
        else: # days came from annotation strip out from list
            days = days[0]
    # Get epochtime value
    else:
        days = current_time - days * ONEDAY
    return days


def monitor_project(syn: Synapse, projectid: str, userid: str = None,
                    email_subject: str = "New Synapse Files",
                    days: int = None, update_project: bool = False):
    """Monitor files

    Args:
        update_project: If set will modify the annotations by setting
                        lastAuditTimeStamp to the current time on project.
    """
    # Get current audit time
    current_time = time.time()*1000

    # Creates file view
    project = syn.get(projectid)
    if not isinstance(project, synapseclient.Project):
        raise ValueError(f"{projectid} must be a Synapse Project")
    # Create file view
    view = create_file_view(syn, projectid)

    # get default user
    userid = syn.getUserProfile()['ownerId'] if userid is None else userid

    epochtime = get_epoch_start(project, current_time, days=days)
    # get dataframe of files
    filesdf = find_new_files(syn, project, view.id, epochtime=epochtime)

    # Filter out projects and folders
    print(f'Total number of entities = {len(filesdf.index)}')

    # Prepare and send Message
    syn.sendMessage([userid], email_subject,
                    filesdf.to_html(index=False),
                    contentType='text/html')

    # Set lastAuditTimeStamp
    if update_project:
        project.lastAuditTimeStamp = current_time
        try:
            project = syn.store(project)
        except synapseclient.core.exceptions.SynapseHTTPError:
            pass


def create_team_tracking(syn, parent):
    """Set up the table that will track team members"""
    cols = [synapseclient.table.Column(name='userid', columnType='USERID'),
            synapseclient.table.Column(name='teamid', columnType='USERID')]
    schema = Schema(name='(monitor) team members', columns=cols, parent=parent)
    return syn.store(schema)


def monitor_team(syn, teamid, projectid, userid=None):
    """Monitor team members"""
    project = syn.get(projectid)
    if not isinstance(project, synapseclient.Project):
        raise ValueError(f"{projectid} must be a Synapse Project")

    # Create team member tracking table
    team_tracker = create_team_tracking(syn, projectid)
    existing_members = syn.tableQuery(f"select * from {team_tracker.id}")
    existing_membersdf = existing_members.asDataFrame()

    # Get userid
    userid = syn.getUserProfile()['ownerId'] if userid is None else userid
    # TODO: check team requests
    # team_requests = syn.restGET('/team/%s/openRequest' % team)['results']
    # Get current team members
    team_member = syn.getTeamMembers(teamid)
    new_members = {'userid': [], 'teamid': []}
    for member in team_member:
        userid = member['member']['ownerId']
        # Get new members only
        if userid not in existing_membersdf['userid']:
            new_members['userid'].append(userid)
            new_members['teamid'].append(teamid)
    mew_membersdf = pd.DataFrame(new_members)

    syn.store(synapseclient.Table(team_tracker.id, mew_membersdf))

    syn.sendMessage([userid], 'New Team Members',
                    mew_membersdf.to_html(index=False),
                    contentType='text/html')
