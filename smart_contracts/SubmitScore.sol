pragma solidity ^0.4.0;

contract SubmitScore {
    struct Winner {
       uint score;
       address winnerAddress;
    }
    mapping(uint => Winner) BountyWinners;
    address public owner;

    function SubmitScore() public {
        owner = msg.sender;
    }

    function submitScore(uint bountyID, uint8 score) public {
        if (score < 0 || score < BountyWinners[bountyID].score) return;
        BountyWinners[bountyID] = Winner(score, msg.sender);
    }
    
    function getCurrentWinner(uint bountyID) public constant returns (address winner) {
        return BountyWinners[bountyID].winnerAddress;
    }
    
}
