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
CROWDSALE_BONUS_ROUND = b'crowd_sale_bonus'
CROWDSALE_ROUND = b'crowd_sale'
SALE_END = b'sale_end'
SALE_PAUSED = b'sale_paused'

LIMITSALE_NEO_MIN = 1 * 100_000_000 # NEO * 10^8
LIMITSALE_NEO_MAX = 50 * 100_000_000 # NEO * 10^8

CROWDSALE_NEO_MIN = 1 * 100_000_000 # NEO * 10^8
CROWDSALE_NEO_MAX = 500 * 100_000_000 # NEO * 10^8

CROWDSALE_LARGE_CONTRIBUTION = 100 * 100_000_000 # NEO * 10^8

LIMITSALE_TOKENS_PER_NEO = 6000 # 6000 Tokens/NEO (5000*1.2=6000)
CROWDSALE_BONUS_ROUND_TOKENS_PER_NEO = 5750 # 5750 Tokens/NEO (5000*1.15=5750)
CROWDSALE_LARGE_CONTRIBUTION_TOKENS_PER_NEO = 5500 # 5500 Tokens/NEO (5000*1.1=5500)
CROWDSALE_TOKENS_PER_NEO = 5000 # 5000 Tokens/NEO

SALE_NOT_STARTED_DETAILS = 'Token sale has not yet started. Please see asuracoin.io for more details.'
LIMITSALE_DETAILS = 'Limit Round: 6000 ASA/NEO, 1 NEO minumum, 50 NEO maximum'
BONUS_SALE_DETAILS = 'Crowdsale Bonus Round: 5750 ASA/NEO, 1 NEO minumum, 500 NEO maximum'
SALE_DETAILS = 'General Crowdsale Round: 5000 ASA/NEO, 5500 ASA/NEO is single contribution of 100 NEO or more, 500 NEO maximum'
SALE_ENDED_DETAILS = 'Token sale has ended'
SALE_PAUSED_DETAILS = 'Token sale has be paused by contract owner'

def crowdsale_status(ctx):
    """
    Get the status of the tokensale

    :param ctx:GetContext() used to access contract storage

    :return:bool whether or not the sale is active
    """

    saleStatus = Get(ctx, SALE_STATUS_KEY)

    isLimitsale = saleStatus == LIMITSALE_ROUND
    isCrowdsaleBonus = saleStatus == CROWDSALE_BONUS_ROUND
    isCrowdsale = saleStatus == CROWDSALE_ROUND

    if isLimitsale or isCrowdsaleBonus or isCrowdsale:
        return True

    return False

def crowdsale_details(ctx):
    """
    Get details about the crowdsale status

    :param ctx:GetContext() used to access contract storage

    :return:string details about the crowdsale status, specific to round
    """

    saleStatus = Get(ctx, SALE_STATUS_KEY)

    if saleStatus == LIMITSALE_ROUND:
        return LIMITSALE_DETAILS

    if saleStatus == CROWDSALE_BONUS_ROUND:
        return BONUS_SALE_DETAILS

    if saleStatus == CROWDSALE_ROUND:
        return SALE_DETAILS

    if saleStatus == SALE_END:
        return SALE_ENDED_DETAILS

    if saleStatus == SALE_PAUSED:
        return SALE_PAUSED_DETAILS

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

    saleStatus = Get(ctx, SALE_STATUS_KEY)

    isLimitsale = saleStatus == LIMITSALE_ROUND
    isCrowdsaleBonus = saleStatus == CROWDSALE_BONUS_ROUND
    isCrowdsale = saleStatus == CROWDSALE_ROUND
    isSalePaused = saleStatus == SALE_PAUSED

    if not isLimitsale and not isCrowdsaleBonus and not isCrowdsale and not isSalePaused:
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
        OnMintTokens(attachments[0], attachments[1], didMint)

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
    saleStatus = Get(ctx, SALE_STATUS_KEY)

    # if the sale has not yet started no amount can be exchanged
    if saleStatus == b'':
        print('token sale has not started yet')
        return 0

    # if the token sale is paused dont allow any exchanges
    if saleStatus == SALE_PAUSED:
        print('token sale has be paused')
        return 0

    current_in_circulation = Get(ctx, TOKEN_CIRC_KEY)

    # if are still in the limit round of the crowdsale
    # ensure only amount abides but limit round rules
    if saleStatus == LIMITSALE_ROUND:
        return calculate_limitsale_amount(ctx, address, neo_amount, current_in_circulation, verify_only)

    if saleStatus == CROWDSALE_BONUS_ROUND:
        return calculate_crowdsale_bonus_round_amount(ctx, address, neo_amount, current_in_circulation, verify_only)

    # calculate amount if still in crowdsale timeline
    if saleStatus == CROWDSALE_ROUND:
        return calculate_crowdsale_amount(ctx, address, neo_amount, current_in_circulation, verify_only)

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

    print('in limited round of token sale')
    limit_round_key = concat(LIMITSALE_ROUND, address)
    amount_exchanged = Get(ctx, limit_round_key)

    exchange_amount = neo_amount * LIMITSALE_TOKENS_PER_NEO
    max_circulation_limit_round = TOKEN_INITIAL_AMOUNT + TOKEN_LIMITSALE_MAX
    new_circulation = current_in_circulation + exchange_amount
    isBelowMaxCirculation = new_circulation < max_circulation_limit_round

    new_exchanged_neo_amount = neo_amount + amount_exchanged
    isAboveMinExchange = LIMITSALE_NEO_MIN <= new_exchanged_neo_amount
    isBelowMaxExchange = new_exchanged_neo_amount <= LIMITSALE_NEO_MAX

    if isBelowMaxCirculation and isAboveMinExchange and isBelowMaxExchange:
        if not verify_only:
            Put(ctx, limit_round_key, new_exchanged_neo_amount)
        return exchange_amount

    return 0

