"""Update activity feed"""
import datetime
from io import StringIO
import time
import dateutil.parser

import pandas as pd
import synapseclient

from . import monitor

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 
          'August', 'September', 'October', 'November', 'December']
EPOCHSTART = datetime.datetime(1970, 1, 1)
MAX_FOR_SUMMARY=4


def get_changes(syn, start, end, view_id):
    """Finds entities updated and changed in month numbered month"""
    start = int((start- EPOCHSTART).total_seconds())*1000
    end = int((end - EPOCHSTART).total_seconds())*1000
    # If start time is greater than the time now, there are no files
    if start > time.time()*1000:
        return pd.DataFrame()

    # updated entities
    update_query = (
        "select id, name, parentId, currentVersion, modifiedOn, "
        "modifiedBy, type "
        f"from {view_id} where modifiedOn > {start} and modifiedOn < {end} "
        "and currentVersion > 1"
    )
    # New entities
    new_query = (
        "select id, name, parentId, currentVersion, modifiedOn, "
        "modifiedBy, type "
        f"from {view_id} where modifiedOn > {start} and modifiedOn < {end} "
        "and currentVersion = 1"
    )

    updated_table = syn.tableQuery(update_query)
    updateddf = updated_table.asDataFrame()
    new_table = syn.tableQuery(new_query)
    newdf = new_table.asDataFrame()

    if not newdf.empty:
        newdf['status'] = 'new'
        newdf.set_index('id', inplace=True)
    if not updateddf.empty:
        updateddf['status'] = 'updated'
        updateddf.set_index('id', inplace=True)
    return pd.concat([newdf, updateddf])


@synapseclient.core.utils.memoize
def get_parent_name(syn, synid):
    """Returns the name of an entity """
    return syn.get(synid, downloadFile=False).name.replace('_', '\_')


def print_updates(syn, md, df):
    """Writes the summary of the updates in df to md string. """
    sumByParent = df.groupby('parentId')['currentVersion'].count()
    for parent in sumByParent.index:
        #Determine wether to put a summary for containers
        filesInParent = df[df['parentId'] == parent]
        if sumByParent[parent] > MAX_FOR_SUMMARY:
            nUpdates = sum(filesInParent.status == 'updated')
            nNew = sum(filesInParent.status == 'new')
            md.write('* ')
            if nUpdates > 1:
                md.write('%i files were updated ' %nUpdates)
            elif nUpdates == 1:
                md.write('%i file was updated ' %nUpdates)
            if nUpdates > 0 and nNew > 0:
                md.write('and ')
            if nNew > 1:
                md.write('%i new files were added ' % nNew)
            elif nNew == 1:
                md.write('%i new file was added ' % nNew)
            md.write('to [%s](#!Synapse:%s)\n' % (get_parent_name(syn, parent), parent))
        else:
            for id, row in filesInParent.iterrows():
                userName = syn.getUserProfile(row['modifiedBy']).userName
                userLink = '[%s](https://www.synapse.org/#!Profile:%s' %(userName, row['modifiedBy'])

                if row.status=='new':
                    md.write('* [%s](#!Synapse:%s) was added by %s)\n' %
                             (row['name'].replace('_', '\_'), id, userLink))
                else:
                    md.write('* [%s](#!Synapse:%s) was updated to version %i by %s)\n' %
                             (row['name'].replace('_', '\_'), id, 
                              row['currentVersion'], userLink))


def update_wiki(syn, owner, wikiId, md):
    """Fetches and existing wiki and overwrites the content. """
    wiki = syn.getWiki(owner, wikiId)
    wiki.markdown = md.getvalue()
    return syn.store(wiki)


def main(syn, project_id, delta_time, earliest_time, wiki):
    """
    """
    project = syn.get(project_id)
    if not isinstance(project, synapseclient.Project):
        raise ValueError(f"{project_id} must be a Synapse Project")
    view = monitor.create_file_view(syn, project_id)

    earliest_time = dateutil.parser.parse(earliest_time)
    today = datetime.datetime.today()
    if delta_time == 'week':
        t = today - datetime.timedelta(days=today.weekday()-7)
    elif delta_time == 'month':
        year, month = divmod(today.month+1, 12)
        year, month = (year+1, 12) if month == 0 else (year, month)
        t = datetime.datetime(today.year + year, month, 1)
    md = StringIO()
    while t > earliest_time:
        if delta_time == 'week':
            tStart = t - datetime.timedelta(days=7)
            headerText = '##week of {}\n'.format(tStart.strftime('%d-%B-%Y'))
        else:
            year, month= divmod(t.month-1, 12)
            year, month = (year-1, 12) if month == 0 else (year, month)
            tStart = datetime.datetime(t.year + year, month, 1)
            headerText = '##{}\n'.format(tStart.strftime('%B-%Y'))
        print(f'{tStart} -> {t}')
        df = get_changes(syn, tStart, t, view.id)
        t = tStart
        if df.empty:
            continue
        print(df.shape)
        # Write the output
        md.write(headerText)
        print_updates(syn, md, df)
    wiki = update_wiki(syn, project_id, wiki, md)
    md.close()
