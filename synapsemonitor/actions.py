from abc import ABC, abstractmethod
from typing import Type

from synapseclient import Synapse

from . import monitor


class SynapseAction(ABC):
    """Base synapse action class"""

    def __init__(
        self, syn: Synapse, syn_id: str, days: int = 1, verbose: bool = False
    ) -> None:
        self.syn = syn
        self.syn_id = syn_id
        self.days = days
        self.verbose = verbose

    @abstractmethod
    def _action(self, modified_entities: list) -> None:
        pass

    def action(self):
        """Do action on list modified entities"""
        modified_entities = monitor.find_modified_entities(
            syn=self.syn, syn_id=self.syn_id, days=self.days
        )
        action_result = self._action(modified_entities)
        if self.verbose:
            print(action_result)
        return action_result


class EmailAction(SynapseAction):
    """This action emails specified users with modified entities"""

    def __init__(
        self,
        syn: Synapse,
        syn_id: str,
        days: int = 1,
        verbose: bool = False,
        users: list = None,
        email_subject: str = "New Synapse Files",
    ):
        self.users = users
        self.email_subject = email_subject
        super().__init__(syn=syn, syn_id=syn_id, days=days, verbose=verbose)

    def _action(self, modified_entities: list) -> list:
        # get user ids
        user_ids = monitor._get_user_ids(self.syn, self.users)

        # TODO: Add function to beautify email message

        # Prepare and send Message
        if modified_entities:
            self.syn.sendMessage(
                user_ids,
                self.email_subject,
                ", ".join(modified_entities),
                contentType="text/html",
            )
        return modified_entities


def synapse_action(action_cls: Type[SynapseAction]):
    """synapse action helper function

    Args:
        action_cls: Takes in any class that extends SynapseAction

    Returns:
        User defined return
    """
    action_results = action_cls.action()
    return action_results
