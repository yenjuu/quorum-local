// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.6.0;

contract attrRecord {
    string attrName;
    string[] list;
    uint256 list_len = 0;
    event setLog(string attrABI, string attrAddress);
    mapping(string => record) public records;
    //event setEvent(string attrName, string attrHash);
    struct record {
        string attrHash;
        bool _isDeleted;
    }

    // User object which we will store
    function add_data(string memory _attrName, string memory _attrHash) public {
        record memory data = record(_attrHash, true);
        records[_attrName] = data;
        list.push(_attrName);
        list_len = list_len + 1;
    }

    function add_event(string memory _attrABI, string memory _attrAddress)
        public
    {
        emit setLog(_attrABI, _attrAddress);
    }

    function get_all_data() public view returns (string memory, uint256) {
        string memory output = "";
        for (uint256 i = 0; i < list.length; i++) {
            string memory tmp;
            record memory data = records[list[i]];

            if (!comparestring(list[i], "")) {
                tmp = concatenate(tmp, "Attr name: ");
                tmp = concatenate(tmp, list[i]);
                tmp = concatenate(tmp, "/Attr Hash: ");
                tmp = concatenate(tmp, data.attrHash);
                tmp = concatenate(tmp, "; ");

                output = concatenate(output, tmp);
            }
        }
        //list_len = abi.encodePacked(list_len);
        return (output, list_len);
    }

    function get_a_data(string memory _attrName)
        public
        view
        returns (string memory, string memory)
    {
        bytes memory data = bytes(records[_attrName].attrHash);
        if (data.length != 0) {
            return (_attrName, records[_attrName].attrHash);
        }
        return ("null", "null");
    }

    function delete_data(string memory _attrName) public returns (bool) {
        for (uint256 i = 0; i < list.length; i++) {
            if (comparestring(list[i], _attrName)) {
                //records[list[i]] = myArray[myArray.length - 1];
                //myArray.pop()
                delete records[list[i]];
                delete list[i];
                list_len = list_len - 1;
                // records[list[i]]._isDeleted = false;
                // list_len = list_len + 1;
                return true;
            }
        }
        return false;
    }

    function concatenate(string memory a, string memory b)
        internal
        pure
        returns (string memory)
    {
        return string(abi.encodePacked(a, b));
    }

    function comparestring(string memory a, string memory b)
        internal
        pure
        returns (bool)
    {
        if (keccak256(abi.encodePacked(a)) == keccak256(abi.encodePacked(b))) {
            return true;
        }
        return false;
    }
}
