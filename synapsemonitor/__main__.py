#!/usr/bin/env python
"""Command line client"""
import argparse

import synapseclient

from . import monitor


def monitor_cli(syn, args):
    monitor.monitor_project(syn, args.projectid,
                            userid=args.userid,
                            email_subject=args.email_subject,
                            days=args.days,
                            update_project=args.update_project)


def monitor_team_cli(syn, args):
    """Monitor team cli"""
    monitor.monitor_team(syn, args.team,
                         projectid=args.projectid,
                         userid=args.userid)


def build_parser():
    """Set up argument parser and returns"""
    parser = argparse.ArgumentParser(
        description='Checks for new/modified entities in a project.'
    )
    parser.add_argument(
        '-c', '--synapse_config', metavar='file', type=str,
        help='Synapse config file with user credentials '
             '(overrides default ~/.synapseConfig)'
    )

    subparsers = parser.add_subparsers(
        title='commands',
        description='The following commands are available:',
        help='For additional help: "synapsemonitor <COMMAND> -h"'
    )
    parser_monitor = subparsers.add_parser(
        'monitor', help='Monitor a Synapse Project'
    )
    parser_monitor.add_argument(
        'projectid', metavar='projectid', type=str,
        help='Synapse ID of project to be monitored.'
    )
    parser_monitor.add_argument(
        '--userid',
        help='User Id of individual to send report, defaults to current user.'
    )
    parser_monitor.add_argument(
        '--email_subject',
        default='New Synapse Files',
        help='Sets the subject heading of the email sent out '
             '(defaults to New Synapse Files)'
    )
    parser_monitor.add_argument(
        '--days', '-d', metavar='days', type=float, default=None,
        help='Find modifications in the last days'
    )
    parser_monitor.add_argument(
        '--update_project', action='store_true',
        help='If set will modify the annotations by setting '
             'lastAuditTimeStamp to the current time on each project.')
    parser_monitor.set_defaults(func=monitor_cli)

    parser_monitor_team = subparsers.add_parser(
        'team',
        help='Checks for new team members. The first time running this'
             'will assume all members are new.'
    )
    parser_monitor_team.add_argument(
        'team', metavar='id', type=str,
        help='A team to monitor for changes in team requests'
    )
    parser_monitor_team.add_argument(
        '--projectid', required=True,
        help='Synapse ID of project to store team member tracking table'
    )
    parser_monitor_team.add_argument(
        '--userid',
        help='User Id of individual to send report, defaults to current user.'
    )
    parser_monitor_team.set_defaults(func=monitor_team_cli)

    return parser


def synapse_login(synapse_config=None):
    if synapse_config is not None:
        syn = synapseclient.Synapse(skip_checks=True,
                                    configPath=synapse_config)
    else:
        syn = synapseclient.Synapse(skip_checks=True)
    syn.login(silent=True)
    return syn


def main():
    args = build_parser().parse_args()
    syn = synapse_login(synapse_config=args.synapse_config)
    args.func(syn, args)


if __name__ == "__main__":
    main()
