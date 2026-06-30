"""
Clear out the workspace to start a fresh volume.

Recursively deletes every (non-hidden) file in workspace/in and workspace/out,
including their bak/ and temp/ subfolders. The folder structure is left in place;
hidden files (e.g. .DS_Store) are left alone.

This is destructive and cannot be undone. Back up anything you need (the originals
in workspace/in/bak included) before running. To reset for a *re-run* of the same
volume instead -- restoring the originals from bak and reconverting -- use
insert_milestones.py -c, not this script.

Usage:
    python clear_all.py                # prompts for confirmation
    python clear_all.py -y             # skip the confirmation prompt
    python clear_all.py --workspace /some/other/workspace
"""
import argparse
import os
from os import listdir, remove
from os.path import join, exists, isfile, isdir, dirname, abspath

# Default to the workspace next to this script, so it works regardless of cwd.
DEFAULT_WORKSPACE = join(dirname(abspath(__file__)), 'workspace')


def delete_files_in(dirpath, recurse=False):
    '''
    Remove the (non-hidden) files in dirpath. If recurse is True, also remove files in its subfolders.
    Missing folders are silently skipped.
    :param dirpath: str
    :param recurse: bool
    :return: int Count of files removed
    '''
    if not exists(dirpath):
        return 0
    count = 0
    for f in listdir(dirpath):
        fpath = join(dirpath, f)
        if isfile(fpath):
            if not f.startswith('.'):
                remove(fpath)
                count += 1
        elif recurse and isdir(fpath):
            count += delete_files_in(fpath, recurse=True)
    return count


def clear_all(workspace, assume_yes=False):
    '''
    Delete all non-hidden files in workspace/in and workspace/out (including bak and temp).
    :param workspace: str path to the workspace folder
    :param assume_yes: bool skip the confirmation prompt
    :return: int Count of files removed (0 if aborted)
    '''
    indir = join(workspace, 'in')
    outdir = join(workspace, 'out')

    if not exists(indir) and not exists(outdir):
        print("Neither {} nor {} exists; nothing to clear.".format(indir, outdir))
        return 0

    if not assume_yes:
        resp = input("Are you sure you want to DELETE ALL files in {} and {}, \n"
                     "including their bak and temp folders? This cannot be undone (Y/n)? ".format(indir, outdir))
        if resp != 'Y':
            print("Aborted.")
            return 0

    removed = delete_files_in(indir, recurse=True) + delete_files_in(outdir, recurse=True)
    print("Cleared {} file(s) from {} and {}.".format(removed, indir, outdir))
    return removed


def main():
    parser = argparse.ArgumentParser(description="Clear all files from workspace/in and workspace/out to start a fresh volume.")
    parser.add_argument('-w', '--workspace', default=DEFAULT_WORKSPACE,
                        help='Path to the workspace folder (default: the workspace next to this script)')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Skip the confirmation prompt')
    args = parser.parse_args()
    clear_all(args.workspace, assume_yes=args.yes)


if __name__ == "__main__":
    main()
