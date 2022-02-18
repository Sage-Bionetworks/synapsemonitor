#!/usr/bin/env python
"""Command line client"""
import argparse
import logging
import json
import os
import sys

import pandas as pd
import synapseclient
from synapseclient.core.exceptions import (
    SynapseAuthenticationError,
    SynapseNoCredentialsError,
)

from . import actions, monitor


def monitor_cli(syn, args):
    """Monitor cli"""

    email_action = actions.EmailAction(
        syn=syn,
        syn_id=args.synapse_id,
        email_subject=args.email_subject,
        users=args.users,
        days=args.days,
    )
    action_results = actions.synapse_action(action_cls=email_action)
    ids = pd.DataFrame({"syn_id": action_results})
    if args.output:
        pd.DataFrame(ids).to_csv(args.output, index=False, header=False)
    else:
        sys.stdout.write(pd.DataFrame(ids).to_csv(index=False, header=False))


def create_file_view_cli(syn, args):
    """Create file view cli"""
    fileview = monitor.create_file_view(
        syn, name=args.name, project_id=args.project_id, scope_ids=args.scope_ids
    )

    logging.info(f"Synapse ID of new file view = {fileview['id']}")


def build_parser():
    """Set up argument parser and returns"""
    parser = argparse.ArgumentParser(
        description="Checks for new or modified Synapse entities. "
        "If a Project or Folder entity is specified, all File entity descendants will be monitored. "
        "Users can create a Synapse File View to track the contents of Projects "
        "or Folders with many file entities more efficiently. You can use the "
        "`create` function provided in this package to create a File View."
    )
    parser.add_argument(
        "-c",
        "--synapse_config",
        metavar="file",
        type=str,
        default=synapseclient.client.CONFIG_FILE,
        help="Synapse config file with user credentials: (default %(default)s)",
    )
    parser.add_argument(
        "--log",
        "-l",
        type=str,
        choices=["debug", "info", "warning", "error"],
        default="error",
        help="Set logging output level " "(default: %(default)s)",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        description="The following commands are available:",
        help='For additional help: "synapsemonitor <COMMAND> -h"',
    )
    parser_monitor = subparsers.add_parser(
        "monitor", help="Find new or modified File entities."
    )
    parser_monitor.add_argument(
        "synapse_id",
        metavar="synapse_id",
        type=str,
        help="Synapse ID of entity to be monitored.",
    )
    parser_monitor.add_argument(
        "--users",
        "-u",
        nargs="+",
        help="User Id or username of individuals to send report. "
        "If not specified, defaults to logged in Synapse user.",
    )
    parser_monitor.add_argument(
        "--output",
        "-o",
        help="Output modified entities into this csv file. (default: None)",
    )
    parser_monitor.add_argument(
        "--email_subject",
        "-e",
        default="New Synapse Files",
        help="Sets the subject heading of the email sent out. (default: %(default)s)",
    )
    parser_monitor.add_argument(
        "--days",
        "-d",
        metavar="days",
        type=int,
        default=1,
        help="Find modifications to File entities in the last N days. "
        "(default: %(default)s)",
    )
    parser_monitor.set_defaults(func=monitor_cli)

    parser_create_view = subparsers.add_parser(
        "create",
        help="Creates a File View that will list all the File entities under "
        "the specified scopes (Synapse Folders or Projects). This will "
        "allow you to query for the files contained in your specified "
        "scopes. This will NOT track the other entities currently: "
        "PROJECT, TABLE, FOLDER, VIEW, DOCKER.",
    )
    parser_create_view.add_argument(
        "name", metavar="NAME", type=str, help="File View name"
    )
    parser_create_view.add_argument(
        "project_id", help="Synapse Project Id to store file view in"
    )
    parser_create_view.add_argument(
        "--scope_ids", nargs="+", required=True, help="Synapse Folder / Project Ids"
    )
    parser_create_view.set_defaults(func=create_file_view_cli)

    return parser


def synapse_login(synapse_config=synapseclient.client.CONFIG_FILE):
    """Login to Synapse.  Looks first for secrets.

    Args:
        synapse_config: Path to synapse configuration file.
                        Defaults to ~/.synapseConfig

    Returns:
        Synapse connection
    """
    try:
        syn = synapseclient.Synapse(skip_checks=True, configPath=synapse_config)
        if os.getenv("SCHEDULED_JOB_SECRETS") is not None:
            secrets = json.loads(os.getenv("SCHEDULED_JOB_SECRETS"))
            syn.login(silent=True, authToken=secrets["SYNAPSE_AUTH_TOKEN"])
        else:
            syn.login(silent=True)
    except (SynapseNoCredentialsError, SynapseAuthenticationError):
        raise ValueError(
            "Login error: please make sure you have correctly "
            "configured your client."
        )
    return syn


def main():
    """Invoke"""
    args = build_parser().parse_args()

    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % args.log)
    logging.basicConfig(level=numeric_level)

    syn = synapse_login(synapse_config=args.synapse_config)
    args.func(syn, args)


if __name__ == "__main__":
    main()
