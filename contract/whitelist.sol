// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.6.0;
pragma experimental ABIEncoderV2;

contract whitelist {
    address owner;
    string[] tx_hash;
    string[] wl;
    uint256[] D;
    int256[] S;
    int256 R;

    constructor() public {
        owner = msg.sender;
    }

    event participant(uint256 num);
    event whitelist_log(string[] whitelist);
    event exchange_result(string hash_a, string hash_b);
    bool flag = true;

    function add_user_secret(string memory _tx_hash, int256 _S) public {
        tx_hash.push(_tx_hash);
        S.push(_S);
        if (S.length >= 100 && flag == true) {
            uint256 num = S.length;
            emit participant(num);
            flag = false;
        }
    }

    function calc_random(int256 _R) public returns (uint256[] memory) {
        R = _R;
        for (uint256 i = 0; i < S.length; i++) {
            D.push(uint256(abs(S[i] - _R)));
        }
        return D;
    }

    function sort() public returns (uint256[] memory, string[] memory) {
        quickSort(D, 0, D.length - 1);
        return (D, tx_hash);
    }

    function set_whiteList(uint256 _x) public returns (string[] memory) {
        for (uint256 i = 0; i < (tx_hash.length / _x); i++) {
            wl.push(tx_hash[i]);
        }
        emit whitelist_log(wl);
        return wl;
    }

    function set_result(string memory _hash_a, string memory _hash_b) public {
        string memory hash_a = _hash_a;
        string memory hash_b = _hash_b;
        emit exchange_result(hash_a, hash_b);
    }

    function clean(string memory _hash_a, string memory _hash_b)
        public
        returns (string[] memory, int256[] memory)
    {
        for (uint256 i = 0; i < tx_hash.length; i++) {
            if (compareStrings(_hash_a, tx_hash[i])) {
                delete tx_hash[i];
                delete S[i];
                tx_hash[i] = tx_hash[tx_hash.length - 1];
                S[i] = S[S.length - 1];
                tx_hash.length--;
                S.length--;
            } else if (compareStrings(_hash_b, tx_hash[i])) {
                delete tx_hash[i];
                delete S[i];
                tx_hash[i] = tx_hash[tx_hash.length - 1];
                S[i] = S[S.length - 1];
                tx_hash.length--;
                S.length--;
            }
        }
        D.length = 0;
        wl.length = 0;
        flag = true;
        return (tx_hash, S);
    }

    function get_data() public view returns (string memory) {
        string memory output = "";
        for (uint256 i = 0; i < S.length; i++) {
            string memory tmp;
            tmp = concatenate(tmp, "tx_hash: ");
            tmp = concatenate(tmp, tx_hash[i]);
            tmp = concatenate(tmp, "; D: ");
            tmp = concatenate(tmp, uint2str(D[i]));
            tmp = concatenate(tmp, "; ");

            output = concatenate(output, tmp);
        }
        return output;
    }

    function get_difference() public view returns (string memory) {
        string memory output = "";
        for (uint256 i = 0; i < D.length; i++) {
            string memory tmp;
            tmp = concatenate(tmp, tx_hash[i]);
            tmp = concatenate(tmp, "; ");
            tmp = concatenate(tmp, uint2str(D[i]));
            tmp = concatenate(tmp, "; ");

            output = concatenate(output, tmp);
        }
        return output;
    }

    function quickSort(
        uint256[] storage arr,
        uint256 left,
        uint256 right
    ) internal {
        uint256 i = left;
        uint256 j = right;
        uint256 pivot = arr[left + (right - left) / 2];
        while (i <= j) {
            while (arr[i] < pivot) i++;
            while (pivot < arr[j]) j--;
            if (i <= j) {
                (arr[i], arr[j]) = (arr[j], arr[i]);
                string memory tmp;
                tmp = tx_hash[i];
                tx_hash[i] = tx_hash[j];
                tx_hash[j] = tmp;

                i++;
                j--;
            }
        }
        if (left < j) quickSort(arr, left, j);
        if (i < right) quickSort(arr, i, right);
    }

    function concatenate(string memory a, string memory b)
        internal
        pure
        returns (string memory)
    {
        return string(abi.encodePacked(a, b));
    }

    function abs(int256 _i) internal pure returns (int256) {
        if (_i < 0) {
            return -_i;
        }
        return _i;
    }

    function int2str(int256 _i) internal pure returns (string memory) {
        int256 tmp = _i;
        if (tmp == 0) {
            return "0";
        }
        int256 j = tmp;
        uint256 len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint256 k = len - 1;
        while (tmp != 0) {
            bstr[k--] = bytes1(uint8(48 + (tmp % 10)));
            tmp /= 10;
        }
        return string(bstr);
    }

    function uint2str(uint256 _i) internal pure returns (string memory) {
        uint256 i = _i;
        if (i == 0) return "0";
        uint256 j = i;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint256 k = length - 1;
        while (i != 0) {
            bstr[k--] = bytes1(uint8(48 + (i % 10)));
            i /= 10;
        }
        return string(bstr);
    }

    function compareStrings(string memory a, string memory b)
        private
        pure
        returns (bool)
    {
        return (keccak256(abi.encodePacked((a))) ==
            keccak256(abi.encodePacked((b))));
    }
}
