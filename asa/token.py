from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Storage import Get, Put
from asa.time import get_now

TOKEN_NAME = 'Asura World Coin'
TOKEN_SYMBOL = 'ASA'
TOKEN_DECIMALS = 8

TOKEN_OWNER = b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9'

TOKEN_CIRC_KEY = b'in_circulation'

TOKEN_TOTAL_SUPPLY = 1_000_000_000 * 100_000_000 # 1 billion * 10^8

TOKEN_PRESALE_AMOUNT = 300_000_000 * 100_000_000 # 300 million * 10^8

TOKEN_CROWDSALE_AMOUNT = 350_000_000 * 100_000_000 # 350 million * 10^8

# allocation for asura world team
# to be locked for 12 months
TOKEN_TEAM_AMOUNT = 100_000_000 * 100_000_000 # 100 million * 10^8
TOKEN_TEAM_LOCKUP_END_TIMESTAMP = 1557360000 # GMT - May 9, 2019 12:00:00 AM
TOKEN_TEAM_DISTRO_KEY = b'team_tokens'

# bounty program and airdrops
# sent to owner wallet on contract deploy
TOKEN_INITIAL_AMOUNT = 250_000_000 * 100_000_000

def deploy():
    if not CheckWitness(TOKEN_OWNER):
        print("Must be owner to deploy")
        return False

    if not Get(ctx, 'initialized'):
        Put(ctx, 'initialized', 1)
        Put(ctx, TOKEN_OWNER, TOKEN_INITIAL_AMOUNT)
        return add_to_circulation(ctx, TOKEN_INITIAL_AMOUNT)

    return False


def crowdsale_available_amount(ctx):

    in_circ = Get(ctx, TOKEN_CIRC_KEY)

    available = TOKEN_TOTAL_SUPPLY - in_circ

    return available


def get_circulation(ctx):
    return Get(ctx, TOKEN_CIRC_KEY)


def add_to_circulation(ctx, amount):

    current_supply = Get(ctx, TOKEN_CIRC_KEY)

    current_supply += amount
    Put(ctx, TOKEN_CIRC_KEY, current_supply)
    return True


def mint_tokens(ctx, address, amount):
    # lookup the current balance of the address
    current_balance = Get(ctx, address)

    # add it to the the exchanged tokens and persist in storage
    new_total = amount + current_balance
    Put(ctx, address, new_total)

    # update the in circulation amount
    result = add_to_circulation(ctx, amount)

    return True


def transfer_team_tokens(ctx, args):
    if not CheckWitness(TOKEN_OWNER):
        print('Must be owner to deploy')
        return False

    if get_now() < TOKEN_TEAM_LOCKUP_END_TIMESTAMP:
        print('Team token lockup period has not yet ended')
        return False

    if len(args) != 2:
        print('Not correct amount of arguments, expected 2')
        return False

    address = args[0]
    amount = args[1]

    if len(address) != 20:
        print('Not a valid address length')
        return False
    if amount <= 0:
        print('No tokens to transfer')
        return False

    team_tokens_distributed = Get(ctx, TOKEN_TEAM_DISTRO_KEY)
    team_tokens_distributed += amount

    if team_tokens_distributed > TOKEN_TEAM_AMOUNT:
        print("can't exceed TOKEN_TEAM_AMOUNT")
        return False

    Put(ctx, TOKEN_TEAM_DISTRO_KEY, team_tokens_distributed)

    didMint = mint_tokens(ctx, address, amount)

    return didMint
