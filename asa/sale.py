from boa.interop.Neo.Blockchain import GetHeight
from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import Get, Put
from boa.builtins import concat
from asa.token import *
from asa.utils.txio import get_asset_attachments
from asa.utils.time import get_now

OnMintTokens = RegisterAction('mintTokens', 'addr_from', 'addr_to', 'amount')
OnRefund = RegisterAction('refund', 'addr_to', 'amount')

SALE_STATUS_KEY = b'sale_status'

LIMITSALE_ROUND = b'limit_sale'
CROWDSALE_ROUND = b'crowd_sale'
SALE_END = b'sale_end'

LIMITSALE_NEO_MIN = 10 # NEO
LIMITSALE_NEO_MAX = 50 # NEO

LIMITSALE_TOKENS_PER_NEO = 600 * 100_000_000 # 600 Tokens/NEO * 10^8 (500*1.2=600)
CROWDSALE_TOKENS_PER_NEO = 500 * 100_000_000 # 500 Tokens/NEO * 10^8

SALE_NOT_STARTED_DETAILS = 'Token sale has not yet started. Please see asuracoin.io for more details.'
LIMITSALE_DETAILS = 'Limit Round: 600 ASA/NEO, 10 NEO minumum, 50 NEO maximum'
SALE_DETAILS = 'Open Round: 500 ASA/NEO'
SALE_ENDED_DETAILS = 'Token sale has ended'

def crowdsale_status(ctx):

    isLimitsale = Get(ctx, SALE_STATUS_KEY) == LIMITSALE_ROUND
    isCrowdsale = Get(ctx, SALE_STATUS_KEY) == CROWDSALE_ROUND

    if isLimitsale or isCrowdsale:
        return True

    return False

def crowdsale_details(ctx):

    if Get(ctx, SALE_STATUS_KEY) == LIMITSALE_ROUND:
        return LIMITSALE_DETAILS

    if Get(ctx, SALE_STATUS_KEY) == CROWDSALE_ROUND:
        return SALE_DETAILS

    if Get(ctx, SALE_STATUS_KEY) == SALE_END:
        return SALE_ENDED_DETAILS

    return SALE_NOT_STARTED_DETAILS

def limitsale_available_amount(ctx):
    """
    Get remaining amount of tokens still available in limit round of crowdsale

    :param ctx:GetContext() used to access contract storage

    :return:int amount of tokens still available in limit round of crowdsale
    """

    if Get(ctx, SALE_STATUS_KEY) != LIMITSALE_ROUND:
        return 0

    max_circulation_limit_round = TOKEN_INITIAL_AMOUNT + TOKEN_LIMITSALE_MAX
    in_circ = Get(ctx, TOKEN_CIRC_KEY)

    return max_circulation_limit_round - in_circ

def crowdsale_available_amount(ctx):
    """
    Get remaining amount of tokens still available in the crowdsale

    :param ctx:GetContext() used to access contract storage

    :return:int amount of tokens still available in the crowdsale
    """

    isLimitsale = Get(ctx, SALE_STATUS_KEY) == LIMITSALE_ROUND
    isCrowdsale = Get(ctx, SALE_STATUS_KEY) == CROWDSALE_ROUND

    if not isLimitsale and not isCrowdsale:
        return 0

    in_circ = Get(ctx, TOKEN_CIRC_KEY)

    return TOKEN_TOTAL_SUPPLY - TOKEN_TEAM_AMOUNT - in_circ

def perform_exchange(ctx):
    """
    Attempt to exchange attached NEO for tokens

    :param ctx:GetContext() used to access contract storage

    :return:bool Whether the exchange was successful
    """

    attachments = get_asset_attachments() # [receiver, sender, neo, gas]
    address = attachments[1]
    neo_amount = attachments[2]

    # calculate the amount of tokens that can be exchanged
    exchange_amount = calculate_exchange_amount(ctx, attachments, False)

    if exchange_amount == 0:
        # This should only happen in the case that there are a lot of TX on the final
        # block before the total amount is reached.  An amount of TX will get through
        # the verification phase because the total amount cannot be updated during that phase
        # because of this, there should be a process in place to manually refund tokens
        if neo_amount > 0:
            OnRefund(address, neo_amount)
        return False

    didMint = mint_tokens(ctx, address, exchange_amount)
    # dispatch mintTokens event
    if didMint:
        OnMintTokens(attachments[0], attachments[1], exchanged_tokens)

    return didMint


