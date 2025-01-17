import abc
import hashlib
import logging
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


class VerifyBlockRequest(BaseModel):
    block: Block
    source: str


class Miner(abc.ABC):
    def __init__(self, difficulty: int) -> None:
        self.difficulty = difficulty

    @abc.abstractmethod
    def mine(self, block: Block) -> Block:
        pass


def _calculate_current_hash(block: Block) -> str:
    inp = f"{block.id}+{block.timestamp}+{block.nonce}"
    return str(hashlib.sha256(inp.encode('utf-8')).hexdigest())


class POWMiner(Miner):

    def mine(self, block: Block) -> Block:
        mined = False
        last_block = None

        prefix = '0' * self.difficulty
        print(f"prefix: {prefix}")

        while not mined:
            current_block = block
            current_block.nonce += 1
            current_block.hash = _calculate_current_hash(current_block)

            print(
                f"[b_id: {current_block.id}; b_timestamp: {current_block.timestamp}] calculating hash: {current_block.hash}")

            mined = current_block.hash.startswith(prefix)
            last_block = current_block

        print(f"[b_id: {block.id}; b_timestamp: {block.timestamp}] mined.")
        return last_block

class BlockchainError(RuntimeError):
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

        genesis.hash = 'GENESIS_HASH'

        self.blocks = [
            genesis
        ]

    def add_block(self, create_block_request: CreateBlockRequest) -> Block:
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
        return mined_block

    def add_existing_block(self, block: Block) -> None:
        prev_block = self.blocks[-1]

        if prev_block.content == 'GENESIS':
            logging.warning('Previous block was genesis. Omitting verification.')
            self.blocks.append(block)

        if prev_block.hash != block.previous_hash:
            raise BlockchainError(f"Block hashes are not equal: {prev_block.hash} != {block.previous_hash}")

        self.blocks.append(block)