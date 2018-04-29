# Asura World Coin
This is the smart contract code for the Asura World token Asura Coin (ASA)
- NEP5 methods
- Name: Asura Coin
- Symbol: ASA
- Total Supply: 1,000,000,000
- Decimals: 8
- Initial Amount: 250,000,000
- Limitsale
  - Max: 300,000,000
  - Exchange rate: Base rate + 20% bonus
  - Min per KYC: 1 NEO
  - Max per KYC: 50 NEO
- Crowdsale
  - Max: 350,000,000 + unsold tokens from limitsale
  - Exchange rates
    - 1st hour: Base rate + 15% bonus
    - General +100 NEO: Base rate + 10%
    - General: Base rate
  - Min per KYC: 1 NEO
  - Max per KYC: 500 NEO
- Team lockup
  - 100,000,000
  - Lockup duration: 12 months from end of crowdsale
- Remainder of tokens from crowdsale
  - Lockup duration: 12 months from end of crowdsale

## Setup
- Clone neo-python repo to local computer
- Install dependencies
- Open prompt for specific network
  - Private net
  - Test net
  - Main net
- Wait for all blocks to sync with latest block on specified network
  - Please note, for test and main net this will take many hours. Do well in advance.
- Open wallet in neo-python prompt
- Confirm this is the correct wallet for the network you want to deploy
  - Wallet should have enough funds to deploy contract on that network (500 GAS)
- Update contract file `token.py` field `TOKEN_OWNER` with your wallet address.
  - This is very important as this address will be the main admin address for your contract

## Deploy contract
- Locate the prebuilt `avm` file included in this repo, as it was compiled with a tested version of neo-python
  - If you would like to compile the contract yourself:
    - Open the neo-python prompt
    - Run command `build <./~~RELATIVE_PATH~~/asa-ico.py>`
    - `avm` file should be located in same directory as the `asa-ico.py` file
- Open the neo-python prompt and open contract admin wallet with 500 GAS
- Run command `import contract <./~~RELATIVE_PATH~~/asa-ico.py> 0710 05 True False`
  - When prompted enter the details about your contract like the Name and Description
  - You will then be prompted for your password for the wallet
  - Upon entering, you will ge a success confirmation, and the contact will be available on the next block
  - Upon success, the contract hash will be returned by the neo-python prompt
    - Copy this hash as it will be used for ALL calls to your contract


## Initialize Contract
- First confirm that the contract is available my running one of the read methods
  - `testinvoke <CONTRACT_HASH> name []`
  - Should return `Asura World Coin`
  - No need to enter password for read invokes, just hit return
- Initialize the contract by issuing the first tokens to the owner wallet
  - `testinvoke <CONTRACT_HASH> deploy []`
  - When propted for your password enter it, and wait for the next block
  - Confirm deployment by checking balance of owner wallet for initial tokens
    - `testinvoke <CONTRACT_HASH> balanceOf ['<TOKEN_OWNER_ADDRESS>']`
    - Should return balance of `250,000,000`
    - No need to enter password for read invokes, just hit return

## KYC Management
#### Register KYC Addresses
- Run command `testinvoke <CONTRACT_HASH> kycRegister ['<ADDRESS_1>','<ADDRESS_2>',...,'<ADDRESS_16>']`
  - Up to 16 addresses in a single call
  - Count will be returned to validate number of addresses registered
  - Enter wallet password after executing command
  - Wait for next block to confirm address registrations

#### Check KYC Status
- To check if an address has already been registered for KYC
- Run read command
  - `testinvoke <CONTRACT_HASH> kycStatus ['<ADDRESS>']`

#### Deregister KYC Addresses
- If for any reason you need to de-register addresses from KYC
- Run command `testinvoke <CONTRACT_HASH> kycDeregister ['<ADDRESS_1>','<ADDRESS_2>',...,'<ADDRESS_16>']`
  - Up to 16 addresses in a single call
  - Count will be returned to validate number of addresses de-registered
  - Enter wallet password after executing command
  - Wait for next block to confirm address registrations

## Token Sale Management
Please note that the contract is strict about executing the different rounds in a specific order

#### Start the first limit round
- Can only be started is no other sale as been started
- Run command `testinvoke <CONTRACT_HASH> startLimitSale []`
- Enter wallet password to submit invoke
- Upon next block limit sale will start
- Confirm sale has started
  - Run read command `testinvoke <CONTRACT_HASH> saleDetails []`
  - Should return message starting with `Limit Round...`

#### Start the crowdsale bonus round
- This will be the first hour of the crowdsale, as controlled by the admin
- Can only be started if the limit sale is in progress
- Run command `testinvoke <CONTRACT_HASH> startBonusCrowdSale []`
- Enter wallet password to submit invoke
- Upon next block crowdsale bonus round will start
- Confirm sale has started
  - Run read command `testinvoke <CONTRACT_HASH> saleDetails []`
  - Should return message starting with `Crowdsale Bonus Round...`

#### Start the open crowdsale round
- This will be the general crowdsale
- Can only be started if the crowd sale bonus round is in progress
- Run command `testinvoke <CONTRACT_HASH> startCrowdSale []`
- Enter wallet password to submit invoke
- Upon next block general crowdsale round will start
- Confirm sale has started
  - Run read command `testinvoke <CONTRACT_HASH> saleDetails []`
  - Should return message starting with `General Crowdsale Round...`

#### End the token sale
- This will end the token sale
- Can only be executed if the general crowd sale round is in progress
- Run command `testinvoke <CONTRACT_HASH> endSale []`
- Enter wallet password to submit invoke
- Upon next block the token sale will have ended
- Confirm sale has ended
  - Run read command `testinvoke <CONTRACT_HASH> saleDetails []`
  - Should return message `Token sale has ended`

## Team tokens
- These will be locked up from distribution for 12 months starting from the timestamp recorded on token sale end
- Once the 12 month lock up is completed, you can sent funds from the token pool to any address from the token owner address
  - Run command `testinvoke <CONTRACT_HASH> transferTeamTokens ['<ADDRESS>',<AMOUNT>]`
    - Keep in mind amount needs to be times 10^8, since the token has 8 decimal places
      - An amount of 1 will transfer 0.00000001 ASA
    - Please remember to not have any spaces in the arguments array
  - Enter wallet password to submit invoke

## Growth tokens
- These will be locked up from distribution for 12 months starting from the timestamp recorded on token sale end
- Once the 12 month lock up is completed, you can sent funds from the token pool to any address from the token owner address
  - Run command `testinvoke <CONTRACT_HASH> transferGrowthTokens ['<ADDRESS>',<AMOUNT>]`
    - Keep in mind amount needs to be times 10^8, since the token has 8 decimal places
      - An amount of 1 will transfer 0.00000001 ASA
    - Please remember to not have any spaces in the arguments array
  - Enter wallet password to submit invoke

## NEP5 Testing
- Once this contract is deployed on the NEO Testnet, you can add it to your neon wallet by contract hash
- After initializing the contract you can test out send tokens to and from addresses as with normal tokens
  - If only testing, all tokens will start from the contact owner wallet after invoking the `deploy` command as described above.
- You can send tokens to exchanges you are working with for token integration, and from there they should be able to ensure it's functioning as expected on the testnet before your deployment to mainnet
