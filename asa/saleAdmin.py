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
        Put(ctx, SALE_STATUS_KEY, LIMITSALE_ROUND)
        return True

    return False

def start_bonus_crowd_sale(ctx):
    """
    Start the bonus crowd round of the token sale

    :param ctx:GetContext() used to access contract storage

    :return:bool Whether starting the round was successful
    """

    if CheckWitness(TOKEN_OWNER):
        Put(ctx, SALE_STATUS_KEY, CROWDSALE_BONUS_ROUND)
        return True

    return False

def start_crowd_sale(ctx):
    """
    Start the crowd round of the token sale

    :param ctx:GetContext() used to access contract storage

    :return:bool Whether starting the round was successful
    """

    if CheckWitness(TOKEN_OWNER):
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
        # end the crowd sale, and set team token lockup date
        if Get(ctx, SALE_STATUS_KEY) != b'':
            Put(ctx, SALE_STATUS_KEY, SALE_END)
            if Get(ctx, TOKEN_LOCKUP_START_KEY) == b'':
                Put(ctx, TOKEN_LOCKUP_START_KEY, get_now())
            return True

    return False