def calculate_exchange_amount(ctx, attachments, verify_only):
    """
    Calculate the amount of tokens that can be exchanged

    :param ctx:GetContext() used to access contract storage
    :param attachments:list [receiver, sender, neo, gas]
    :param verify_only:bool if this is the actual exchange, or just a verification

    :return:int Amount of tokens to be exchanged
    """

    address = attachments[1]
    neo_amount = attachments[2]

    if attachments[2] == 0:
       print("no neo attached")
       return 0

    # the following looks up whether an address has been
    # registered with the contract for KYC regulations
    # this is not required for operation of the contract
    if not get_kyc_status(ctx, address):
        return 0

    current_timestamp = get_now()

    # if the sale has not yet started no amount can be exchanged
    if Get(ctx, SALE_STATUS_KEY) == b'':
        print('token sale has not started yet')
        return 0

    current_in_circulation = Get(ctx, TOKEN_CIRC_KEY)

    # if are still in the limit round of the crowdsale
    # ensure only amount abides but limit round rules
    if Get(ctx, SALE_STATUS_KEY) == LIMITSALE_ROUND:
        return calculate_limitsale_amount(ctx, address, neo_amount, current_in_circulation, verify_only)

    # calculate amount if still in crowdsale timeline
    if Get(ctx, SALE_STATUS_KEY) == CROWDSALE_ROUND:
        return calculate_crowdsale_amount(neo_amount, current_in_circulation)

    return 0

def calculate_limitsale_amount(ctx, address, neo_amount, current_in_circulation, verify_only):
    """
    Calculate the amount of tokens that can be exchanged in limit round

    :param ctx:GetContext() used to access contract storage
    :param address: address to calculate amount for
    :param neo_amount:int amount of neo attached for exchange
    :param current_in_circulation:int amount tokens in circulation
    :param verify_only:bool if this is the actual exchange, or just a verification

    :return:int Amount of tokens to be exchanged
    """

    print('in limited round of crowd sale')
    limit_round_key = concat(address, LIMITSALE_ROUND_KEY)
    amount_exchanged = Get(ctx, limit_round_key)

    exchange_amount = neo_amount * LIMITSALE_TOKENS_PER_NEO
    max_circulation_limit_round = TOKEN_INITIAL_AMOUNT + TOKEN_LIMITSALE_MAX
    new_circulation = current_in_circulation + exchange_amount
    isBelowMaxCirculation = new_circulation < max_circulation_limit_round

    new_exchanged_neo_amount = neo_amount + amount_exchanged
    isAboveMinExchange = LIMITSALE_NEO_MIN < new_exchanged_neo_amount
    isBelowMaxExchange = new_exchanged_neo_amount < LIMITSALE_NEO_MAX

    if isBelowMaxCirculation and isAboveMinExchange and isBelowMaxExchange:
        if not verify_only:
            Put(ctx, limit_round_key, new_exchanged_neo_amount)
        return exchange_amount

    return 0


def calculate_crowdsale_amount(neo_amount, current_in_circulation):
    """
    Calculate the amount of tokens that can be exchanged in general crowdsale

    :param neo_amount:int amount of neo attached for exchange
    :param current_in_circulation:int amount tokens in circulation

    :return:int Amount of tokens to be exchanged
    """

    print('in open round of crowd sale')
    exchange_amount = neo_amount * CROWDSALE_TOKENS_PER_NEO
    max_circulation_crowdsale = TOKEN_TOTAL_SUPPLY - TOKEN_TEAM_AMOUNT
    new_circulation = current_in_circulation + exchange_amount
    isBelowMaxCirculation = new_circulation < max_circulation_crowdsale

    if isBelowMaxCirculation:
        return exchange_amount

    return 0
