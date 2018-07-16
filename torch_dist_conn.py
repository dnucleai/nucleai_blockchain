import os
import torch
import torch.distributed as dist
from torch.multiprocessing import Process
from web3.auto.infura import w3 # Should work without Infura API key
# Otherwise, obtain a key and export INFURA_API_KEY=...


# Mostly adapted from code at https://pytorch.org/tutorials/intermediate/dist_tuto.html
# torch.distributed API documentation: https://pytorch.org/docs/stable/distributed.html
# web3 documentation (used to retreive ethereum blockchain data): 
# https://web3py.readthedocs.io/en/stable/quickstart.html


def run(rank, size):
    """ Distributed function """
    tensor = torch.tensor([0]*68)
    copy = torch.tensor([0]*68)
    # tensor = torch.zeros(68) <-- this produces a size mismatch when receiving for some reason
    if rank == 0:
        # Retrieving ethereum block data and wrapping it in a tensor
        block_data = w3.eth.getBlock('latest')

        # Convert the hash string to ASCII so that the tensor can encode it (No strings)
        ascii_hash = [ord(c) for c in block_data.hash.hex()]
        print("Original hash: ", block_data.hash.hex())
        tensor = torch.tensor([block_data.number, block_data.timestamp] + ascii_hash)

        # Send the tensor to process 1
        dist.send(tensor=tensor, dst=1)
        
        # Testing that rank 1 sends back equivalent tensor as confirmation
        dist.recv(tensor=copy, src=1)
        print("Sent and received tensors at rank 0 are the same: ", torch.equal(tensor, copy))
    else:
        # Receive tensor from process 0
        dist.recv(tensor=tensor, src=0)

        dist.send(tensor=tensor, dst=0)

    print('Rank ', rank, ' has block number: ', tensor[0].item())
    print('Rank ', rank, ' has timestamp: ', tensor[1].item())
    hash_str = ''.join(chr(i) for i in tensor[2:])
    print('Rank ', rank, ' has hash: ', hash_str)

def init_processes(rank, size, fn, backend='tcp'):
    """ Initialize the distributed environment. """
    # These environment variables must be set on all machines running distributed code
    # MASTER_ADDR and MASTER_PORT should be set to those of the rank 0 machine
    os.environ['MASTER_ADDR'] = '127.0.0.1'
    os.environ['MASTER_PORT'] = '29500'
    # RANK and WORLD_SIZE must also be set if not passed in here
    dist.init_process_group(backend, rank=rank, world_size=size)
    fn(rank, size)


if __name__ == "__main__":
    size = 2
    processes = []
    for rank in range(size):
        p = Process(target=init_processes, args=(rank, size, run))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()