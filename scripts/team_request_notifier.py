#!/usr/bin/env python
"""
# TODO: This is an old script that needs to be rewritten and maybe added to the
functionality
"""
import synapseclient
import argparse
import os

def composeMessage(allRequests):
    """Composes a of the list of requests and returs a string."""
    
    message=''
    for teamId, requests in allRequests.items():
        teamName = syn.restGET('/team/%s' %teamId)['name']
        teamURL = 'https://www.synapse.org/#!Team:%s' %teamId


        message += '<h4><a href="%s">%s</a> has %i pending request(s)</h4>\n' %(teamURL, teamName, len(requests))
    return message


def filterRequests(allRequests):
    """Filters out all teams that have no requests
    Arguments:
    - `allRequests`: dict with teamId keys and list of requests as values
    """
    



def build_parser():
    """Set up argument parser and returns"""
    parser = argparse.ArgumentParser(
        description='Checks for new requests to multiple teams')
    parser.add_argument('teams', metavar='id', type=str, nargs='*',
                        help='A list of teams to monitor for changes.')
    parser.add_argument('--userId', dest='userId',
                        help='User Id of individual to send report, defaults to current user.')
    parser.add_argument('--config', metavar='file', dest='configPath',  type=str,
            help='Synapse config file with user credentials (overides default ~/.synapseConfig)')
    return parser


#p = mp.Pool(6)
args = build_parser().parse_args()
if args.configPath is not None:
    syn=synapseclient.Synapse(skip_checks=True, configPath=args.configPath)
else:
    syn=synapseclient.Synapse(skip_checks=True)
syn.login(silent=True) 
args.userId = syn.getUserProfile()['ownerId'] if args.userId is None else args.userId

allRequests = {team: syn.restGET('/team/%s/openRequest' % team)['results'] for team in args.teams}
allRequests = {key:item for (key, item) in allRequests.items() if len(item)>0}  #Filter out empty team requests

message = composeMessage(allRequests)

#Whoa, this is a bad idea for multiple concurrently running processes.
oldMessage = ''
if os.path.exists('.last_teamRequestNotifier_message'):
    with open('.last_teamRequestNotifier_message', "r+") as fp:
        oldMessage = fp.read()

with open('.last_teamRequestNotifier_message', "w") as fp:
    fp.write(message)

if oldMessage != message:
    print 'sending message'
    syn.sendMessage([args.userId], 'New Team requests', message, contentType = 'text/html')
else: 
    print 'Not sending message'


