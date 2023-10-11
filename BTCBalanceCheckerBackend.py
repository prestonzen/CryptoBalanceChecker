import os
import httpx
import asyncio
import aiofiles.os
from enum import Enum
from datetime import datetime
from colorama import Fore, Back, Style

class FileType(Enum):
    JSON_ARRAY = 1
    CSV = 2

MAX_ADDRESSES_PER_REQUEST = 45

async def doCheck(path, output, type, continuefrom):
    for input in os.listdir(path):
        f = os.path.join(path, input)
        async with aiofiles.open(f, 'r') as file:
            if type == FileType.CSV:
                content = await file.read()
                lines = content.splitlines()
                for line in lines:
                    keys = line.split(',')
                    try:
                        start_idx = keys.index(continuefrom)
                    except:
                        start_idx = 0
                    
                    for idx in range(start_idx, len(keys), MAX_ADDRESSES_PER_REQUEST):
                        address_batch = keys[idx:idx+MAX_ADDRESSES_PER_REQUEST]
                        batch_str = "|".join(address for address in address_batch if len(address) == 34)
                        await process_key_batch(address_batch=batch_str, url=url, network=net, file=f, start_idx=idx, name=fname, winname=output)
            elif type == FileType.JSON_ARRAY:
                print('WIP')
            else:
                print('no')

async def process_key_batch(address_batch, url, network, file, start_idx, name, winname):
    res = await checkBitcoin(url=url, network=network, address=address_batch, api_key="")
    await writeBatchResponse(res, file=file, network=network, address_batch=address_batch, name=name, winname=winname, start_idx=start_idx)
    #start_idx += 1
    # Assuming you will handle the response for all addresses in the batch here
    # The writeResponse function would also need adjustments to handle batched responses

async def process_key(key, url, network, file, indice, name, winname):
    if len(key) == 34:
        res = await checkBitcoin(url=url, network=network, address=key, api_key="")
        await writeResponse(res, file=file, network=network, address=key, name=name, winname=winname, index=indice)
        indice += 1

async def checkBitcoin(url, network, address, api_key):
    url = url.replace('{network}', network)
    url = url.replace('{address}', address)
    url = url.replace('{api_key}', api_key)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            #response.raise_for_status()
        except httpx.ReadTimeout as exc:
            print(f"HTTP Exception for {exc.request.url} - {exc}")
        except Exception as e:
            print(f"IT WENT WRONG, here's why - {e}")

    return response

async def writeBatchResponse(res, file, network, address_batch, name, winname, start_idx):
    if res.status_code != 200:
        print(f'{Fore.RED}{Back.BLACK} Error for batch starting at index {start_idx} in {file} {Fore.RESET}{Back.RESET}')
        return

    data = res.json()

    for idx, address in enumerate(address_batch.split('|')):
        obj = data.get(address)
        if not obj:
            continue

        balance = obj.get('final_balance')
        log = f'[{start_idx + idx}] Network: {network}, Address: {address}, Code: {res.status_code}, Balance: {balance}'

        if balance == 0 or balance == 'None':
            print(f'{Fore.RED}{Back.BLACK} {log} {Fore.RESET}{Back.RESET}')
            async with aiofiles.open(f'log/{name}', 'a') as file:
                await file.write(f'{log}\n')
        elif balance != 'Error' or balance != 'None':
            print(f'{Fore.YELLOW}{Back.BLACK} {log} {Fore.RESET}{Back.RESET}')
            async with aiofiles.open(f'{winname}', 'a') as out_file:
                await out_file.write(f'{log}\n')

async def writeResponse(res, file, network, address, name, winname, index):
    if res.status_code != 200:
        balance = 'Error'
    else:
        data = res.json()
        obj = data.get(f'{address}')
        balance = obj.get('final_balance')
    
    log = f'[{index}] Network: {network}, Address: {address}, Code: {res.status_code}, Balance: {balance}'
    async with aiofiles.open(f'log/{name}', 'w') as file:
        if balance == 0 or balance == 'None':
            print(f'{Fore.RED}{Back.BLACK} {log} {Fore.RESET}{Back.RESET}')
            await file.write(f'{log}\n')
        elif balance != 'Error' or balance != 'None':
            print(f'{Fore.YELLOW}{Back.BLACK} {log} {Fore.RESET}{Back.RESET}')
            async with aiofiles.open(f'{winname}', 'r') as file:
                content = await file.read()
                if address not in content:
                    async with aiofiles.open(f'{winname}', 'a') as out_file:
                        await out_file.write(f'{log}\n')

def statisticalize(path, output, time):
    lenwins = 0
    lenlosses = 0
    for file in os.listdir(path):
        filepath = os.path.join(path + file)
        losses = open(filepath, 'r')
        lenlosses = lenlosses + len(losses.readlines())
        print(f'file {filepath} len {len(losses.readlines())}')
        losses.close()
    
    wins = open(output, 'r')
    lenwins += len(wins.readlines())
    wins.close()

    errors = open('errors.log', 'r')
    errorlen = (errors.readlines())
    errors.close()

    starttime = time
    nowtime = datetime.now().strftime("%H:%M:%S")

    with open('statistics.txt', 'w') as file:
        log = f'''
-----------------------------------------------------
#{len(open("statistics.txt", "r").readlines()) / 3} 
Started {starttime}
Ended at {nowtime}
Found {lenwins}/{lenlosses} 
        '''
        print(log)
        file.write(log + '\n')
        file.close()

if __name__ == "__main__":
    net = 'BTC'
    url = 'https://blockchain.info/balance?active={address}'
    
    tolog = ['final_balance', 'n_tx', 'total_received']

    current_time = datetime.now().strftime("%H:%M:%S")

    fname = f'{net}_{current_time}'
    winname = f'WINS.log'

    path = './input/'
    logpath = './log/'
    continuefrom = '' # '17HQDqBgYdVaT1jf9EENUMosZvLLmRRYBE'

    # FileType.CSV 
    count = asyncio.run(doCheck(path, winname, FileType.CSV, continuefrom))
    statisticalize(logpath, winname, current_time)