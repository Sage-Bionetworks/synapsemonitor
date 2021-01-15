#!/usr/bin/env python
"""Command line client"""
import argparse

import synapseclient

from . import monitor


def monitor_cli(syn, args):
    filesdf = monitor.monitoring(
        syn, args.synid, userid=args.userid,
        email_subject=args.email_subject,
        days=args.days,
        use_last_audit_time=args.use_last_audit_time
    )
    if args.output:
        filesdf.to_csv(args.output, index=False)
    else:
        print(filesdf.to_csv(index=False))


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
        'project_or_view',
        help='Monitor a Synapse Project or Fileview.'
    )

    parser_monitor.add_argument(
        'synid', metavar='id', type=str,
        help='Synapse ID of project or fileview to be monitored.'
    )
    parser_monitor.add_argument(
        '--userid',
        help='User Id of individual to send report, defaults to current user.'
    )
    parser_monitor.add_argument(
        '--output',
        help='Output modified entities into this csv file.'
    )
    parser_monitor.add_argument(
        '--email_subject',
        default='New Synapse Files',
        help='Sets the subject heading of the email sent out '
             '(defaults to New Synapse Files)'
    )
    group = parser_monitor.add_mutually_exclusive_group()
    group.add_argument(
        '--days', '-d', metavar='days', type=float, default=None,
        help='Find modifications in the last days'
    )
    group.add_argument(
        '--use_last_audit_time', action='store_true',
        help='Use the last audit time. This value is stored'
             'as an annotation on the file view.'
             '(Default to False)'
    )
    parser_monitor.set_defaults(func=monitor_cli)

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
