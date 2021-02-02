"""Test monitor module"""
from unittest import mock
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from synapseclient import EntityViewSchema, Project

from synapsemonitor import monitor


class TestModifiedEntities:
    """Test modifying entities"""
    def setup_method(self):
        self.syn = Mock()
        self.table_query_results = Mock()
        query_results = {
            "id": ["syn23333"], "name": ["test"],
            'currentVersion': [2], 'modifiedOn': [1000000000],
            'createdOn': [1000000000],
            'modifiedBy': [333333], 'type': "file",
            'projectId': ['syn55555']
        }
        self.query_resultsdf = pd.DataFrame(query_results)
        self.expecteddf = pd.DataFrame({
            "id": ["syn23333"], "name": ["test"],
            'currentVersion': [2], 'modifiedOn': ["Jan/12/1970 13:46"],
            'createdOn': ["Jan/12/1970 13:46"],
            'modifiedBy': ["user"], 'type': "file",
            'projectId': 'syn55555'
        })

    def test__render_fileview(self):
        """Test rendering of file view"""
        with patch.object(self.syn, "getUserProfile",
                          return_value={"userName": "user"}) as patch_get:
            rendereddf = monitor._render_fileview(self.syn,
                                                  self.query_resultsdf)
            patch_get.assert_called_once_with(333333)
            assert rendereddf.equals(self.expecteddf)

    def test_find_modified_entities(self):
        """Patch finding modified entities"""
        with patch.object(self.syn, "tableQuery",
                          return_value=self.table_query_results) as patch_q,\
            patch.object(self.table_query_results, "asDataFrame",
                         return_value=self.query_resultsdf) as patch_asdf,\
            patch.object(monitor, "_render_fileview",
                         return_value=self.expecteddf) as patch_render:
            resultdf = monitor.find_modified_entities(self.syn, "syn44444",
                                                      days=2)
            patch_q.assert_called_once_with(
                "select id, name, currentVersion, modifiedOn, modifiedBy, "
                f"createdOn, projectId, type from syn44444 where "
                f"modifiedOn > unix_timestamp(NOW() - INTERVAL 2 DAY)*1000"
            )
            patch_asdf.assert_called_once_with()
            assert resultdf.equals(self.expecteddf)
            patch_render.assert_called_once_with(
                self.syn, viewdf=self.query_resultsdf
            )

def test__get_user_ids_none():
    """Test getting logged in user profile when no users specified"""
    syn = Mock()
    with patch.object(syn, "getUserProfile",
                      return_value={"ownerId": "111"}) as patch_get:
        user_ids = monitor._get_user_ids(syn, None)
        patch_get.assert_called_once_with()
        assert user_ids == ["111"]


def test__get_user_ids():
    """Test getting user profiles ids"""
    syn = Mock()
    with patch.object(syn, "getUserProfile",
                      return_value={"ownerId": "111"}) as patch_get:
        user_ids = monitor._get_user_ids(syn, [1, "username"])
        patch_get.has_calls([mock.call(1), mock.call("username")])
        assert user_ids == ["111", "111"]


class TestMonitoring:
    """Test monitoring function, includes integration test"""
    def setup_method(self):
        self.syn = Mock()

    def test_monitoring_fail_entity(self):
        """Test only FileView entities are accepted"""
        entity = Project(id="syn12345")
        with pytest.raises(ValueError,
                           match="syn12345 must be a Synapse File View"),\
            patch.object(self.syn, "get", return_value=entity):
            monitor.monitoring(self.syn, "syn12345")

    def test_monitoring_fail_integration(self):
        """Test all monitoring functions are called"""
        entity = EntityViewSchema(id="syn12345", parentId="syn3333")
        returndf = pd.DataFrame({"test": ["foo"]})
        with patch.object(self.syn, "get", return_value=entity) as patch_get,\
             patch.object(monitor, "find_modified_entities",
                          return_value=returndf) as patch_find,\
             patch.object(monitor, "_get_user_ids",
                          return_value=[111]) as patch_get_user,\
             patch.object(self.syn, "sendMessage") as patch_send:
            monitor.monitoring(self.syn, "syn12345", users=["2222", "fooo"],
                               email_subject="new subject", days=15)
            patch_get.assert_called_once_with("syn12345")
            patch_find.assert_called_once_with(self.syn, "syn12345", days=15)
            patch_get_user.assert_called_once_with(self.syn, ["2222", "fooo"])
            patch_send.assert_called_once_with([111], "new subject",
                                               returndf.to_html(index=False),
                                               contentType='text/html')
