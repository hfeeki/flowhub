#!/usr/bin/env python
import argparse

from engine import Engine


__version__ = "0.3.1"


def handle_init_call(args, engine):
    if args.verbosity > 2:
        print "handling init"

    engine.setup_repository_structure()


def handle_feature_call(args, engine):
    if args.verbosity > 2:
        print "handling feature"
    if args.action == 'start':
        if args.issue_number:
            args.name = "{}-{}".format(args.issue_number, args.name)
        engine.create_feature(
            name=args.name,
            create_tracking_branch=(not args.no_track),
        )

    elif args.action == 'work':
        engine.work_feature(name=args.name)

    elif args.action == 'publish':
        try:
            engine.publish_feature(name=args.name)
        except AssertionError:
            # This is janky as shit, but running twice fixes it.
            # see #14
            engine.publish_feature(name=args.name)
    elif args.action == 'abandon':
        engine.abandon_feature(
            name=args.name,
        )

    elif args.action == 'accepted':
        try:
            engine.accept_feature(
                name=args.name,
            )
        except AssertionError:
            # see #14
            engine.accept_feature(
                name=args.name,
            )
    elif args.action == 'list':
        engine.list_features()
    else:
        raise RuntimeError("Unimplemented command for features: {}".format(args.action))


def handle_hotfix_call(args, engine):
    if args.verbosity > 2:
        print "handling hotfix"

    if args.action == 'start':
        engine.start_hotfix(
            name=args.name,
            issues=args.issue_numbers,
        )
    elif args.action == 'publish':
        engine.publish_hotfix(
            name=args.name,
        )
    elif args.action == 'contribute':
        engine.contribute_hotfix()
    else:
        raise RuntimeError("Unimplemented command for hotfixes: {}".format(args.action))


def handle_release_call(args, engine):
    if args.verbosity > 2:
        print "handling release"

    if args.action == 'start':
        engine.start_release(
            name=args.name,
        )
    elif args.action == 'publish':
        engine.publish_release(
            name=args.name,
            delete_release_branch=(not args.no_cleanup),
        )
    elif args.action == 'contribute':
        engine.contribute_release()
    else:
        raise RuntimeError("Unimplemented command for releases: {}".format(args.action))


def handle_cleanup_call(args, engine):
    if args.verbosity > 2:
        print "handling cleanup"

    # Get the targets for cleanup
    targets = ''
    if args.t or args.all:
        if args.verbosity > 2:
            print "adding 't' to targets"
        targets += 't'
    if args.u or args.all:
        if args.verbosity > 2:
            print "adding 'u' to targets"
        targets += 'u'
    if args.r or args.all:
        if args.verbosity > 2:
            print "adding 'r' to targets"
        targets += 'r'

    if targets:
        engine.cleanup_branches(targets=targets)
    else:
        print "No targets specified for cleanup."


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbosity', action="store", type=int, default=0)
    parser.add_argument('--no-gh', action='store_true', default=False,
        help='do not talk to GitHub',)
    parser.add_argument('--version', action='version',
        version=('flowhub v{}'.format(__version__)))

    subparsers = parser.add_subparsers(dest="subparser")
    init = subparsers.add_parser('init',
        help="set up a repository to use flowhub",)
    feature = subparsers.add_parser('feature',
        help="do feature-related things",)
    hotfix = subparsers.add_parser('hotfix',
        help="do hotfix-related things",)
    release = subparsers.add_parser('release',
        help="do release-related things",)
    cleanup = subparsers.add_parser('cleanup',
        help="do repository-cleanup related things.",)

    #
    # Features
    #
    feature_subs = feature.add_subparsers(dest='action')

    fstart = feature_subs.add_parser('start',
        help="start a new feature branch")
    fstart.add_argument('name', help="name of the feature")
    fstart.add_argument('--no-track', default=False, action='store_true',
        help="do *not* set up a tracking branch on origin.")
    fstart.add_argument('-i', '--issue-number', type=int,
        action='store', default=None,
        help="prepend an issue number to the feature name")

    fwork = feature_subs.add_parser('work',
        help="switch to a different feature (by name)")
    fwork.add_argument('name', help="name of feature to switch to")

    fpublish = feature_subs.add_parser('publish',
        help="send the current feature branch to origin and create a pull-request")
    fpublish.add_argument('name', nargs='?',
        default=None,
        help='name of feature to publish. If not given, uses current feature')

    fabandon = feature_subs.add_parser('abandon',
        help="remove a feature branch completely"
    )
    fabandon.add_argument('name', nargs='?',
        default=None,
        help="name of the feature to abandon. If not given, uses current feature")
    faccepted = feature_subs.add_parser('accepted',
        help="declare that a feature was accepted into the trunk")
    faccepted.add_argument('name', nargs='?',
        default=None,
        help="name of the accepted feature. If not given, assumes current feature")
    flist = feature_subs.add_parser('list',
        help='list the feature names on this repository')

    #
    # Hotfixes
    #
    hotfix_subs = hotfix.add_subparsers(dest='action')

    hstart = hotfix_subs.add_parser('start',
        help="start a new hotfix branch")
    hstart.add_argument('name',
        help="name (and tag) for the hotfix")
    hstart.add_argument('--issue-numbers', '-i', type=int,
        default=None, nargs='+',
        help="specifies the issues this hotfix addresses")
    hpublish = hotfix_subs.add_parser('publish',
        help="publish the hotfix to production and trunk")
    hpublish.add_argument('name', nargs='?',
        help="name of hotfix to publish. If not given, uses current branch.")
    hcontribute = hotfix_subs.add_parser('contribute',
        help='send this branch as a pull request to the current hotfix')
    #
    # Releases
    #
    release_subs = release.add_subparsers(dest='action')

    rstart = release_subs.add_parser('start',
        help="start a new release branch")
    rstart.add_argument('name', help="name (and tag) of the release branch.")

    rstage = release_subs.add_parser('stage',
        help="send a release branch to a staging environment")

    rpublish = release_subs.add_parser('publish',
        help="publish a release branch to production and trunk")
    rpublish.add_argument('name', nargs='?',
        help="name of release to publish. if not specified, current branch is assumed.")
    rpublish.add_argument('--no-cleanup', action='store_true',
        default=False,
        help="do not delete the release branch after a successful publish",
    )
    rcontribute = release_subs.add_parser('contribute')

    rabandon = release_subs.add_parser('abandon',
        help='abort a release branch')
    rabandon.add_argument('name', nargs='?',
        help='name of release to abandon. if not specified, current branch is assumed.')
    #
    # Cleanup
    #
    cleanup.add_argument('-u', action='store_true',
        help='do cleanup features.', default=False)
    cleanup.add_argument('-r', action='store_true',
        help='do cleanup releases.', default=False)
    cleanup.add_argument('-t', action='store_true',
        help='do cleanup hotfixes.', default=False)
    cleanup.add_argument('-a', '--all', action='store_true', default=False,
        help='Shorthand for using the flag -urt')

    args = parser.parse_args()
    if args.verbosity > 2:
        print "Args: ", args

    e = Engine(debug=args.verbosity, skip_auth=args.no_gh)

    if args.subparser == 'feature':
        handle_feature_call(args, e)

    elif args.subparser == 'hotfix':
        handle_hotfix_call(args, e)

    elif args.subparser == 'release':
        handle_release_call(args, e)

    elif args.subparser == 'cleanup':
        handle_cleanup_call(args, e)

    elif args.subparser == 'init':
        handle_init_call(args, e)

    else:
        raise RuntimeError("Unrecognized command: {}".format(args.subparser))

if __name__ == "__main__":
    run()
