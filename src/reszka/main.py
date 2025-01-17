import argparse
import asyncio
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from signal import SIGINT, SIGTERM
import requests
from typing import Any

import uvicorn
from fastapi import FastAPI, Response
from pydantic_core._pydantic_core import to_jsonable_python

from reszka.crypto import Blockchain, POWMiner, Block, CreateBlockRequest, VerifyBlockRequest
from reszka.master import Network, Node, RegisterNodeRequest, BlockchainNetworkError

app = FastAPI()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

miner = POWMiner(3)
blockchain = Blockchain(miner)

current_url: str | None = None
current_port: int | None = None
current_master_node_url: str | None = None
network: Network | None = None
network_key = "abc"


@app.get('/blocks', response_model=list[Block])
async def get_blocks() -> Any:
    return blockchain.blocks


@app.get('/nodes', response_model=list[Node])
async def get_nodes() -> Any:
    return network.nodes


@app.post('/blocks', status_code=201)
async def create_block(create_block_request: CreateBlockRequest) -> Any:
    logger.info("Mining block.")
    mined_block = blockchain.add_block(create_block_request)
    logger.info("Adding mined block to rest of the network.")
    _add_existing_block_to_api(mined_block)
    return {'status': 'adding'}


@app.post('/nodes', status_code=201)
async def register_node(register_node_request: RegisterNodeRequest, response: Response) -> Any:
    logger.info("Adding node.")
    if network is None:
        response.status_code = 502
        return {'status': 'not_master_node'}

    network.register_node(register_node_request.node, register_node_request.key)
    return {'status': 'adding'}


@app.post("/existing", status_code=201)
async def add_existing(verify_block_request: VerifyBlockRequest) -> Any:
    block = verify_block_request.block

    logger.info(f"Adding block: {block.id} from {verify_block_request.source}")

    blockchain.add_existing_block(block)


def _add_existing_block_to_api(block: Block) -> None:
    payload = to_jsonable_python(VerifyBlockRequest(block=block, source=current_url))
    for node in network.nodes:
        req = requests.post(f"{node.url}/existing", json=payload)
        if req.status_code != 201:
            raise BlockchainNetworkError(f"Cannot register block: {req.json()}")

        logger.info(f"Successfuly registered block: {payload} for node: {node.url}")


async def main() -> None:
    await run_server()


async def run_server() -> None:
    config = uvicorn.Config(app, host='0.0.0.0', port=current_port)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-node-url", help="add node to master node",
                        type=str)
    parser.add_argument("--port", help="port to listen on", type=int)
    args = parser.parse_args()

    current_port = args.port
    current_url = f"localhost:{current_port}"

    if args.master_node_url:
        logger.info("Registering the node in master node")
        Network.register_node_in_master(current_url, args.master_node_url, network_key)
    else:
        logger.info("Assuming this is master node")
        network = Network(master_node=Node(url=current_url), nodes=[], key=network_key)

    asyncio.run(main())
