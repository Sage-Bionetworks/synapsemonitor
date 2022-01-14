"""Test monitor module"""
from unittest import mock
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from synapseclient import EntityViewSchema, Project, Folder, File

from synapsemonitor import monitor
import synapsemonitor


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
            'currentVersion': [2],
            'modifiedOn': ["1970-01-12 05:46:40-08:00"],
            'createdOn': ["1970-01-12 05:46:40-08:00"],
            'modifiedBy': ["user"], 'type': "file",
            'projectId': 'syn55555'
        })
        self.expecteddf['createdOn'] = self.expecteddf['createdOn'].astype(
            'datetime64[ns, US/Pacific]'
        )
        self.expecteddf['modifiedOn'] = self.expecteddf['modifiedOn'].astype(
            'datetime64[ns, US/Pacific]'
        )

    def test__render_fileview(self):
        """Test rendering of file view"""
        with patch.object(self.syn, "getUserProfile",
                          return_value={"userName": "user"}) as patch_get:
            rendereddf = monitor._render_fileview(self.syn,
                                                  self.query_resultsdf)
            patch_get.assert_called_once_with(333333)
            assert rendereddf.equals(self.expecteddf)

    def test__find_modified_entities_fileview(self):
        """Patch finding modified entities"""
        with patch.object(self.syn, "tableQuery",
                          return_value=self.table_query_results) as patch_q,\
            patch.object(self.table_query_results, "asDataFrame",
                         return_value=self.query_resultsdf) as patch_asdf,\
            patch.object(monitor, "_render_fileview",
                         return_value=self.expecteddf) as patch_render:
            resultdf = monitor._find_modified_entities_fileview(
                self.syn, "syn44444", days=2
            )
            patch_q.assert_called_once_with(
                "select id, name, currentVersion, modifiedOn, modifiedBy, "
                "createdOn, projectId, type from syn44444 where "
                "modifiedOn > unix_timestamp(NOW() - INTERVAL 2 DAY)*1000"
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


@pytest.mark.parametrize(
    "entity, entity_type",
    [
        (Project(id="syn12345", parentId="syn3333"), "Project"),
        (Folder(id="syn12345", parentId="syn3333"), "Folder"),
        (File(id="syn12345", parentId="syn3333"), "File")
    ]
)
def test_find_modified_entities(entity, entity_type):
    """Test unsupported entity types to monitor"""
    syn = Mock()
    with pytest.raises(NotImplementedError, match=".not supported yet"),\
         patch.object(syn, "get", return_value=entity):
        monitor.find_modified_entities(
            syn=syn, syn_id="syn12345", days=1
        )


def test_find_modified_entities():
    """Test supported entity types to monitor"""
    entity = EntityViewSchema(id="syn12345", parentId="syn3333")
    syn = Mock()
    empty = pd.DataFrame()
    with patch.object(syn, "get", return_value=entity) as patch_get,\
         patch.object(monitor, "_find_modified_entities_fileview",
                      return_value=empty) as patch_mod:
        value = monitor.find_modified_entities(
            syn=syn, syn_id="syn12345", days=1
        )
        patch_get.assert_called_once_with("syn12345", downloadFile=False)
        patch_mod.assert_called_once()
        assert empty.equals(value)


class TestMonitoring:
    """Test monitoring function, includes integration test"""
    def setup_method(self):
        self.syn = Mock()

    def test_monitoring_fail_integration(self):
        """Test all monitoring functions are called"""
        returndf = pd.DataFrame({"test": ["foo"]})
        with patch.object(monitor, "find_modified_entities",
                          return_value=returndf) as patch_find,\
             patch.object(monitor, "_get_user_ids",
                          return_value=[111]) as patch_get_user,\
             patch.object(self.syn, "sendMessage") as patch_send:
            monitor.monitoring(self.syn, "syn12345", users=["2222", "fooo"],
                               email_subject="new subject", days=15)
            patch_find.assert_called_once_with(syn=self.syn, syn_id="syn12345", days=15)
            patch_get_user.assert_called_once_with(self.syn, ["2222", "fooo"])
            patch_send.assert_called_once_with([111], "new subject",
                                               returndf.to_html(index=False),
                                               contentType='text/html')
