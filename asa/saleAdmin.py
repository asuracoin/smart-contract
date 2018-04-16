from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Storage import Get, Put
from asa.sale import *
from asa.token import *
from asa.utils.time import get_now

def start_limit_sale(ctx):
    """
    Start the limit round of the token sale

    :param ctx:GetContext() used to access contract storage

    :return:bool Whether starting the round was successful
    """

    if CheckWitness(TOKEN_OWNER):
        # start the limit sale if no sale started
        if Get(ctx, SALE_STATUS_KEY) == b'':
            Put(ctx, SALE_STATUS_KEY, LIMITSALE_ROUND)
            return True

    return False

def start_crowd_sale(ctx):
    """
    Start the crowd round of the token sale

    :param ctx:GetContext() used to access contract storage

    :return:bool Whether starting the round was successful
    """

    if CheckWitness(TOKEN_OWNER):
        # start the crowd sale if limit sale in progress
        if Get(ctx, SALE_STATUS_KEY) == LIMITSALE_ROUND:
            Put(ctx, SALE_STATUS_KEY, CROWDSALE_ROUND)
            return True

    return False

def end_sale(ctx):
    """
    End the token sale, start clock on team tokens unlock

    :param ctx:GetContext() used to access contract storage

    :return:bool Whether starting the sale was successful
    """

    if CheckWitness(TOKEN_OWNER):
        # end the crowd sale if in progress
        if Get(ctx, SALE_STATUS_KEY) == CROWDSALE_ROUND:
            Put(ctx, SALE_STATUS_KEY, SALE_END)
            Put(ctx, TOKEN_LOCKUP_START_KEY, get_now())
            return True

    return False
