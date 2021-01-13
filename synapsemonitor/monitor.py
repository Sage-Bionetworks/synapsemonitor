"""Monitor Synapse Project"""
import calendar
import time

import pandas as pd
import synapseclient
from synapseclient import Synapse, EntityViewSchema, EntityViewType

ONEDAY=86400000 #default delta t is 10 days prior


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
                            add_default_columns=True)
    return syn.store(view)


def find_new_files(syn: Synapse, project_id: str, view_id: str,
                   days: int = None,
                   update_project: bool = False) -> pd.DataFrame:
    """Performs query to find changed entities in id

    Args:
        syn: Synapse connection
        project_id: Synapse Project Id
        view_id: Synapse View Id
        days: Find modifications in the last days
        update_project: If set will modify the annotations by setting
                        lastAuditTimeStamp to the current time on project.

    Returns:
        Dataframe with updated entities
    """
    t = calendar.timegm(time.gmtime())*1000
    project = syn.get(project_id)
    #Determine the last audit time or overide with lastTime
    if days is None:  # No time specified
        days = project.get('lastAuditTimeStamp', None)
        if days is None:  # No time specified and no lastAuditTimeStamp set
            days = t - ONEDAY*1.1
        else: # days came from annotation strip out from list
            days = days[0]
    print(t, days, project_id, (t-days)/float(ONEDAY), 'days')
    query = ("select id, name, currentVersion, modifiedOn, modifiedBy, type "
             f"from {view_id} where modifiedOn > {days}")
    results = syn.tableQuery(query)
    resultsdf = results.asDataFrame()
    # Add in project and project name
    resultsdf['project'] = project_id
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

    resultsdf['date'] = dates
    resultsdf['users'] = users

    # #Set lastAuditTimeStamp
    if update_project:
        project.lastAuditTimeStamp = t
        try:
            project = syn.store(project)
        except synapseclient.core.exceptions.SynapseHTTPError:
            pass
    return resultsdf


# def compose_message(entityList):
#     """Composes a message with the contents of entityList """

#     messageHead =('<h4>Time of Audit: %s </h4>'%time.ctime() +
#                  '<table border=1><tr>'
#                  '<th>Project</th>'
#                  '<th>Entity</th>'
#                  '<th>Ver.</th>'
#                  '<th>Type</th>'
#                  '<th>Change Time</th>'
#                  '<th>Contributor</th></tr>')
#     lines = [('<tr><td><a href="https://www.synapse.org/#!Synapse:%(projectId)s">%(projectName)s</a></td>'
#               '<td><a href="https://www.synapse.org/#!Synapse:%(entity.id)s">(%(entity.id)s)</a> %(entity.name)s </td>'
#               '<td>%(entity.versionNumber)s</td>'
#               '<td>%(type)s</td>'
#               '<td>%(date)s</td>'
#               '<td><a href="https://www.synapse.org/#!Profile:%(entity.modifiedByPrincipalId)s">%(user)s</a></td></tr>')%item for 
#              item in entityList]
#     return messageHead + '\n'.join(lines)+'</table></body>'


def main(syn: Synapse, projectid: str, userid: str = None,
         email_subject: str = "New Synapse Files",
         days: int = None, update_project: bool = False):
    # Creates file view
    project = syn.get(projectid)
    if not isinstance(project, synapseclient.Project):
        raise ValueError(f"{projectid} must be a Synapse Project")
    view = create_file_view(syn, projectid)
    # Get default days
    days = (None if days is None
            else calendar.timegm(time.gmtime())*1000 - days * ONEDAY)
    # get default user
    userid = syn.getUserProfile()['ownerId'] if userid is None else userid

    # get dataframe of files
    filesdf = find_new_files(syn, projectid, view.id, days=days,
                             update_project=update_project)

    # Filter out projects and folders
    print(f'Total number of entities = {len(filesdf.index)}')

    # Prepare and send Message
    syn.sendMessage([userid], email_subject,
                    filesdf.to_html(index=False),
                    contentType='text/html')
