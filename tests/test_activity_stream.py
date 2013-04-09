# -*- coding: utf-8 -*-
"""
    Test activity stream

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import sys
import os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import POOL, CONTEXT, USER, DB_NAME
from trytond.transaction import Transaction
from trytond.wizard import Session


class ActivityStreamTestCase(unittest.TestCase):
    '''
    Test Nereid Activity Stream  module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('nereid_activity_stream')
        self.activity_stream_obj = POOL.get('activity.stream')
        self.party_obj = POOL.get('party.party')
        self.company_obj = POOL.get('company.company')
        self.nereid_user_obj = POOL.get('nereid.user')
        self.currency_obj = POOL.get('currency.currency')
        self.activity_stream_object_obj = POOL.get('activity.stream.object')
        self.activity_stream_broadcast_wizard = POOL. \
            get('activity.stream.broadcast', type='wizard')
        self.model_obj = POOL.get('ir.model')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('nereid_activity_stream')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()

    def create_user(self):
        '''
        Cretae User.
        '''

        self.user_party = self.party_obj.create({
            'name': 'User1',
        })

        currency = self.currency_obj.create({
            'name': 'US Dollar',
            'code': 'USD',
            'symbol': '$',
        })

        self.company = self.company_obj.create({
            'name': 'openlabs',
            'currency': currency,
        })

        actor_party = self.party_obj.create({
            'name': 'Party1',
        })

        self.nereid_user_user = self.nereid_user_obj.create({
            'party': self.user_party,
            'company': self.company,
        })

        self.nereid_user_actor = self.nereid_user_obj.create({
            'party': actor_party,
            'company': self.company,
        })

        self.nereid_stream_owner = self.nereid_user_obj.create({
            'party': self.nereid_user_user,
            'company': self.company,
        })

        party_model_id, = self.model_obj.search([
            ('model', '=', 'party.party')
        ])

        activity_stream_object = self.activity_stream_object_obj.create({
            'name': 'Party',
            'model': party_model_id,
        })

    def test0010activity_stream(self):
        '''
        Creates activity stream object and uses it in activity stream.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_user()

            activity_stream = self.activity_stream_obj.create({
                'verb': 'Added a new friend',
                'actor': self.nereid_user_actor,
                'nereid_user': self.nereid_stream_owner,
                'object': 'party.party,%s' % self.user_party,
            })
            user = self.nereid_user_obj.browse(self.nereid_stream_owner)

            self.assertTrue(
                self.activity_stream_obj.browse(activity_stream) in \
                user.activity_stream
            )

    def test0020activity_stream_object(self):
        '''
        Creates activity stream object but uses company in activity stream.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_user()

            self.assertRaises(
                Exception, self.activity_stream_obj.create, {
                    'verb': 'Added a new friend',
                    'actor': self.nereid_user_actor,
                    'nereid_user': self.nereid_stream_owner,
                    'object': 'company.company,%s' % self.company,
                }
            )

    def test0030activity_stream_broadcast(self):
        '''
        Creates activity stream broadcast for activity stream.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_user()

            session_id, start_state, end_state = self. \
                activity_stream_broadcast_wizard.create()

            session = Session(
                self.activity_stream_broadcast_wizard, session_id
            )

            session.data['start'].update({
                'nereid_user': self.nereid_user_actor,
                'message': 'This is a system test message'
            })

            self.activity_stream_broadcast_wizard.transition_submit_(session)
            user1 = self.nereid_user_obj.browse(self.nereid_stream_owner)
            user2 = self.nereid_user_obj.browse(self.nereid_user_user)
            user3 = self.nereid_user_obj.browse(self.nereid_user_actor)

            for each in (user1, user2, user3):
                self.assertTrue(
                    'This is a system test message' in \
                        each.activity_stream[0].verb
            )


def suite():
    '''
    Test Suite
    '''
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        ActivityStreamTestCase)
    )
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
