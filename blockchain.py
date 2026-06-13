"""
blockchain.py - Custom Blockchain Implementation for E-Voting System
Uses SHA-256 hashing to create an immutable chain of vote records.
"""

import hashlib
import json
from datetime import datetime


class Block:
    """
    Represents a single block in the blockchain.
    Each block stores one vote record.
    """

    def __init__(self, index, timestamp, voter_id_hash, candidate_id, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.voter_id_hash = voter_id_hash      # Hashed voter ID for privacy
        self.candidate_id = candidate_id
        self.previous_hash = previous_hash
        self.current_hash = self.compute_hash()

    def compute_hash(self):
        """
        Computes SHA-256 hash of all block contents.
        Any change to the block data will produce a completely different hash.
        """
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "voter_id_hash": self.voter_id_hash,
            "candidate_id": self.candidate_id,
            "previous_hash": self.previous_hash
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        """Returns block data as a dictionary (useful for JSON serialization)."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "voter_id_hash": self.voter_id_hash,
            "candidate_id": self.candidate_id,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash
        }


class Blockchain:
    """
    Manages the chain of vote blocks.
    Ensures immutability and integrity of all recorded votes.
    """

    def __init__(self):
        self.chain = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        """
        Creates the first block (genesis block) with hardcoded values.
        This block anchors the entire chain.
        """
        genesis = Block(
            index=0,
            timestamp=str(datetime.now()),
            voter_id_hash="GENESIS",
            candidate_id=0,
            previous_hash="0" * 64  # 64 zeros as the genesis previous hash
        )
        self.chain.append(genesis)

    @property
    def last_block(self):
        """Returns the most recently added block."""
        return self.chain[-1]

    @staticmethod
    def hash_voter_id(voter_id):
        """
        Hashes a voter ID using SHA-256 for privacy.
        The original voter ID is never stored in the blockchain.
        """
        return hashlib.sha256(voter_id.encode()).hexdigest()

    def add_vote(self, voter_id, candidate_id):
        """
        Creates a new block for a vote and appends it to the chain.
        Returns the newly created block.
        """
        voter_hash = self.hash_voter_id(voter_id)
        new_block = Block(
            index=len(self.chain),
            timestamp=str(datetime.now()),
            voter_id_hash=voter_hash,
            candidate_id=candidate_id,
            previous_hash=self.last_block.current_hash
        )
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        """
        Validates the entire blockchain by:
        1. Checking each block's hash matches its recomputed hash (no tampering).
        2. Checking each block's previous_hash links correctly to the prior block.
        Returns True if chain is valid, False if any tampering is detected.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Recompute hash and compare
            if current.current_hash != current.compute_hash():
                return False

            # Check linkage
            if current.previous_hash != previous.current_hash:
                return False

        return True

    def get_chain_as_list(self):
        """Returns the entire chain as a list of dictionaries."""
        return [block.to_dict() for block in self.chain]

    def get_chain_length(self):
        """Returns the number of blocks including genesis."""
        return len(self.chain)

    def search_by_hash(self, query_hash):
        """
        Search for a block by its current hash or previous hash.
        Returns the matching block dict or None.
        """
        for block in self.chain:
            if block.current_hash == query_hash or block.previous_hash == query_hash:
                return block.to_dict()
        return None


# Global blockchain instance shared across the application
voting_blockchain = Blockchain()
