"""Test monitor module"""
from datetime import datetime, timedelta
from dateutil import tz
from unittest import mock
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from synapseclient import EntityViewSchema, Project, Folder, File, Entity

from synapsemonitor import monitor


class TestModifiedEntitiesFileView:
    """Test modifying entities"""

    def setup_method(self):
        self.syn = Mock()
        self.table_query_results = Mock()
        query_results = {
            "id": ["syn23333"],
            "name": ["test"],
            "currentVersion": [2],
            "modifiedOn": [1000000000],
            "createdOn": [1000000000],
            "modifiedBy": [333333],
            "type": "file",
            "projectId": ["syn55555"],
        }
        self.query_resultsdf = pd.DataFrame(query_results)
        self.expecteddf = pd.DataFrame(
            {
                "id": ["syn23333"],
                "name": ["test"],
                "currentVersion": [2],
                "modifiedOn": ["1970-01-12 05:46:40-08:00"],
                "createdOn": ["1970-01-12 05:46:40-08:00"],
                "modifiedBy": ["user"],
                "type": "file",
                "projectId": "syn55555",
            }
        )
        self.expecteddf["createdOn"] = self.expecteddf["createdOn"].astype(
            "datetime64[ns, US/Pacific]"
        )
        self.expecteddf["modifiedOn"] = self.expecteddf["modifiedOn"].astype(
            "datetime64[ns, US/Pacific]"
        )

    def test__render_fileview(self):
        """Test rendering of file view"""
        with patch.object(
            self.syn, "getUserProfile", return_value={"userName": "user"}
        ) as patch_get:
            rendereddf = monitor._render_fileview(self.syn, self.query_resultsdf)
            patch_get.assert_called_once_with(333333)
            assert rendereddf.equals(self.expecteddf)

    def test__find_modified_entities_fileview(self):
        """Patch finding modified entities"""
        with patch.object(
            self.syn, "tableQuery", return_value=self.table_query_results
        ) as patch_q, patch.object(
            self.table_query_results, "asDataFrame", return_value=self.query_resultsdf
        ) as patch_asdf:
            # patch.object(monitor, "_render_fileview",
            #              return_value=self.expecteddf) as patch_render:
            modified_list = monitor._find_modified_entities_fileview(
                self.syn, "syn44444", days=2
            )
            patch_q.assert_called_once_with(
                "select id from syn44444 where "
                "modifiedOn > unix_timestamp(NOW() - INTERVAL 2 DAY)*1000"
            )
            patch_asdf.assert_called_once_with()
            assert modified_list == ["syn23333"]
            # patch_render.assert_called_once_with(
            #     self.syn, viewdf=self.query_resultsdf
            # )


