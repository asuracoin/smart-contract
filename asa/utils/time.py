from boa.interop.Neo.Blockchain import GetHeight, GetBlock
from boa.interop.Neo.Block import *

def get_now():
    height = GetHeight()
    current_block = GetBlock(height)
    return current_block.Timestamp