def calculate_crowdsale_bonus_round_amount(ctx, address, neo_amount, current_in_circulation, verify_only):
    """
    Calculate the amount of tokens that can be exchanged in bonus round of crowdsale

    :param ctx:GetContext() used to access contract storage
    :param address: address to calculate amount for
    :param neo_amount:int amount of neo attached for exchange
    :param current_in_circulation:int amount tokens in circulation
    :param verify_only:bool if this is the actual exchange, or just a verification

    :return:int Amount of tokens to be exchanged
    """

    print('bonus round of crowd sale')
    crowdsale_round_key = concat(CROWDSALE_ROUND, address)
    amount_exchanged = Get(ctx, crowdsale_round_key)

    exchange_amount = neo_amount * CROWDSALE_BONUS_ROUND_TOKENS_PER_NEO
    max_circulation = TOKEN_TOTAL_SUPPLY - TOKEN_TEAM_AMOUNT
    new_circulation = current_in_circulation + exchange_amount
    isBelowMaxCirculation = new_circulation <= max_circulation

    new_exchanged_neo_amount = neo_amount + amount_exchanged
    isAboveMinExchange = CROWDSALE_NEO_MIN <= new_exchanged_neo_amount
    isBelowMaxExchange = new_exchanged_neo_amount <= CROWDSALE_NEO_MAX

    if isBelowMaxCirculation and isAboveMinExchange and isBelowMaxExchange:
        if not verify_only:
            Put(ctx, crowdsale_round_key, new_exchanged_neo_amount)
        return exchange_amount

    return 0

def calculate_crowdsale_amount(ctx, address, neo_amount, current_in_circulation, verify_only):
    """
    Calculate the amount of tokens that can be exchanged in general crowdsale

    :param ctx:GetContext() used to access contract storage
    :param address: address to calculate amount for
    :param neo_amount:int amount of neo attached for exchange
    :param current_in_circulation:int amount tokens in circulation
    :param verify_only:bool if this is the actual exchange, or just a verification

    :return:int Amount of tokens to be exchanged
    """

    print('general round of crowd sale')
    crowdsale_round_key = concat(CROWDSALE_ROUND, address)
    amount_exchanged = Get(ctx, crowdsale_round_key)

    contribution_rate = CROWDSALE_TOKENS_PER_NEO

    if neo_amount >= CROWDSALE_LARGE_CONTRIBUTION:
        contribution_rate = CROWDSALE_LARGE_CONTRIBUTION_TOKENS_PER_NEO

    exchange_amount = neo_amount * contribution_rate
    max_circulation = TOKEN_TOTAL_SUPPLY - TOKEN_TEAM_AMOUNT
    new_circulation = current_in_circulation + exchange_amount
    isBelowMaxCirculation = new_circulation <= max_circulation

    new_exchanged_neo_amount = neo_amount + amount_exchanged
    isAboveMinExchange = CROWDSALE_NEO_MIN <= new_exchanged_neo_amount
    isBelowMaxExchange = new_exchanged_neo_amount <= CROWDSALE_NEO_MAX

    if isBelowMaxCirculation and isAboveMinExchange and isBelowMaxExchange:
        if not verify_only:
            Put(ctx, crowdsale_round_key, new_exchanged_neo_amount)
        return exchange_amount

    return 0
