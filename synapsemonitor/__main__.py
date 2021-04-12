#!/usr/bin/env python
"""Command line client"""
import argparse

import synapseclient

from . import monitor, update_activity_feed


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


def create_view_changelog_cli(syn, args):
    """Update activity cli"""
    markdown = update_activity_feed.create_view_changelog(
        syn=syn, view_id=args.view_id,
        delta_time=args.interval,
        earliest_time=args.earliest_time,
    )
    if args.project_id is not None:
        update_activity_feed.update_wiki(
            syn=syn, project_id=args.project_id, markdown=markdown,
            wiki_id=args.wiki_id
        )
    if args.markdown_path is not None:
        with open(args.markdown_path, "w") as markdown_f:
            markdown_f.write(markdown)



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

    parser_update = subparsers.add_parser(
        'create-view-changelog',
        help='Looks for changes to a fileview in defined time ranges and '
             'has the option of writing to a Synapse wiki page and writing '
             'to a markdown file.'
    )
    parser_update.add_argument(
        'view_id', help='Synapse ID of fileview.'
    )
    parser_update.add_argument(
        '--project_id', '-p', type=str,
        help='If specified, will store changelog to '
             'homepage of Synapse project'
    )
    parser_update.add_argument(
        '--wiki_id', '-w', type=str,
        help='Optional sub-wiki id where to store change-log '
             '(defaults to project wiki)'
    )
    parser_update.add_argument(
        '--markdown_path', type=str,
        help='If specified, will write changelog to a markdown file'
    )

    parser_update.add_argument(
        '-i', '--interval',
        choices=['week', 'month'], default='week',
        help='divide changesets into either "week" or "month" long intervals '
             '(default: %(default)s)'
    )
    parser_update.add_argument(
        '--earliest', '-e', metavar='date', dest='earliest_time',
        type=str, default='1-Jan-2014',
        help='The start date for which changes will be searched '
             '(default: %(default)s)'
    )
    parser_update.set_defaults(func=create_view_changelog_cli)

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
