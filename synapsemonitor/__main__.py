#!/usr/bin/env python
"""Command line client"""
import argparse

import synapseclient
from synapseclient.core.exceptions import (
    SynapseAuthenticationError,
    SynapseNoCredentialsError,
)

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


def create_file_view_cli(syn, args):
    """Create file view cli"""
    fileview = monitor.create_file_view(
        syn, name=args.name, project_id=args.project_id,
        scope_ids=args.scope_ids
    )
    print("To monitor the files in your specified scope, "
          "you can run the command line function:")
    print(f"$ synapsemonitor view {fileview.id} --days 4")


def build_parser():
    """Set up argument parser and returns"""
    parser = argparse.ArgumentParser(
        description='Checks for new/modified entities in a Fileview.'
                    'A Synapse Fileview can be created to allow users to '
                    'track entities in a Project or Folder.  For more '
                    'information, head to '
                    'https://docs.synapse.org/articles/views.html. '
                    'You can use the `create-file-view` function provided '
                    'in this package to create a File View.'
    )
    parser.add_argument(
        '-c', '--synapse_config', metavar='file', type=str,
        default=synapseclient.client.CONFIG_FILE,
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

    parser_create_view = subparsers.add_parser(
        'create-file-view',
        help='Creates a file view that will list all the File entities under '
             'the specified scopes (Synapse Folders or Projects). This will '
             'allow you to query for the files contained in your specified '
             'scopes. This will NOT track the other entities currently: '
             'PROJECT, TABLE, FOLDER, VIEW, DOCKER.'
    )
    parser_create_view.add_argument(
        'name', metavar='NAME', type=str,
        help='File View name'
    )
    parser_create_view.add_argument(
        'project_id',
        help='Synapse Project Id to store file view in'
    )
    parser_create_view.add_argument(
        '--scope_ids', nargs='+', required=True,
        help='Synapse Folder / Project Ids'
    )
    parser_create_view.set_defaults(func=create_file_view_cli)

    return parser


def synapse_login(synapse_config=synapseclient.client.CONFIG_FILE):
    """Login to Synapse

    Args:
        synapse_config: Path to synapse configuration file.
                        Defaults to ~/.synapseConfig

    Returns:
        Synapse connection
    """
    try:
        syn = synapseclient.Synapse(skip_checks=True,
                                    configPath=synapse_config)
        syn.login(silent=True)
    except (SynapseNoCredentialsError, SynapseAuthenticationError):
        raise ValueError(
            "Login error: please make sure you have correctly "
            "configured your client.  Instructions here: "
            "https://help.synapse.org/docs/Client-Configuration.1985446156.html. "
            "You can also create a Synapse Personal Access Token and set it "
            "as an environmental variable: "
            "SYNAPSE_AUTH_TOKEN='<my_personal_access_token>'"
        )
    return syn


def main():
    """Invoke"""
    args = build_parser().parse_args()
    syn = synapse_login(synapse_config=args.synapse_config)
    args.func(syn, args)


if __name__ == "__main__":
    main()
