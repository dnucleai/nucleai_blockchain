pragma solidity ^0.4.23;

contract BountyData {
    // initial file to test getters/setters, will be migrated to main contract file

    string[5] public features;
    string public result;
    address public winner;

    // Add an (index, feature) pair to features.
    function addFeature(uint index, string value) external {
        require(index <= 4);
        features[index] = value;
    }

    function setResult(string value) external {
        result = value;
    }

    function sendEthToContract(address _buyer) payable public {}

    // Warning: money can be sent to this contract, but cannot be withdrawn as is.
    function () payable public {
        sendEthToContract(msg.sender);
    }

    function setWinner(address winnerAddress) external {
        // require role in order to set winner
        winner = winnerAddress;
    }
}
