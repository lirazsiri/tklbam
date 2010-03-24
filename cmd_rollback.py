#!/usr/bin/python
"""
Rollback last restore
"""

import sys
import getopt

def fatal(e):
    print >> sys.stderr, "error: " + str(e)
    sys.exit(1)

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s" % sys.argv[0]
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h', 
                                       ['help'])
                                        
    except getopt.GetoptError, e:
        usage(e)

    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()

    if args:
        usage()

import os
import stat
from changes import Changes
from restore import Rollback, remove_any
from dirindex import DirIndex

def test():
    rollback = Rollback()
    
    changes = Changes.fromfile(rollback.fsdelta)
    dirindex = DirIndex(rollback.dirindex)

    for change in changes:
        if change.OP == 'o':
            print "removing overwritten " + change.path
            remove_any(change.path)

        if change.path not in dirindex:
            continue

        if change.OP in ('o', 'd'):
            print "restoring from originals: " + change.path
            rollback.originals.move_out(change.path)

        dirindex_rec = dirindex[change.path]
        local_rec = DirIndex.Record.frompath(change.path)

        if dirindex_rec.uid != local_rec.uid or \
           dirindex_rec.gid != local_rec.gid:
            print "chown %d:%d %s" % (dirindex_rec.uid, dirindex_rec.gid, change.path)
            os.lchown(change.path, dirindex_rec.uid, dirindex_rec.gid)

        if dirindex_rec.mod != local_rec.mod:
            mod = stat.S_IMODE(dirindex_rec.mod)
            print "chmod %s %s" % (oct(mod), change.path)
            os.chmod(change.path, mod)

    # delete empty directories

if __name__=="__main__":
    test()
