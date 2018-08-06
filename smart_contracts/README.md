# Smart Contracts

## Setting up
Simple developer environment:
1. Download MetaMask Chrome extension. Acquire some test ether from faucet for Ropsten test network.
2. Compile on Remix. Use Injected Web3 environment. Deploy contract and test on Ropsten network.

More advanced developer environment:
1. Download IntelliJ. Set up IntelliJ-Solidity plugin.
2. Download ganache-cli. To spin up local network, run `ganache-cli` with or without options. See more at https://github.com/trufflesuite/ganache-cli
3. On Remix, set environment to Web3 Provider and use the ganache environment, which defaults to localhost:7545
4. Optional: Download truffle and webpack, configure both for sample React application.


## Contract Design
### BountyAndResearchers.sol
Composes of two main storage parts: keeping track of bounties and their data, and researchers and their data.

1. keeps record of all the bounties, and their internal values. Each bounty is identified by the address of the owner that created the contract. Each bounty keeps track of 
    - bounty amount, currently set to `100` with no units, pending functions that allow payment
    - list of registered researchers by their address. Only researchers in this list are eligible to win the bounty.
    - list of features required in the model, currently a string array of max length 5. Contract allows for adding/editing one feature at a time.
    - string result, representing the field of the result.
    - boolean isActive, false at bounty creation, then set to `true` after bounty details are finalized up until the end date, false after the end date. When isActive is true, no further changes can be made to bounty object, including features list and bounty amount. 
    - end date, which is the date in which bounty amount will be paid out to winner.
    - address winner
    

2. keeps record of all the researchers. Each researcher is identified by their address. Each researcher can only have one active bounty at a time (* this might change to support multiple bounties per researcher). Each researcher keep track of these fields:
    - address activeBounty, the address of their active bounty
    - boolean isWinner, will be set to true after confirmnation that they are the winner for their active bounty
    - boolean isVoter, will be set to true after they have submitted their scores, and is in the top 75% of highest scores and meets a minimum score requirement. This is so that the network is not flooded with "bad voters" who did not do any work within their models.
    - boolean receivedPayment, will be set to true after `sendBountyPrizeToWinner(address bountyAddress)` is called. This function can only be called if require(isWinner) is true and require(receivedPayment) is false. 


Roles needed: 
1. contract owner, will be creator of this contract, will be an internal Nucleai address. Can do admin functions, override almost everything. Perform manual locking of bounties if necessary. Receive all bounty amount if falling back to centralized payout system (in lieu of voting mechanism). Destroy contract if necessary.
2. bounty creator, owner of the bounty they create, can make changes to their own bounties.
3. researcher, owner of their Researcher object, can register themselves to different bounties. Can vote for themselves or other researchers in the same bounty. Can win the bounty prize. 

Pending: a voting scheme that allows registered addresses for each bounty to vote for the winner.