class TestModifiedContainer:
    """Test modifying containers"""

    def setup_method(self):
        self.syn = Mock()
        self.days = 1
        self.now = datetime.now().replace(tzinfo=tz.tzutc()).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.past = (datetime.now().replace(tzinfo=tz.tzutc()) - timedelta(days=self.days+1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.project = Project(name="test_project", id = "syn0", modifiedOn=self.now, parentId = "syn00")
        self.folder = Folder(name="test_folder", id = "syn1", modifiedOn=self.now, parentId = "syn0")
        self.file = File(name="test_file", id = "syn2", modifiedOn=self.now, parentId = "syn1")
        self.file_child = File(name="test_file", id = "syn2", modifiedOn=self.now, parentId = "syn1", type = "org.sagebionetworks.repo.model.FileEntity")


    def test__traverse_folder_include(self):
        """Traverse folder no children including project entity types"""
        with patch.object(self.syn, "get",
                          return_value=self.folder) as patch_get,\
            patch.object(self.syn, "getChildren",
                         return_value=[]) as patch_child:
            desc = monitor._traverse_root(self.syn, self.folder["id"], include_types=["file", "folder", "project"])
            patch_get.assert_called()
            patch_child.assert_called()
            assert desc == [self.folder["id"]]


    def test__traverse_folder_exclude(self):
        """Traverse folder no children excluding folder entity types"""
        with patch.object(self.syn, "get",
                          return_value=self.folder) as patch_get,\
            patch.object(self.syn, "getChildren",
                         return_value=[]) as patch_child:
            desc = monitor._traverse_root(self.syn, self.folder["id"], include_types=["file"])
            patch_get.assert_called()
            patch_child.assert_called()
            assert desc == []


    def test__traverse_project_include(self):
        """Traverse project with no children including project entity types"""
        with patch.object(self.syn, "get",
                          return_value=self.project) as patch_get,\
            patch.object(self.syn, "getChildren",
                         return_value=[]) as patch_child:
            desc = monitor._traverse_root(self.syn, self.project["id"], include_types=["file", "folder", "project"])
            patch_get.assert_called()
            patch_child.assert_called()
            assert desc == [self.project["id"]]


    def test__traverse_project_exclude(self):
        """Traverse project with no children excluding project entity types"""
        with patch.object(self.syn, "get",
                          return_value=self.project) as patch_get,\
            patch.object(self.syn, "getChildren",
                         return_value=[]) as patch_child:
            desc = monitor._traverse_root(self.syn, self.project["id"], include_types=["file", "folder"])
            patch_get.assert_called()
            patch_child.assert_called()
            assert desc == []

    
    def test__traverse_file_include(self):
        """Traverse file including file entity types"""
        with patch.object(self.syn, "get",
                          return_value=self.file) as patch_get,\
            patch.object(self.syn, "getChildren",
                         return_value=[]) as patch_child:
            desc = monitor._traverse_root(self.syn, self.file["id"], include_types=["file", "folder", "project"])
            patch_get.assert_called()
            patch_child.assert_called()
            assert desc == [self.file["id"]]


    def test__traverse_file_exclude(self):
        """Traverse project with no children excluding project entity types"""
        with patch.object(self.syn, "get",
                          return_value=self.file) as patch_get,\
            patch.object(self.syn, "getChildren",
                         return_value=[]) as patch_child:
            desc = monitor._traverse_root(self.syn, self.file["id"], include_types=["folder", "project"])
            patch_get.assert_called()
            patch_child.assert_called()
            assert desc == []


    def test__traverse_folder_with_file_child(self):
        """Traverse project with no children excluding project entity types"""
        with patch.object(self.syn, "get",
                          return_value=self.folder) as patch_get,\
            patch.object(self.syn, "getChildren",
                         return_value=[self.file_child]) as patch_child:
            desc = monitor._traverse_root(self.syn, self.folder["id"], include_types=["folder", "project", "file"])
            patch_get.assert_called()
            patch_child.assert_called()
            assert desc == [self.file_child["id"], self.folder["id"]]
            
            
    def test__find_modified_entities_folder_modified(self):
        """Find modified entities in a folder"""
        with patch.object(monitor, "_traverse_root",
                          return_value=[self.folder["id"]]) as patch_get,\
            patch.object(monitor, "_find_modified_entities_file",
                         return_value=[self.folder["id"]]) as patch_child:
            modified_list = monitor._find_modified_entities_container(
                self.syn, self.folder["id"], days=self.days
            )
            patch_get.assert_called()
            patch_child.assert_called()
            assert modified_list == ["syn1"]


    def test__find_modified_entities_project_modified(self):
        """Find modified entities in a project"""
        with patch.object(monitor, "_traverse_root",
                          return_value=[self.project["id"]]) as patch_get,\
            patch.object(monitor, "_find_modified_entities_file",
                         return_value=[self.project["id"]]) as patch_child:
            modified_list = monitor._find_modified_entities_container(
                self.syn, self.project["id"], days=self.days
            )
            patch_get.assert_called()
            patch_child.assert_called()
            assert modified_list == ["syn0"]

    def test__find_modified_entities_folder_not_modified(self):
        """Find no modified entities in a folder"""

        folder = self.folder
        folder['modifiedOn'] = self.past
        with patch.object(monitor, "_traverse_root",
                          return_value=[self.folder["id"]]) as patch_get,\
            patch.object(monitor, "_find_modified_entities_file",
                         return_value=[]) as patch_child:
            modified_list = monitor._find_modified_entities_container(
                self.syn, "syn234", days=self.days
            )
            patch_get.assert_called()
            patch_child.assert_called()
            assert modified_list == []


    def test__find_modified_entities_project_not_modified(self):
        """Find no modified entities in a project"""
        project = self.project
        project['modifiedOn'] = self.past
        with patch.object(monitor, "_traverse_root",
                          return_value=[self.folder["id"]]) as patch_get,\
            patch.object(monitor, "_find_modified_entities_file",
                         return_value=[]) as patch_child:
            modified_list = monitor._find_modified_entities_container(
                self.syn, "syn234", days=self.days
            )
            patch_get.assert_called()
            patch_child.assert_called()
            assert modified_list == []


def test__find_modified_entities_file_modified():
    """Patch finding modified entities no modified"""
    syn = Mock()
    date_mod = (
        datetime.now().replace(tzinfo=tz.tzutc()).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    entity = File("test", "syn234", modifiedOn=date_mod)
    with patch.object(syn, "get", return_value=entity) as patch_get:
        modified_list = monitor._find_modified_entities_file(syn, "syn234", days=1)
        patch_get.assert_called_once_with("syn234", downloadFile=False)
        assert modified_list == ["syn234"]


def test__find_modified_entities_file_none():
    """Patch finding modified entities no modified"""
    syn = Mock()
    # create a modified date that is in the past
    old_modified = datetime.now() - timedelta(days=3)
    date_mod = old_modified.replace(tzinfo=tz.tzutc()).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    entity = File("test", "syn234", modifiedOn=date_mod)
    with patch.object(syn, "get", return_value=entity) as patch_get:
        modified_list = monitor._find_modified_entities_file(syn, "syn234", days=1)
        patch_get.assert_called_once_with("syn234", downloadFile=False)
        assert modified_list == []


def test__get_user_ids_none():
    """Test getting logged in user profile when no users specified"""
    syn = Mock()
    with patch.object(
        syn, "getUserProfile", return_value={"ownerId": "111"}
    ) as patch_get:
        user_ids = monitor._get_user_ids(syn, None)
        patch_get.assert_called_once_with()
        assert user_ids == ["111"]


def test__get_user_ids():
    """Test getting user profiles ids"""
    syn = Mock()
    with patch.object(
        syn, "getUserProfile", return_value={"ownerId": "111"}
    ) as patch_get:
        user_ids = monitor._get_user_ids(syn, [1, "username"])
        patch_get.has_calls([mock.call(1), mock.call("username")])
        assert user_ids == ["111", "111"]


@pytest.mark.parametrize(
    "entity, entity_type", [(Entity(id="syn12345", parentId="syn3333"), "Entity")]
)
def test_find_modified_entities_unsupported(entity, entity_type):
    """Test unsupported entity types"""
    syn = Mock()
    with pytest.raises(
        ValueError, match=f".+synapseclient.entity.{entity_type}'> not supported"
    ), patch.object(syn, "get", return_value=entity):
        monitor.find_modified_entities(syn=syn, syn_id="syn12345", days=1)


def test_find_modified_entities_supported():
    """Test supported entity types to monitor"""
    entity = EntityViewSchema(id="syn12345", parentId="syn3333")
    syn = Mock()
    empty = pd.DataFrame()
    with patch.object(syn, "get", return_value=entity) as patch_get, patch.object(
        monitor, "_find_modified_entities_fileview", return_value=empty
    ) as patch_mod:
        value = monitor.find_modified_entities(syn=syn, syn_id="syn12345", days=1)
        patch_get.assert_called_once_with("syn12345", downloadFile=False)
        patch_mod.assert_called_once()
        assert empty.equals(value)


class TestMonitoring:
    """Test monitoring function, includes integration test"""

    def setup_method(self):
        self.syn = Mock()

    def test_monitoring_fail_integration(self):
        """Test all monitoring functions are called"""
        modified_list = ["syn2222", "syn33333"]
        with patch.object(
            monitor, "find_modified_entities", return_value=modified_list
        ) as patch_find, patch.object(
            monitor, "_get_user_ids", return_value=[111]
        ) as patch_get_user, patch.object(
            self.syn, "sendMessage"
        ) as patch_send:
            monitor.monitoring(
                self.syn,
                "syn12345",
                users=["2222", "fooo"],
                email_subject="new subject",
                days=15,
            )
            patch_find.assert_called_once_with(syn=self.syn, syn_id="syn12345", days=15)
            patch_get_user.assert_called_once_with(self.syn, ["2222", "fooo"])
            patch_send.assert_called_once_with(
                [111], "new subject", "syn2222, syn33333", contentType="text/html"
            )
