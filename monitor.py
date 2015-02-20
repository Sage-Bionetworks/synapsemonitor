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


def findNewFiles(args, id):
    """Performs query query to find changed entities in id. """

    QUERY = "select id, name, versionNumber, modifiedOn, modifiedByPrincipalId, nodeType from entity where projectId=='%s' and modifiedOn>%i" 
    t = calendar.timegm(time.gmtime())*1000
    project = syn.get(id)
    #Determine the last audit time or overide with lastTime
    if args.days is None:  #No time specified
        args.days = project.get('lastAuditTimeStamp', None)
        if args.days is None:  #No time specified and no lastAuditTimeStamp set
            args.days = t - ONEDAY*1.1
        else: #args.days came from annotation strip out from list
            args.days = args.days[0]  
    print t, args.days, id, (t-args.days)/float(ONEDAY), 'days'
    results = list(syn.chunkedQuery(QUERY % (id, args.days)))
    #Add the project and other metadata
    for r in results:
        r['projectId'] = id
        r['projectName'] = project.name
        r['date'] = synapseclient.utils.from_unix_epoch_time(r['entity.modifiedOn']).strftime("%b/%d/%Y %H:%M")
        r['user'] = syn.getUserProfile(r['entity.modifiedByPrincipalId'])['userName']
        r['type'] = nodeTypes[r['entity.nodeType']]
        
    #Set lastAuditTimeStamp
    if args.updateProject:
        project.lastAuditTimeStamp = t
        try:
            project = syn.store(project)
        except synapseclient.exceptions.SynapseHTTPError:
            pass
    return results

def composeMessage(entityList):
    """Composes a message with the contents of entityList """
    
    messageHead=('<h4>Time of Audit: %s </h4>'%time.ctime() +
                 '<table border=1><tr>'
                 '<th>Project</th>'
                 '<th>Entity</th>'
                 '<th>Ver.</th>'
                 '<th>Type</th>'
                 '<th>Change Time</th>'
                 '<th>Contributor</th></tr>'  )
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
    parser.add_argument('--days', '-d', metavar='days', type=float, default=None,
            help='Find modifications in the last days')
    parser.add_argument('--updateProject', dest='updateProject',  action='store_true',
            help='If set will modify the annotations by setting lastAuditTimeStamp to the current time on each project.')
    parser.add_argument('--emailSubject', dest='emailSubject',  default = 'Updated Synapse Files',
            help='Sets the subject heading of the email sent out (defaults to Updated Synapse Files')
    parser.add_argument('--config', metavar='file', dest='configPath',  type=str,
            help='Synapse config file with user credentials (overides default ~/.synapseConfig)')
    return parser


p = mp.Pool(6)
args = build_parser().parse_args()
args.days = None if args.days is None else calendar.timegm(time.gmtime())*1000 - args.days*ONEDAY
if args.configPath is not None:
    syn=synapseclient.Synapse(skip_checks=True, configPath=args.configPath)
else:
    syn=synapseclient.Synapse(skip_checks=True)
syn.login(silent=True) 
args.userId = syn.getUserProfile()['ownerId'] if args.userId is None else args.userId


#query each project then combine into long list
entityList = p.map(lambda project: findNewFiles(args, project), args.projects)
entityList = [item for sublist in entityList for item in sublist]
#Filter out projects and folders
entityList = [e for e in entityList if e['entity.nodeType'] not in [2, 4]]
print 'Total number of entities = ', len(entityList)

#Prepare and send Message
syn.sendMessage([args.userId], 
                args.emailSubject, 
                composeMessage(entityList),
                contentType = 'text/html')



