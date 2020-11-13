from flask import Flask, request, jsonify
import json, pprint
import register

app = Flask(__name__)

"""
假設使用者已有以太坊帳號
讓使用者輸入自己的以太坊帳號、私鑰 POST
"""


@app.route('/addObj', methods=["POST"])
def addObj():
    if 'acct' in request.args:
        acct = request.args['acct']
        print("acct", acct)
    if 'obj' in request.args:
        obj = request.args['obj']
        print('obj', obj)
    if 'attr' in request.args:
        attr = request.args['attr']
        print('attr', attr)
    if 'wishlist' in request.args:
        wishlist = request.args['wishlist']
        print('wishlist', wishlist)

    results = jsonify(
        acct=acct,
        obj=obj,
        attr=attr,
        wishlist=wishlist
    )

    register.run(acct, obj, attr, wishlist)
    return results


if __name__ == "__main__":
    
    app.run()