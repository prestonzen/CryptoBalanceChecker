import json
import csv
import asyncio
from web3 import Web3, HTTPProvider
from mnemonic import Mnemonic
from eth_account import Account
from bip_utils import Bip44, Bip39SeedGenerator, Bip44Coins, Bip44Changes

# Initialize a Web3 instance with async provider
w3 = Web3(HTTPProvider('https://mainnet.infura.io/v3/70a8ace7afb54c7fa0de6504c36be15b', {"timeout": 60}))

app_version = 7  # Incremented from previous version

def derive_bip44_private_key(seed_bytes):
    """Derive private key using BIP-44 standard."""
    bip_obj_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip_obj_acc = bip_obj_mst.Purpose().Coin().Account(0)
    bip_obj_chain = bip_obj_acc.Change(Bip44Changes.CHAIN_EXT)
    bip_obj_addr = bip_obj_chain.AddressIndex(0)
    return bip_obj_addr.PrivateKey().ToBytes()

def derive_bip39_private_key(seed_phrase):
    """Derive private key using BIP-39 standard."""
    seed_bytes = Bip39SeedGenerator(seed_phrase).Generate()
    return derive_bip44_private_key(seed_bytes)

async def check_transaction_activity(address):
    """Asynchronously check transaction activity for a given Ethereum address."""
    tx_count = await asyncio.to_thread(w3.eth.getTransactionCount, address)
    return tx_count > 0

def import_txt(filepath):
    """Import seed phrases from a .txt file."""
    with open(filepath, 'r') as file:
        return [line.strip() for line in file]

def import_csv(filepath):
    """Import seed phrases from a .csv file."""
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        return [",".join(row).replace(",", " ").strip() for row in reader]

def import_json(filepath):
    """Import seed phrases from a .json file."""
    with open(filepath, 'r') as file:
        data = json.load(file)
        return list(data.values())

async def process_seed(seed):
    """Asynchronously process a seed phrase to derive private keys using multiple BIP standards, fetch associated addresses and balances, and check transaction activity."""
    seed_bytes = Mnemonic("english").ToSeed(seed)
    
    for method, bip_func in [("BIP-39", derive_bip39_private_key), 
                             ("BIP-44", derive_bip44_private_key)]:
        private_key = bip_func(seed_bytes)
        account = Account.from_key(private_key)
        address = account.address

        # If no transaction activity, skip further processing for this BIP type
        has_activity = await check_transaction_activity(address)
        if not has_activity:
            continue

        balance_wei = w3.eth.getBalance(address)
        balance_eth = w3.fromWei(balance_wei, 'ether')
        print(f"[{method}] Address: {address} has a balance of {balance_eth} ETH. Transaction activity: {'Yes' if has_activity else 'No'}")

seed_phrases = []

# Importing seed phrases from .txt, .csv, and .json files
seed_phrases.extend(import_txt("seedPhrases.txt"))
seed_phrases.extend(import_csv("seedPhrases.csv"))
seed_phrases.extend(import_json("seedPhrases.json"))

# Running the asynchronous processing
loop = asyncio.get_event_loop()
tasks = [process_seed(seed) for seed in seed_phrases]
loop.run_until_complete(asyncio.gather(*tasks))
