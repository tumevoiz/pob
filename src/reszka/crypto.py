import uuid
from datetime import datetime
from pydantic import BaseModel

class Block(BaseModel):
    id: uuid.UUID
    content: str

    hash: str | None
    previous_hash: str

    timestamp: float
    nonce: int

    def __str__(self) -> str:
        return f"Block[ID: {self.id}, C: {self.content}, H: {self.hash}, PH: {self.previous_hash}, T: {self.timestamp}, N: {self.nonce}]"


class CreateBlockRequest(BaseModel):
    content: str


class Miner: # TODO: implement it
    def mine(self, block: Block) -> Block:
        pass


def _calculate_current_hash(block: Block) -> str: # TODO: implement it
    pass


class Blockchain:
    blocks: list[Block] = []

    def __init__(self, miner: Miner):
        self._miner = miner

        genesis = Block(
            id=uuid.uuid4(),
            content='GENESIS',
            hash=None,
            previous_hash='',
            timestamp=0,
            nonce=0
        )

        genesis.hash = _calculate_current_hash(genesis)

        self.blocks = [
            genesis
        ]

    def add_block(self, create_block_request: CreateBlockRequest) -> None:
        block_id = uuid.uuid4()
        block_timestamp = datetime.now().timestamp()
        block_content = create_block_request.content

        block = Block(
            id=block_id,
            content=block_content,
            hash=None,
            previous_hash=self.blocks[-1].hash,
            timestamp=block_timestamp,
            nonce=0
        )

        mined_block = self._miner.mine(block)

        self.blocks.append(mined_block)
