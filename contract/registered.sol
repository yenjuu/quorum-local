// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.6.0;

//pragma experimental ABIEncoderV2;

contract registered {
    address owner;

    struct user {
        string userID;
        string object;
        string attribute;
        string wishlist;
    }
    // User object which we will store
    user user_obj;

    constructor() public {
        owner = msg.sender;
    }

    event logObjs(string id, string obj, string attr, string wishlist);

    function setUser(
        string memory _userID,
        string memory _object,
        string memory _attribute,
        string memory _wishlist
    ) public {
        user_obj = user({
            userID: _userID,
            object: _object,
            attribute: _attribute,
            wishlist: _wishlist
        });
        emit logObjs(
            user_obj.userID,
            user_obj.object,
            user_obj.attribute,
            user_obj.wishlist
        );
    }

    function getUser()
        public
        view
        returns (
            string memory,
            string memory,
            string memory,
            string memory
        )
    {
        return (
            user_obj.userID,
            user_obj.object,
            user_obj.attribute,
            user_obj.wishlist
        );
    }
}
