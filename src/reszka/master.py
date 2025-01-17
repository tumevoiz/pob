import logging
from dataclasses import dataclass

import requests
from pydantic import BaseModel
from pydantic_core._pydantic_core import to_jsonable_python

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BlockchainNetworkError(RuntimeError):
    pass


class Node(BaseModel):
    url: str


class RegisterNodeRequest(BaseModel):
    node: Node
    key: str


@dataclass
class Network:
    master_node: Node
    nodes: list[Node]
    key: str

    def register_node(self, node: Node, key: str) -> None:
        if self.key != key:
            raise BlockchainNetworkError('Invalid network key. Cannot register node!')

        logger.info(f"Registering node: {node.url}")
        self.nodes.append(node)

    @staticmethod
    def register_node_in_master(url: str, master_node_url: str, key: str) -> None:
        payload = to_jsonable_python(RegisterNodeRequest(node=Node(url=f"http://{url}"), key=key))
        req = requests.post(f"{master_node_url}/nodes", json=payload)
        if req.status_code != 201:
            raise BlockchainNetworkError(f"Cannot register node: {req.json()}")

        logger.info(f"Successfuly registered node: {payload}")
