#!/usr/bin/env python

"""
@file ion/services/dm/scheduler/test/test_scheduler.py
@date 9/21/10
@author Paul Hubbard
@test ion.services.dm.scheduler Exercise the crontab
"""

from twisted.internet import defer

from ion.core.data.cassandra_bootstrap import CassandraSchemaProvider, IndexType
from ion.core.object import object_utils
from ion.services.dm.scheduler.scheduler_service import SchedulerService
from ion.core.data import storage_configuration_utility
from ion.core.data.storage_configuration_utility import STORAGE_PROVIDER, PERSISTENT_ARCHIVE

import ion.util.ionlog

log = ion.util.ionlog.getLogger(__name__)

# get configuration
from ion.core import ioninit
CONF = ioninit.config(__name__)

ADDTASK_REQ_TYPE     = object_utils.create_type_identifier(object_id=2601, version=1)
ADDTASK_RSP_TYPE     = object_utils.create_type_identifier(object_id=2602, version=1)
RMTASK_REQ_TYPE      = object_utils.create_type_identifier(object_id=2603, version=1)
RMTASK_RSP_TYPE      = object_utils.create_type_identifier(object_id=2604, version=1)
QUERYTASK_REQ_TYPE   = object_utils.create_type_identifier(object_id=2605, version=1)
QUERYTASK_RSP_TYPE   = object_utils.create_type_identifier(object_id=2606, version=1)

# other messages used for payloads
SCHEDULE_TYPE_PERFORM_INGESTION_UPDATE_PAYLOAD_TYPE = object_utils.create_type_identifier(object_id=2607, version=1)

# desired_origins
from ion.services.dm.scheduler.test.test_scheduler import SchedulerTest

class SchedulerCassandraTest(SchedulerTest):
    """
    Derived test for using the cassandra backend for scheduler service.
    """

    KEYSPACE = 'test_scheduler_ks'

    @defer.inlineCallbacks
    def setUp(self):
        yield SchedulerTest.setUp(self)

    def _get_spawn_args(self):
        return {'storage_provider':CONF.getValue('storage_provider', {'host':'localhost', 'port': 9160}),
                'index_store_class':CONF.getValue('index_store_class', 'ion.core.data.cassandra_bootstrap.CassandraIndexedStoreBootstrap'),
                'username':CONF.getValue('username', None),
                'password':CONF.getValue('password', None),
                'keyspace':CONF.getValue('keyspace', self.KEYSPACE)}

    @defer.inlineCallbacks
    def _setup_store(self):
        uname = CONF.getValue('cassandra_username', None)
        pword = CONF.getValue('cassandra_password', None)
        storage_provider = CONF.getValue(STORAGE_PROVIDER, self._get_spawn_args()['storage_provider'].copy())

        keyspace = self.KEYSPACE

        test_ks = storage_configuration_utility.base_ks_def.copy()
        test_ks['name'] = keyspace

        storage_conf = {
            STORAGE_PROVIDER:storage_provider,
            PERSISTENT_ARCHIVE:test_ks,
        }

        test_cf = storage_configuration_utility.base_cf_def.copy()
        test_cf['name'] = SchedulerService.COLUMN_FAMILY
        test_cf['keyspace'] = keyspace
        test_cf['column_metadata'] = []

        test_ks['cf_defs']=[test_cf]

        for col in SchedulerService.INDICES:
            test_col = storage_configuration_utility.base_col_def.copy()

            test_col['name'] = col
            test_col['index_type'] = IndexType.KEYS
            test_cf['column_metadata'].append(test_col)


        self.test_harness = CassandraSchemaProvider(uname,pword,storage_conf,error_if_existing=False)
        self.test_harness.connect()
        yield self.test_harness.run_cassandra_config()
        yield self.test_harness.client.truncate(SchedulerService.COLUMN_FAMILY)

    @defer.inlineCallbacks
    def _cleanup_store(self):
        yield self.test_harness.client.truncate(SchedulerService.COLUMN_FAMILY)
        yield self.test_harness.disconnect()

