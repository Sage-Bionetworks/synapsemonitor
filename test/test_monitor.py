"""Test monitor module"""
from unittest.mock import Mock, patch

import pandas as pd
from synapseclient import EntityViewSchema, Project

from synapsemonitor import monitor


# class TestGetEpochStart:
#     """Test get_epoch_start"""
#     def setup_method(self):
#         self.view = EntityViewSchema(lastAuditTimeStamp=[3], parentId="syn2222")
#         self.syn = Mock()

#     def test_specify_days(self):
#         """Testing days specified"""
#         epochtime = monitor._get_audit_time(864000000, 9, self.view, use_last_audit_time=False)
#         assert epochtime == 86400000

#     def test_none_days(self):
#         """Test no days and not use last audit time"""
#         epochtime = monitor._get_audit_time(864000000, None, self.view, use_last_audit_time=False)
#         assert epochtime == 777600000

#     def test_none_days_audit(self):
#         """Test no days and use last audit time"""
#         epochtime = monitor._get_audit_time(864000000, None, self.view, use_last_audit_time=True)
#         assert epochtime == 3

#     def test_none_days_no_last_audit(self):
#         """Testing no days and use last audit, but value doesn't exist"""
#         self.view.lastAuditTimeStamp = None
#         epochtime = monitor._get_audit_time(864000000, None, self.view, use_last_audit_time=True)
#         assert epochtime == 777600000


def test_find_modified_entities():
    project = Project(id="syn2222", name="testing")
    syn = Mock()
    table_query_results = Mock()
    query_results = {"id": ["syn23333"], "name": ["test"],
                     'currentVersion': [2], 'modifiedOn': [1000000000],
                     'createdOn': [1000000000],
                     'modifiedBy': [333333], 'type': "file",
                     'projectId': ['syn55555']}
    query_resultsdf = pd.DataFrame(query_results)
    expecteddf = pd.DataFrame({
        "id": ["syn23333"], "name": ["test"],
        'currentVersion': [2], 'modifiedOn': ["Jan/12/1970 13:46"],
        'createdOn': ["Jan/12/1970 13:46"],
        'modifiedBy': ["user"], 'type': "file",
        'projectId': 'syn55555'
    })
    with patch.object(syn, "tableQuery", return_value=table_query_results),\
         patch.object(table_query_results, "asDataFrame",
                      return_value=query_resultsdf),\
         patch.object(syn, "getUserProfile",
                      return_value={"userName": "user"}):

        resultdf = monitor.find_modified_entities(syn, "syn44444", days=2)
        assert resultdf.equals(expecteddf)
