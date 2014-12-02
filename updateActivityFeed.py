#!/usr/bin/env python

import datetime
import StringIO
import time
import argparse
import dateutil.parser
import pandas as pd
import synapseclient

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 
          'August', 'September', 'October', 'November', 'December']
EPOCHSTART = datetime.datetime(1970,1,1)
MAX_FOR_SUMMARY=4

updateQuery = ('select id, name, parentId, modifiedByPrincipalId, versionNumber from file '
               'where benefactorId=="%s" and modifiedOn>%i and modifiedOn<%i '
               'and versionNumber>1')
newQuery =    ('select id, name, parentId, modifiedByPrincipalId, versionNumber from file '
               'where benefactorId=="%s" and modifiedOn>%i and  modifiedOn<%i '
               'and versionNumber==1')

def getChanges(start, end, projectId):
    """Finds entities updated and changed in month numbered month"""
    start = int((start- EPOCHSTART).total_seconds())*1000
    end = int((end - EPOCHSTART).total_seconds())*1000        
    if start > time.time()*1000:
        return pd.DataFrame()
    new = pd.DataFrame(syn.chunkedQuery(newQuery %(projectId, start, end)))
    updated = pd.DataFrame(syn.chunkedQuery(updateQuery %(projectId, start, end)))
    if not new.empty:
        new['status'] = 'new'
        new.set_index('file.id', inplace=True)
    if not updated.empty:
        updated['status'] = 'updated'
        updated.set_index('file.id', inplace=True)
    return pd.concat([new, updated])


@synapseclient.utils.memoize
def getParentName(id):
    """Returns the name of an entity """
    return syn.get(id, downloadFile=False).name
    


def printUpdates(md, df):
    """Writes the summary of the updates in df to md string. """
    sumByParent = df.groupby('file.parentId')['file.versionNumber'].count()
    for parent in sumByParent.index:
        #Determine wether to put a summary for containers
        filesInParent = df[df['file.parentId']==parent]
        if sumByParent[parent] > MAX_FOR_SUMMARY:
            nUpdates = sum(filesInParent.status=='updated')
            nNew = sum(filesInParent.status=='new')
            md.write('* ')
            if nUpdates >1:
                md.write('%i files were updated ' %nUpdates)
            elif nUpdates ==1:
                md.write('%i file was updated ' %nUpdates)
            if nUpdates>0 and nNew >0:
                md.write('and ')
            if nNew >1:
                md.write('%i new files were added ' % nNew)
            elif nNew == 1:
                md.write('%i new file was added ' % nNew)
            md.write('to [%s](#!Synapse:%s)\n' % (getParentName(parent), parent))
        else:
            for id, row in filesInParent.iterrows():
                userName = syn.getUserProfile(row['file.modifiedByPrincipalId']).userName
                userLink = '[%s](https://www.synapse.org/#!Profile:%s' %(userName, row['file.modifiedByPrincipalId'])
                                              
                if row.status=='new':
                    md.write('* [%s](#!Synapse:%s) was added by %s)\n' %
                             (row['file.name'], id, userLink))
                else:
                    md.write('* [%s](#!Synapse:%s) was updated to version %i by %s)\n' %
                             (row['file.name'], id, 
                              row['file.versionNumber'], userLink))
                                 
                             
def updateWiki(owner, wikiId, md):
    """Fetches and existing wiki and overwrites the content. """
    wiki = syn.getWiki(owner, wikiId)
    wiki.markdown = md.getvalue()
    return syn.store(wiki)


def build_parser():
    """
    """
    parser = argparse.ArgumentParser(
        description='Looks for changes to project in defined time ranges and updates a wiki')
    parser.add_argument('project', help='Synapse ID of projects to be monitored.')
    parser.add_argument('--wiki', '-w', metavar='wikiId', type=str, 
            help='Optional sub-wiki id where to store change-log (defaults to project wiki)')
    parser.add_argument('-i', '--interval', metavar='interval', 
            choices=['week', 'month'], default='week',
            help='divide changesets into either "week" or "month" long intervals (default week)')
    parser.add_argument('--earliest', '-e', metavar='date', dest='earliestTime', 
           type=str, default = '1-Jan-2014',
           help='The start date for which changes will be searched (defaults to 1-January-2014)')
    parser.add_argument('--config', metavar='file', dest='configPath',  type=str,
            help='Synapse config file with user credentials (overides default ~/.synapseConfig)')
    return parser


if __name__ == '__main__':
    args = build_parser().parse_args()
    projectId = args.project
    deltaTime = args.interval
    earliestTime = dateutil.parser.parse(args.earliestTime)

    if args.configPath is not None:
        syn=synapseclient.Synapse(skip_checks=True, configPath=args.configPath)
    else:
        syn=synapseclient.Synapse(skip_checks=True)
    syn.login(silent=True) 

    today =  datetime.datetime.today()
    if deltaTime=='week':
        t = today - datetime.timedelta(days=today.weekday()-7)
    elif deltaTime=='month':
        year, month= divmod(today.month+1, 12)
        year, month = (year+1, 12) if month == 0 else (year, month)
        t = datetime.datetime(today.year + year, month, 1)
    md = StringIO.StringIO()
    while t>earliestTime:
        if deltaTime=='week':
            tStart = t-datetime.timedelta(days=7) 
            headerText = '##week of %s\n' %tStart.strftime('%d-%B-%Y')
        else:
            year, month= divmod(t.month-1, 12)
            year, month = (year-1, 12) if month == 0 else (year, month)
            tStart = datetime.datetime(t.year + year, month, 1)
            headerText = '##%s\n' %tStart.strftime('%B-%Y')
        print '%s -> %s' %(tStart, t)
        df = getChanges(tStart, t, projectId)
        t = tStart
        if len(df)==0:
            continue
        print df.shape
        #Write the output
        md.write(headerText)
        printUpdates(md, df)
    wiki = updateWiki(projectId, args.wiki, md)
    md.close()

