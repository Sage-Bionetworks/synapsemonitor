"""Update activity feed"""
import datetime
from io import StringIO
import time
import dateutil.parser

import pandas as pd
import synapseclient

from . import monitor

EPOCHSTART = datetime.datetime(1970, 1, 1)
# This is the threshold for number of entities that will show up in the
# summary updates
MAX_FOR_SUMMARY = 4


def get_changes(syn, start, end, view_id):
    """Finds entities that are new, or updated given a start and end time

    Args:
        syn: Synapse connection
        start: Start time
        end: end time
        view_id: Synapse View Id
    """
    start = int((start - EPOCHSTART).total_seconds())*1000
    end = int((end - EPOCHSTART).total_seconds())*1000
    # If start time is greater than the time now, there are no files
    if start > time.time()*1000:
        return pd.DataFrame()

    # Get entities
    query = (
        "select id, name, parentId, currentVersion, modifiedOn, "
        "modifiedBy, type "
        f"from {view_id} where modifiedOn > {start} and modifiedOn < {end}"
    )
    # Determine updated and new entities
    entities_table = syn.tableQuery(query)
    entitiesdf = entities_table.asDataFrame()

    new_entities_idx = entitiesdf['currentVersion'] == 1
    updated_entities_idx = ~new_entities_idx
    if new_entities_idx.any():
        entitiesdf.loc[new_entities_idx, 'status'] = 'new'
    if updated_entities_idx.any():
        entitiesdf.loc[updated_entities_idx, 'status'] = 'updated'
    entitiesdf.set_index('id', inplace=True)
    return entitiesdf


@synapseclient.core.utils.memoize
def get_parent_name(syn, synid):
    """Returns the name of an entity"""
    entity = syn.get(synid, downloadFile=False)
    return entity.name.replace('_', '\_')


def print_updates(syn, md, df):
    """Writes the summary of the updates in df to md string."""
    group_by_parent = df.groupby('parentId')
    for parent, files_in_parent in group_by_parent:
        # Determine whether to put a summary for containers
        if files_in_parent.shape[0] > MAX_FOR_SUMMARY:
            n_updates = sum(files_in_parent.status == 'updated')
            n_new = sum(files_in_parent.status == 'new')
            md.write('* ')
            if n_updates > 1:
                md.write(f'{n_updates} files were updated ')
            elif n_updates == 1:
                md.write(f'{n_new} file was updated ')
            if n_updates > 0 and n_new > 0:
                md.write('and ')
            if n_new > 1:
                md.write(f'{n_new} new files were added ')
            elif n_new == 1:
                md.write(f'{n_new} new file was added ')
            md.write('to [{}](#!Synapse:{})\n'.format(
                get_parent_name(syn, parent), parent
            ))
        else:
            for entity_id, row in files_in_parent.iterrows():
                username = syn.getUserProfile(row['modifiedBy']).userName
                userlink = '[{}](https://www.synapse.org/#!Profile:{}'.format(
                    username, row['modifiedBy']
                )
                if row.status == 'new':
                    md.write('* [{}](#!Synapse:{}) was added by {})\n'.format(
                        row['name'].replace('_', '\_'), entity_id, userlink
                    ))
                else:
                    md.write('* [{}](#!Synapse:{}) was updated to version {} by {})\n'.format(
                        row['name'].replace('_', '\_'), entity_id,
                        row['currentVersion'], userlink
                    ))


def update_wiki(syn, owner, wikiId, md):
    """Fetches and existing wiki and overwrites the content. """
    wiki = syn.getWiki(owner, wikiId)
    wiki.markdown = md.getvalue()
    return syn.store(wiki)


def create_view_changelog(syn, view_id, project_id, delta_time,
                          earliest_time, wiki_id):
    """
    Create entity view changelog
    """
    # earliest_time = "1-Jan-2021"
    # delta_time = "week"
    # view_id = "syn24172191"
    # project_id = "syn4990358"
    # wiki_id = "607852"

    earliest_time = dateutil.parser.parse(earliest_time)
    today = datetime.datetime.today()
    # Get the first time end for collecting updates
    if delta_time == 'week':
        t_end = today - datetime.timedelta(days=today.weekday()-7)
    elif delta_time == 'month':
        year, month = divmod(today.month+1, 12)
        year, month = (year+1, 12) if month == 0 else (year, month)
        t_end = datetime.datetime(today.year + year, month, 1)
    # Collect markdown strings
    md = StringIO()
    while t_end > earliest_time:
        # Calculate time start based on interval string
        if delta_time == 'week':
            t_start = t_end - datetime.timedelta(days=7)
            header_text = '##week of {}\n'.format(
                t_start.strftime('%d-%B-%Y')
            )
        else:
            year, month = divmod(t_end.month-1, 12)
            year, month = (year-1, 12) if month == 0 else (year, month)
            t_start = datetime.datetime(t_end.year + year, month, 1)
            header_text = '##{}\n'.format(t_start.strftime('%B-%Y'))
        print(f'{t_start} -> {t_end}')
        df = get_changes(syn, t_start, t_end, view_id)
        t_end = t_start
        if df.empty:
            continue
        # Write the output
        md.write(header_text)
        print_updates(syn, md, df)
    update_wiki(syn, project_id, wiki_id, md)
    md.close()
