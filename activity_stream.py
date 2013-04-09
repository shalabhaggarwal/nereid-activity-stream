# -*- coding: utf-8 -*-
"""
    activity_stream

    Activity Stream module.

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.wizard import Wizard, StateTransition, StateView, Button


class NereidUser(ModelSQL, ModelView):
    "Nereid User"
    _name = 'nereid.user'

    activity_stream = fields.One2Many(
        'activity.stream', 'nereid_user', 'Activity Stream'
    )

NereidUser()


class ActivityStream(ModelSQL, ModelView):
    "Activity Stream"
    _name = 'activity.stream'
    _description = __doc__

    nereid_user = fields.Many2One(
        'nereid.user', 'Nereid User', required=True, select=True
    )
    actor = fields.Many2One(
        'party.party', 'Actor', required=True, select=True
    )
    verb = fields.Char("Verb", required=True)
    object = fields.Reference(
        "Object", selection='objects_get', select=True
    )
    target = fields.Many2One(
        'ir.model.field', 'Target',
        select=True, depends=['object'],
        states={'invisible': ~Eval('object')}
    )
    create_date = fields.DateTime('Published On', readonly=True, select=True)
    #TODO
    # url - fields.function - the URL of the stream record.

    def __init__(self):
        super(ActivityStream, self).__init__()
        self._constraints += [
            ('check_target', 'wrong_target')
        ]
        self._error_messages.update({
            'wrong_target': 'The target field selected does not belong '
            'to model in object'
        })

    def check_target(self, ids):
        "Checks whether the target belongs to the model chosen in object."
        field_obj = Pool().get('ir.model.field')

        for activity in self.browse(ids):
            # If object or target is missing, then dont check.
            if not activity.object or not activity.target:
                continue

            model_name = activity.object.split(',')[0]
            field_ids = field_obj.search([
                ('model.model', '=', model_name),
                ('id', '=', activity.target.id)
            ])
            if not field_ids:
                return False

        return True

    def objects_get(self):
        "Returns the activity stream objects in form of list of tuples."
        stream_object_obj = Pool().get('activity.stream.object')

        stream_object_ids = stream_object_obj.search([])
        res = []
        for stream_object in stream_object_obj.browse(stream_object_ids):
            res.append((stream_object.model.model, stream_object.name))
        return res

ActivityStream()


class ActivityStreamObject(ModelSQL, ModelView):
    "Activity Stream Object"
    _name = 'activity.stream.object'
    _description = __doc__

    name = fields.Char("Name", required=True, select=True)
    model = fields.Many2One('ir.model', 'Model', required=True, select=True)

ActivityStreamObject()


class ActivityStreamBroadcastStart(ModelView):
    'Activity Stream Broadcast Start'
    _name = 'activity.stream.broadcast.start'
    _description = __doc__

    nereid_user = fields.Many2One('nereid.user', 'Nereid User', required=True)
    message = fields.Text("Message", required=True)

ActivityStreamBroadcastStart()


class ActivityStreamBroadcast(Wizard):
    'Activity Stream Broadcast'
    _name = 'activity.stream.broadcast'
    _description = __doc__

    start = StateView(
        'activity.stream.broadcast.start',
        'nereid_activity_stream.activity_stream_broadcast_start_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Submit', 'submit_', 'tryton-ok')
        ]
    )

    submit_ = StateTransition()

    def transition_submit_(self, session):
        '''
        This method creates an activity stream record for each
        nereid user with the details provided in wizard.
        '''
        activity_stream_obj = Pool().get('activity.stream')
        nereid_user_obj = Pool().get('nereid.user')

        nereid_user_ids = nereid_user_obj.search([])

        for user_id in nereid_user_ids:
            activity_stream_obj.create({
                'actor': session.start.nereid_user.id,
                'nereid_user': user_id,
                'verb': session.start.message,
            })
        return 'end'

ActivityStreamBroadcast()
