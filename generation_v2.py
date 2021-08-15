# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 18:42:22 2021

@author: Danny1

https://threadreaderapp.com/thread/1408091355105087488.html
with thanks to @vee for the sharing and inspiration
and @squeebo for code review (it was even worse before)

"""


from __future__ import print_function
import pandas as pd
import numpy as np
from PIL import Image, ImageSequence
import os
import ast
import json

import keystore as k # create keystore.py fetching all api and metamask keys


paths = []

path = os.path.join(k.ROOT,'opensea_creatures')

# requires opensea creatures tutorial image folders stored in above path
# additionally add backgrounds (basic filled images of the same size as other files) - or remove lines below

# set folder paths to images sequencd from background to foreground
paths.append(os.path.join(path,"img/background/"))
paths.append(os.path.join(path,"img/accessory/"))
paths.append(os.path.join(path,"img/bases/"))
paths.append(os.path.join(path,"img/eyes/"))
paths.append(os.path.join(path,"img/mouths/"))

# trait names in order of sequence & reused for trait names
layer = ['background', 'accessory', 'bases', 'eyes', 'mouths']

# # read folders for .png filenames and create table to set weights
# # only run when traits are updated/added
# # take the csv and create a table containing <folder>_<filename no extension> | weighting
# # example: background_blue | 20 sets a relative weight of 20 to the blue backround
# # (anything weighted 10 will appear half as often while 40 would appear 2x more)
# files = []
# folders = []

# for (fpath, dirnames, filenames) in os.walk(path + '/img'):
#     folders.extend(os.path.join(fpath, name) for name in dirnames)
#     files.extend(os.path.join(fpath, name) for name in filenames)
# dataframe = pd.DataFrame(files)
# dataframe = dataframe[dataframe[0].str.endswith('.png')]
# dataframe.to_csv(path + "\data1.csv")

# load images from folders
layers = [[]]

# read weights from a table (built in steps above)
df = pd.read_excel(path + '/weights.xlsx')

# loop through each folder and get the path to each image file and store with the appropriate trait
# also store a text code 'attribute' used for testing uniqueness later
# and json dictionary 'trait used to build the metadata file
for i in range(len(paths)):
    files = os.listdir(paths[i])
    layers.append([])
    for img_name in files:
        layers[i].append([(paths[i] + img_name),img_name.replace(".png","")])
    layers[i] = pd.DataFrame(layers[i], columns = ['image',layer[i]])
    layers[i]['attribute'] = layer[i] + '_' + layers[i][layer[i]]
    layers[i]['trait'] = '{\'' + layer[i] + '\': \'' + layers[i][layer[i]] + '\'}'
    layers[i] = layers[i].merge(df, how='left', on='attribute')
layers.pop(len(paths))
    
# loop through desired number mint generations

mint_IDs = []
minted_dicts = []
minted_pngs = []

while (len(mint_IDs) < 5):
    
    rand_img = []
    test_mint = mint_IDs.copy()

    # select random components
    r_code = ''
    r_dict = {}

    for i in range(len(paths)):
        rand_img.append(layers[i].sample(n=1, weights = layers[i]['weight']))
        r_code = r_code + '__' + rand_img[i]['attribute'].iloc[0]
        r_dict.update(ast.literal_eval(rand_img[i]['trait'].iloc[0]))
        
    # verify selected combination is not a duplicate (restart if duplicate combo)
    
    test_mint.append(r_code)
    flag = len(set(test_mint)) == len(test_mint)
    if (flag):
        mint_IDs = test_mint.copy()
        minted_dicts.append(r_dict)
    else:
        continue
    
    # convert/store valid images
    
    img_build = []
    
    for i in range(len(rand_img)):
        img_build.append(Image.open(rand_img[i]['image'].iloc[0]))
        img_build[i] = img_build[i].convert('RGBA')
   
    # generate randomly selected image
    
    new_img = img_build[0]
    
    for i in range (len(rand_img)):
        new_img = Image.alpha_composite(new_img, img_build[i])
    
    # store local paths for ipfs upload
    minted_pngs.append(path + "/output/mint" + str(len(mint_IDs)).zfill(3)+'.png')
    
    new_img.save(minted_pngs[len(mint_IDs)-1])
    
    
    # new_img.show()


'''
#######################################

# SELECT ANIMATION
# ASSEMBLE ANIMATION FRAMES

#######################################
'''

    # incomplete, but contains steps to add in animation behind each image
    
    # transparent_foreground = new_img
    # # transparent_foreground.show()
    # animation = Image.open(path + '\\img\\animated.png')
    # # animation.show()
    
    # frames = []
    # for frame in ImageSequence.Iterator(animation):
    #     frame = frame.copy()
    #     frame = frame.convert('RGBA')
    #     frame = frame.resize(transparent_foreground.size)
    #     frame = Image.alpha_composite(frame,transparent_foreground)
    #     # frame.paste(transparent_foreground, transparent_foreground)
    #     frames.append(frame)
    # frames[0].save(path + '\\output\\mint'+str(len(mint_IDs)).zfill(3)+'.png', save_all=True, append_images=frames[1:])

'''
#######################################
#######################################

# POST Image Files to IPFS

#######################################
'''

import requests
import json

pinata = 'https://api.pinata.cloud'

headers = {
    "pinata_api_key": k.PIN_KEY,
    "pinata_secret_api_key": k.PIN_SECRET,
    }

r_hashes = []

for i in minted_pngs:
    file = {"file":open(i,'rb')}
    # upload & pin file to IPFS, receive hash
    response = requests.post(pinata + '/pinning/pinFileToIPFS', files = file, headers = headers)
    r_hashes.append(response.json()['IpfsHash'])
    
    

'''
#######################################
#######################################

# Add Images to JSON & Upload to IPFS

#######################################
'''


# update dictionaries to json
minted_json = minted_dicts.copy()
r_json_hashes = []

for i in range(len(minted_json)):
    # set item details
    desc = 'Opensea Creatures testing'
    image = 'ipfs://' + r_hashes[i]
    name = 'creature' + str(i+1).zfill(2)

    attributes = []
    for x, y in minted_json[i].items():
        if x == 'lines':
            continue
        attributes.append({"trait_type": x, "value": y})
        
    # minted_json[i] = json.dumps(minted_json[i])
    # minted_json[i] = json.loads('{ "description":' + desc + ', "name":' + name + ', "image":' + image + ', "attributes":' + json.dumps(attributes) + '}')
    minted_json[i] = {"description": desc, "name": name, "image": image,"attributes": attributes}
    # minted_json[i] = json.dumps( minted_json[i] )
    
    # minted_json[i] = json.loads('{ "description":' + desc + ', "name":' + name + ', "attributes":' + json.dumps(attributes) + '}')
    with open(path + '\\output\\mint' + str(i+1).zfill(3) + '.json', 'w') as f:
        json.dump(minted_json[i], f)
        
    # upload & pin file to IPFS, receive hash
    response = requests.post(pinata + '/pinning/pinJSONToIPFS', json = minted_json[i], headers = headers)
    
    r_json_hashes.append(response.json()['IpfsHash'])


    

'''
#######################################
#######################################

# Confirm Uploads and Compute Collection Hash for Provenance

#######################################
'''

# TO DO confirm uploads


# Python program to find SHA256 hash string of a file
import hashlib

prov = ''

for filename in minted_pngs:
    sha256_hash = hashlib.sha256()
    with open(filename,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
        prov = prov + sha256_hash.hexdigest()
        
prov = hashlib.sha256(prov.encode('utf-8')).hexdigest()



'''
#######################################
#######################################
# MINT!!!
#######################################
'''

import json
import os
import time

import requests
from web3 import Web3


path = os.path.join(k.ROOT,'contracts/seaABI.json')

with open(path, 'r') as myfile:
    data=myfile.read()

ABI = data

# connect to provider
w3 = Web3(Web3.HTTPProvider(k.ALCH_KEY))

# set account to owner
owner = k.OWNER
w3.eth.defaultAccount = owner

# connect to contract
contract = w3.eth.contract(address = k.CONTRACT, abi = ABI)

# check contract symbol
contract.functions.symbol().call()

nonce = w3.eth.get_transaction_count(owner)

# loop through items to be minted
for i in r_json_hashes:

    # set award
    receiver = owner
    r_hash = i
    award = {receiver, r_hash, 'ipfs://'+r_hash}
    
    transaction = contract.functions.awardItem(receiver, r_hash, 'ipfs://'+r_hash).buildTransaction()
    
    transaction.update({"nonce": nonce})
        
    signed_tx = w3.eth.account.sign_transaction(transaction, k.TEST_KEY)
    
    w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    count = 0
    ## TO DO
    while nonce == w3.eth.get_transaction_count(receiver) and count < 60:
        time.sleep(1)
        count = count + 1
        # wait until transaction registers

    nonce = w3.eth.get_transaction_count(receiver)