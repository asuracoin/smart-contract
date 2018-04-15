from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Storage import Get, Put
from asa.utils.time import get_now

TOKEN_NAME = 'Asura World Coin'
TOKEN_SYMBOL = 'ASA'
TOKEN_DECIMALS = 8

TOKEN_OWNER = b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9'

TOKEN_CIRC_KEY = b'in_circulation'
TOKEN_LOCKUP_START_KEY =  b'token_lockup_start'

TOKEN_TOTAL_SUPPLY = 1_000_000_000 * 100_000_000 # 1 billion * 10^8
TOKEN_LIMITSALE_MAX = 300_000_000 * 100_000_000 # 300 million * 10^8

# allocation for asura world team
# to be locked for 12 months
TOKEN_TEAM_AMOUNT = 100_000_000 * 100_000_000 # 100 million * 10^8
TOKEN_TEAM_LOCKUP_PERIOD = 31536000 # 365 days
TOKEN_TEAM_DISTRO_KEY = b'team_tokens'

TOKEN_GROWTH_LOCKUP_PERIOD = 31536000 # 365 days

# bounty program and airdrops
# sent to owner wallet on contract deploy
TOKEN_INITIAL_AMOUNT = 250_000_000 * 100_000_000
TOKEN_INITIALIZED_KEY = b'initialized'

def deploy(ctx):
    """
    Deploys the contract, issues inital tokens

    :param ctx:GetContext() used to access contract storage

    :return:bool Whether the operation was successful
    """

    # Only the contract owner can execute the deploy
    if not CheckWitness(TOKEN_OWNER):
        print("Must be owner to deploy")
        return False

    # Check to make sure the contract hasn't already been deployed
    if not Get(ctx, TOKEN_INITIALIZED_KEY):
        # Mark that the deploy has been executed
        Put(ctx, TOKEN_INITIALIZED_KEY, True)
        # Issue the initial tokens to the contract owner
        Put(ctx, TOKEN_OWNER, TOKEN_INITIAL_AMOUNT)
        # Initialize the tokens in circulation from the initial amount
        return add_to_circulation(ctx, TOKEN_INITIAL_AMOUNT)

    return False


def get_circulation(ctx):
    """
    Get the toal amount of tokens in circulation

    :param ctx:GetContext() used to access contract storage

    :return: int The amount of tokens in circulation
    """

    return Get(ctx, TOKEN_CIRC_KEY)


def add_to_circulation(ctx, amount):
    """
    Add to the toal amount of tokens in circulation

    :param ctx:GetContext() used to access contract storage
    :param amount:int the amount of tokens to add to circulation

    :return:bool Whether the operation was successful
    """

    current_supply = Get(ctx, TOKEN_CIRC_KEY)

    current_supply += amount
    Put(ctx, TOKEN_CIRC_KEY, current_supply)
    return True


def mint_tokens(ctx, address, amount):
    """
    Mint tokens for an address

    :param ctx:GetContext() used to access contract storage
    :param to_address: the address to add the tokens to
    :param amount:int the number of tokens to mint

    :return:bool Whether the operation was successful
    """

    # lookup the current balance of the address
    current_balance = Get(ctx, address)

    # add it to the the exchanged tokens and persist in storage
    new_total = amount + current_balance
    Put(ctx, address, new_total)

    # update the in circulation amount
    return add_to_circulation(ctx, amount)


def transfer_team_tokens(ctx, args):
    """
    Transfer team alloted tokens

    :param ctx:GetContext() used to access contract storage
    :param args:list address and amount to send tokens to

    :return:bool Whether the operation was successful
    """

    # only the contract owner can transfer team tokens
    if not CheckWitness(TOKEN_OWNER):
        print('Must be owner to transfer team tokens')
        return False

    lockup_start = Get(ctx, TOKEN_LOCKUP_START_KEY)

    # team tokens cant be transfered before lockup period has started
    if lockup_start == b'':
        print('Team token lockup period has not yet started')
        return False

    lockup_end = lockup_start + TOKEN_TEAM_LOCKUP_PERIOD

    # team tokens cant be transfered before lockup period is over
    if get_now() < lockup_end:
        print('Team token lockup period has not yet ended')
        return False

    if len(args) != 2:
        print('Not correct amount of arguments, expected 2')
        return False

    # address to send tokens to
    address = args[0]
    # amount of tokens to send
    amount = args[1]

    if len(address) != 20:
        print('Not a valid address length')
        return False
    if amount <= 0:
        print('No tokens to transfer')
        return False

    # get amount of team tokens already distributed
    team_tokens_distributed = Get(ctx, TOKEN_TEAM_DISTRO_KEY)
    team_tokens_distributed += amount

    # check to make sure that the total amount of tokens distributed
    # will not exceed the amount alloted for the team
    if team_tokens_distributed > TOKEN_TEAM_AMOUNT:
        print("can't exceed TOKEN_TEAM_AMOUNT")
        return False

    # update total amount of tokens distributed to team
    Put(ctx, TOKEN_TEAM_DISTRO_KEY, team_tokens_distributed)

    # mint tokens into the team address
    didMint = mint_tokens(ctx, address, amount)

    return didMint

def transfer_growth_tokens(ctx, args):
    """
    Transfer growth alloted tokens

    :param ctx:GetContext() used to access contract storage
    :param args:list address and amount to send tokens to

    :return:bool Whether the operation was successful
    """

    # only the contract owner can transfer team tokens
    if not CheckWitness(TOKEN_OWNER):
        print('Must be owner to transfer growth tokens')
        return False

    lockup_start = Get(ctx, TOKEN_LOCKUP_START_KEY)

    # growth tokens cant be transfered before lockup period has started
    if lockup_start == b'':
        print('Growth token lockup period has not yet started')
        return False

    lockup_end = lockup_start + TOKEN_TEAM_LOCKUP_PERIOD

    # growth tokens cant be transfered before lockup period is over
    if get_now() < lockup_end:
        print('Growth token lockup period has not yet ended')
        return False

    if len(args) != 2:
        print('Not correct amount of arguments, expected 2')
        return False

    # address to send tokens to
    address = args[0]
    # amount of tokens to send
    amount = args[1]

    if len(address) != 20:
        print('Not a valid address length')
        return False
    if amount <= 0:
        print('No tokens to transfer')
        return False

    # get amount of total tokens in circulation
    in_circulation = get_circulation(ctx)

    # get amount of team tokens already distributed
    team_tokens_distributed = Get(ctx, TOKEN_TEAM_DISTRO_KEY)
    team_tokens_remaining = TOKEN_TEAM_AMOUNT - team_tokens_distributed

    # calculate remaining tokens available for growth fund
    growth_tokens_remaining = TOKEN_TOTAL_SUPPLY - team_tokens_remaining - in_circulation

    # check to make sure that the total amount of tokens distributed
    # will not exceed the remaining growth tokens
    if growth_tokens_remaining < amount:
        print("can't exceed TOKEN_TOTAL_SUPPLY")
        return False

    # mint tokens into the team address
    didMint = mint_tokens(ctx, address, amount)

    return didMint
