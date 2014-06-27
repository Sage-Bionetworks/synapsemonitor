#!/usr/bin/env python

import synapseclient
import calendar
import time
import argparse
import multiprocessing.dummy as mp

nodeTypes = {0:'dataset',1: 'layer',2: 'project',3: 'preview',4: 'folder',5: 'analysis',6: 'step',
             7: 'code',8: 'link',9: 'phenotypedata',10:'genotypedata',11:'expressiondata',12:'robject',
             13:'summary',14:'genomicdata',15:'page',16:'file',17:'table',18:'community'}

ONEDAY=86400000 #default delta t is 10 days prior
syn=synapseclient.Synapse(skip_checks=True)
syn.login(silent=True) 


def findNewFiles(id, lastTime=None):
    """Performs query query to find changed entities in id
    
    Arguments:
    - `id`: A synapse Id
    - `lastTime`: time to check for new files since defaults to lastAuditTimeStamp in project annotation or 10 day
    """
    QUERY = "select id, name, versionNumber, modifiedOn, modifiedByPrincipalId, nodeType from entity where benefactorId=='%s' and modifiedOn>%i" 
    t = calendar.timegm(time.gmtime())*1000
    project = syn.get(id)
    #Determine the last audit time or overide with lastTime
    if lastTime is None:  #No time specified
        lastTime = project.get('lastAuditTimeStamp', None)
        if lastTime is None:  #No time specified and no lastAuditTimeStamp set
            lastTime = t - ONEDAY*1.2
        else: #lastTime came from annotation strip out from list
            lastTime = lastTime[0]  
    print t, lastTime, id, (t-lastTime)/ONEDAY
    results = list(syn.chunkedQuery(QUERY % (id, lastTime)))
    #Add the project and other metadata
    for r in results:
        r['projectId'] = id
        r['projectName'] = project.name
        r['date'] = synapseclient.utils.from_unix_epoch_time(r['entity.modifiedOn']).strftime("%d-%b-%Y %H:%M")
        r['user'] = syn.getUserProfile(r['entity.modifiedByPrincipalId'])['userName']
        r['type'] = nodeTypes[r['entity.nodeType']]
        
    #Set lastAuditTimeStamp
    project.lastAuditTimeStamp = t
    try:
        project = syn.store(project)
    except synapseclient.exceptions.SynapseHTTPError:
        pass
    return results

def composeMessage(entityList):
    """Composes a message with the contents of entityList """
    
    messageHead=('<table border=1><tr>'
                 '<th>Project</th>'
                 '<th>Entity</th>'
                 '<th>Ver.</th>'
                 '<th>Type</th>'
                 '<th>Change Time</th>'
                 '<th>Contributor</th></tr>')
    lines = [('<tr><td><a href="https://www.synapse.org/#!Synapse:%(projectId)s">%(projectName)s</a></td>'
              '<td><a href="https://www.synapse.org/#!Synapse:%(entity.id)s">(%(entity.id)s)</a> %(entity.name)s </td>'
              '<td>%(entity.versionNumber)s</td>'
              '<td>%(type)s</td>'
              '<td>%(date)s</td>'
              '<td><a href="https://www.synapse.org/#!Profile:%(entity.modifiedByPrincipalId)s">%(user)s</a></td></tr>')%item for 
             item in entityList]
    return messageHead + '\n'.join(lines)+'</table></body>'


def build_parser():
    """Set up argument parser and returns"""
    parser = argparse.ArgumentParser(
        description='Checks for new/modified entities in a project.')
    parser.add_argument('--userId', dest='userId',
                        help='User Id of individual to send report, defaults to current user.')
    parser.add_argument('--projects', '-p', metavar='projects', type=str, nargs='*',
            help='Synapse IDs of projects to be monitored.')
    parser.add_argument('--days', '-d', metavar='days', type=int, default=None,
            help='Find modifications in the last days')
    return parser


if __name__ == '__main__':
    p = mp.Pool(6)
    args = build_parser().parse_args()
    args.userId = syn.getUserProfile()['ownerId'] if args.userId is None else args.userId
    args.days = None if args.days is None else calendar.timegm(time.gmtime())*1000 - args.days*ONEDAY

    print args.days

    #query each project then combine into long list
    entityList = p.map(lambda project: findNewFiles(project, args.days), args.projects)
    entityList = [item for sublist in entityList for item in sublist]
    #Filter out projects and folders
    entityList = [e for e in entityList if e['entity.nodeType'] not in [2, 4]]


    #Prepare and send Message
    syn.sendMessage([args.userId], 
                    'New TCGA files at: %s' %time.ctime(),
                    composeMessage(entityList),
                    contentType = 'text/html')



    # projects=['syn300013',  #Pancan
    #           'syn1725886', # TCGA Gastric Data Snapshot
    #           'syn2344890', # TCGA_Cervical_AWG
    #           'syn2344108', # TCGA_KIRP_AWG
    #           'syn2480680', # TCGA_PCPG_AWG
    #           'syn2024473', # TCGA_SKCM_AWG
    #           'syn1960986', # TCGA thyroid
    #           'syn2426653', # TCGA FFPE
    #           'syn1935546', # TCGA kidney chromophobe
    #           'syn2296810', # TCGA prostate
    #           'syn2284679', # TCGA ACC
    #           'syn2289118', # TCGA Uterine CS
    #           'syn1973664', # TCGA LGG
    #           'syn2318326'] # TCGA liver
