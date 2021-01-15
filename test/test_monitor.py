"""Test monitor module"""
from unittest.mock import Mock, patch

import pandas as pd
from synapseclient import Project

from synapsemonitor import monitor


class TestGetEpochStart:
    """Test get_epoch_start"""
    def setup_method(self):
        self.project = Project(lastAuditTimeStamp=[3])
        self.syn = Mock()

    def test_specify_days(self):
        """Testing days specified"""
        epochtime = monitor.get_audit_time(self.syn, self.project, 864000000, days=9)
        assert epochtime == 86400000

    def test_none_days(self):
        """Test no days"""
        epochtime = monitor.get_audit_time(self.syn, self.project, 864000000)
        assert epochtime == 3

    def test_none_days_no_last_audit(self):
        """Testing no days and no last audit"""
        self.project.lastAuditTimeStamp = None
        epochtime = monitor.get_audit_time(self.syn, self.project, 864000000)
        assert epochtime == 768960000


def test_find_new_files():
    project = Project(id="syn2222", name="testing")
    syn = Mock()
    table_query_results = Mock()
    query_results = {"id": ["syn23333"], "name": ["test"],
                     'currentVersion': [2], 'modifiedOn': [1000000000],
                     'modifiedBy': [333333], 'type': "file",
                     'projectId': ['syn55555']}
    query_resultsdf = pd.DataFrame(query_results)
    expecteddf = pd.DataFrame({
        "id": ["syn23333"], "name": ["test"],
        'currentVersion': [2], 'modifiedOn': ["Jan/12/1970 13:46"],
        'modifiedBy': ["user"], 'type': "file",
        'projectId': 'syn55555'
    })
    with patch.object(syn, "tableQuery", return_value=table_query_results),\
         patch.object(table_query_results, "asDataFrame",
                      return_value=query_resultsdf),\
         patch.object(syn, "getUserProfile",
                      return_value={"userName": "user"}):

        resultdf = monitor.find_new_files(syn, "syn44444", 222222)
        assert resultdf.equals(expecteddf)
