from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import Get, Put, Delete
from boa.builtins import concat
from asa.token import TOKEN_OWNER
from asa.txio import get_asset_attachments

OnInvalidKYCAddress = RegisterAction('invalid_registration', 'address')
OnKYCRegister = RegisterAction('kyc_registration', 'address')
OnKYCUnregister = RegisterAction('kyc_unregistration', 'address')

KYC_KEY = b'kyc_ok'

def kyc_register(ctx, args):

    ok_count = 0

    if CheckWitness(TOKEN_OWNER):
        for address in args:
            if len(address) == 20:
                Put(ctx, concat(KYC_KEY, address), True)
                OnKYCRegister(address)
                ok_count += 1

    return ok_count


def kyc_unregister(ctx, args):

    ok_count = 0

    if CheckWitness(TOKEN_OWNER):

        for address in args:
            if len(address) == 20:
                Delete(ctx, concat(KYC_KEY, address))
                OnKYCRUnregister(address)
                ok_count -= 1

    return ok_count


def kyc_status(ctx, args):

    if len(args) > 0:
        return get_kyc_status(ctx, args[0])

    return False


def get_kyc_status(ctx, address):

    return Get(ctx, concat(KYC_KEY, address))
