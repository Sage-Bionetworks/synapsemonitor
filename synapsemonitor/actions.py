from abc import ABC, abstractmethod

from synapseclient import Synapse

from . import monitor


class SynapseAction(ABC):
    def __init__(self, syn: Synapse, syn_id: str, days: int = 1) -> None:
        self.syn = syn
        self.syn_id = syn_id
        self.days = days

    @abstractmethod
    def _action(self, modified_entities: list) -> None:
        pass

    def action(self):
        """Do action on list modified entities"""
        modified_entities = monitor.find_modified_entities(
            syn=self.syn, syn_id=self.syn_id, days=self.days
        )
        action_result = self._action(modified_entities)
        return action_result
