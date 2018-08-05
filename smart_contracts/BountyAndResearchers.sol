pragma solidity ^0.4.23;

contract BountyAndResearchers {

    address public owner;
    uint public numBounties; 

    constructor() public {
        owner = msg.sender;
        numBounties = 0;
    }

    struct Bounty { //todo: add other fields for bounty creation
        address bountyCreatorAddress;
        uint bountyAmount;
    }

    struct Researcher {
        address researcherAddress;
        address bountyAddress; //researcher can only do 1 bounty at a time
    }

    mapping(address => Bounty) public bounties;

    mapping(address => Researcher[]) public registeredResearchersOfBounty;

    mapping(address => address) public activeBountyOfResearcher;


    function createBounty() public {
        bounties[msg.sender] = Bounty(msg.sender, 100); //default value of bounty for now, todo: implement payable when receiving tokens
        numBounties++;
    }

    function registerAsResearcher(address bountyAddress) {
        registeredResearchersOfBounty[bountyAddress].push(Researcher(msg.sender, bountyAddress));
        activeBountyOfResearcher[msg.sender] = bountyAddress;
    }

    function getNumberOfResearchersForBounty(address bountyAddress) public constant returns(uint count) {
        return registeredResearchersOfBounty[bountyAddress].length;
    }


    function destroyContract() public {  //todo: import Ownable.sol
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}
