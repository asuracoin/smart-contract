from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Storage import *

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


def add_to_circulation(ctx, amount):

    current_supply = Get(ctx, TOKEN_CIRC_KEY)

    current_supply += amount
    Put(ctx, TOKEN_CIRC_KEY, current_supply)
    return True


def get_circulation(ctx):
    return Get(ctx, TOKEN_CIRC_KEY)
