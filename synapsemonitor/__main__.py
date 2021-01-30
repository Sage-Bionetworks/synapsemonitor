#!/usr/bin/env python
"""Command line client"""
import argparse

import synapseclient

from . import monitor


def monitor_cli(syn, args):
    """Monitor cli"""
    filesdf = monitor.monitoring(
        syn, args.view_id, users=args.users,
        email_subject=args.email_subject,
        days=args.days
    )
    if args.output:
        filesdf.to_csv(args.output, index=False)
    else:
        print(filesdf.to_csv(index=False))


def build_parser():
    """Set up argument parser and returns"""
    parser = argparse.ArgumentParser(
        description='Checks for new/modified entities in a Fileview.'
                    'A Synapse Fileview can be created to allow users to '
                    'track entities in a Project or Folder.  For more '
                    'information, head to '
                    'https://docs.synapse.org/articles/views.html'
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
        'view',
        help='Monitor entities tracked in a Synapse Fileview.'
    )
    parser_monitor.add_argument(
        'view_id', metavar='id', type=str,
        help='Synapse ID of fileview to be monitored.'
    )
    parser_monitor.add_argument(
        '--users', nargs='+',
        help='User Id or username of individuals to send report. '
             'If not specified will defaults to logged in Synapse user.'
    )
    parser_monitor.add_argument(
        '--output',
        help='Output modified entities into this csv file.'
    )
    parser_monitor.add_argument(
        '--email_subject',
        default='New Synapse Files',
        help='Sets the subject heading of the email sent out. '
             '(default: %(default)s)'
    )
    parser_monitor.add_argument(
        '--days', '-d', metavar='days', type=int, default=1,
        help='Find modifications to entities in the last N days. '
             '(default: %(default)s)'
    )
    parser_monitor.set_defaults(func=monitor_cli)

    return parser


def synapse_login(synapse_config=None):
    """Synapse login helper"""
    if synapse_config is not None:
        syn = synapseclient.Synapse(skip_checks=True,
                                    configPath=synapse_config)
    else:
        syn = synapseclient.Synapse(skip_checks=True)
    syn.login(silent=True)
    return syn


def main():
    """Invoke"""
    args = build_parser().parse_args()
    syn = synapse_login(synapse_config=args.synapse_config)
    args.func(syn, args)


if __name__ == "__main__":
    main()
