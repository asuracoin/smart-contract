from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import Get, Put, Delete
from boa.builtins import concat
from asa.token import TOKEN_OWNER
from asa.utils.txio import get_asset_attachments

OnKYCRegister = RegisterAction('kycRegister', 'address')
OnKycDeregister = RegisterAction('kycDeregister', 'address')

KYC_KEY = b'kyc_ok'

def kyc_register(ctx, args):
    """
    Register a list of addresses for KYC

    :param ctx:GetContext() used to access contract storage
    :param args:list a list of addresses to register

    :return:int The number of addresses registered for KYC
    """

    ok_count = 0

    if CheckWitness(TOKEN_OWNER):
        for address in args:
            # validate the address is 20 bytes
            if len(address) == 20:
                Put(ctx, concat(KYC_KEY, address), True)
                OnKYCRegister(address)
                ok_count += 1

    return ok_count


def kyc_deregister(ctx, args):
    """
    Deregister a list of addresses from KYC

    :param ctx:GetContext() used to access contract storage
    :param args:list a list of addresses to deregister
    
    :return:int The number of addresses deregistered from KYC
    """

    ok_count = 0

    if CheckWitness(TOKEN_OWNER):

        for address in args:
            if len(address) == 20:
                Delete(ctx, concat(KYC_KEY, address))
                OnKycDeregister(address)
                ok_count += 1

    return ok_count


def kyc_status(ctx, args):
    """
    Gets the KYC Status of an address

    :param ctx:GetContext() used to access contract storage
    :param args:list contains address to lookup

    :return:bool Returns the kyc status of an address
    """

    if len(args) > 0:
        return get_kyc_status(ctx, args[0])

    return False


def get_kyc_status(ctx, address):
    """
    Looks up the KYC status of an address

    :param ctx:GetContext() used to access contract storage
    :param address:bytearray The address to lookup

    :return:bool KYC Status of address
    """

    return Get(ctx, concat(KYC_KEY, address))
