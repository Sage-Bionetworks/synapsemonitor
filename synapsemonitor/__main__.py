#!/usr/bin/env python
"""Command line client"""
import argparse

from . import monitor


def build_parser():
    """Set up argument parser and returns"""
    parser = argparse.ArgumentParser(
        description='Checks for new/modified entities in a project.'
    )
    parser.add_argument(
        'projectid', metavar='projectid', type=str,
        help='Synapse ID of project to be monitored.'
    )
    parser.add_argument(
        '--userid',
        help='User Id of individual to send report, defaults to current user.'
    )
    parser.add_argument(
        '--email-subject', dest='email_subject',
        default = 'New Synapse Files',
        help='Sets the subject heading of the email sent out '
             '(defaults to New Synapse Files)'
    )
    parser.add_argument(
        '--synapseconfig', metavar='file', type=str,
        help='Synapse config file with user credentials '
             '(overrides default ~/.synapseConfig)'
    )
    return parser


def main():
    """Invoke"""
    args = build_parser().parse_args()
    # func has to match the set_defaults
    # monitor.monitoring(args.projectid, synapseconfig=args.synapseconfig,
    #                    userid=args.userid, email_subject=args.email_subject)


if __name__ == "__main__":
    main()
