"""Test monitor module"""
from synapseclient import Project

from synapsemonitor import monitor


class TestGetEpochStart:
    """Test get_epoch_start"""
    def setup_method(self):
        self.project = Project(lastAuditTimeStamp=[3])

    def test_specify_days(self):
        """Testing days specified"""
        epochtime = monitor.get_epoch_start(self.project, 864000000, days=9)
        assert epochtime == 86400000

    def test_none_days(self):
        """Test no days"""
        epochtime = monitor.get_epoch_start(self.project, 864000000)
        assert epochtime == 3

    def test_none_days_no_last_audit(self):
        """Testing no days and no last audit"""
        self.project.lastAuditTimeStamp = None
        epochtime = monitor.get_epoch_start(self.project, 864000000)
        assert epochtime == 768960000
