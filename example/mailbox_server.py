#!/usr/bin/env python
"""Demo server providing a set of PVs which do nothing except store a value.

For fun, allow type change via an RPC.


   $ python example/mailbox_server.py foo

In another shell

   $ pvinfo foo
   $ eget -s foo -a help
   $ eget -s foo -a newtype=str
   $ pvinfo foo
"""

from __future__ import print_function

import time, logging

from p4p.nt import NTScalar
from p4p.server import Server, StaticProvider
from p4p.server.thread import SharedPV

help_type = NTScalar('s')
types = {
    'int':NTScalar('i').wrap(0),
    'float':NTScalar('d').wrap(0.0),
    'str':NTScalar('s').wrap(''),
}

class MailboxHandler(object):
    type = None
    def rpc(self, pv, op):
        V = op.value()
        print("RPC", V, V.query.get('help'), V.query.get('newtype'))
        if V.query.get('help') is not None:
            op.done(help_type.wrap('Try newtype=int (or float or str)'))
            return

        newtype = types[V.query.newtype]

        op.done(help_type.wrap('Success'))

        pv.close() # disconnect client
        pv.open(newtype)

    def put(self, pv, op):
        print("X", op.value())
        pv.post(op.value())
        op.done()

def getargs():
    from argparse import ArgumentParser
    P = ArgumentParser()
    P.add_argument('name', nargs='+')
    P.add_argument('-v','--verbose', action='store_const', default=logging.INFO, const=logging.DEBUG)
    return P.parse_args()

def main(args):
    provider = StaticProvider('mailbox') # 'mailbox' is an arbitrary name

    pvs = [] # we must keep a reference in order to keep the Handler from being collected
    for name in args.name:
        pv = SharedPV(initial=types['int'], handler=MailboxHandler())

        provider.add(name, pv)
        pvs.append(pv)

    with Server(providers=[provider]) as S:
        print('Running', S.conf())
        try:
            while True: # wait forever
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass

    print('Done')
if __name__=='__main__':
    args = getargs()
    logging.basicConfig(level=args.verbose)
    main(args)
