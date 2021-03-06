import base64
import os

# Flask
import cv2
import datetime
from flask import Flask, request, render_template, jsonify
from gevent.pywsgi import WSGIServer
import sentry_sdk
from ChangeBg import ChangeBg

# Declare a flask app
app = Flask(__name__)

matting_edit_bg = ChangeBg()


@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')


@app.route('/', methods=['POST'])
def fusion_bg():
    """
    Change bg.
    Basis params:
        mode, img_path, mask_path, save_path
    fusion:
        mode=fusion
        no extra params requires. save as rgba
    change_bg:
        mode=change
        pure bg:
            bg_color
        image bg:
            bg_path, scale, position_x, position_y, blur_coeff (optional)
    """
    img_path = request.form["img_path"]
    mask_path = request.form["mask_path"]
    save_path = request.form["save_path"]

    print(datetime.datetime.now())
    print("Input: ")
    print(request.form)

    if request.form["mode"] == "fusion":
        try:
            matting_edit_bg.generate(mask_path, img_path, save_path)
        except AttributeError:
            return jsonify(data={"message": "Input pictures failure. "}, code=1)
        except cv2.error as err:
            print(err)
            return jsonify(data={"message": "cv2 failure "}, code=1)
        except ValueError:
            print("img, mask size unmatch")
            return jsonify(data={"message": "img, mask size unmatch"}, code=1)
        except OSError:
            return jsonify(data={"message": "save failure "}, code=1)

    elif request.form['mode'] == "change_color":
        bg_color = request.form["bg_color"]

        try:
            matting_edit_bg.generate(mask_path, img_path, save_path, bg_color=bg_color)
        except AttributeError:
            return jsonify(data={"message": "Input pictures failure. "}, code=1)
        except cv2.error as err:
            print(err)
            return jsonify(data={"message": "cv2 failure "}, code=1)
        except ValueError:
            print("img, mask size unmatch")
            return jsonify(data={"message": "img, mask size unmatch"}, code=1)
        except OSError:
            return jsonify(data={"message": "save failure "}, code=1)
        except:
            return jsonify(data={"message": "change color error"}, code=1)

    elif request.form["mode"] == "change_bg":
        bg_path = request.form["bg_path"]
        scale = float(request.form["scale"])
        position_x = int(float(request.form["position_x"]))
        position_y = int(float(request.form["position_y"]))
        blur_coeff = int(float(request.form["blur_coeff"]))

        try:
            if blur_coeff != 0:
                matting_edit_bg.generate(mask_path, img_path, save_path, bg_addr=bg_path, scale=scale, x=position_x,
                                         y=position_y, blur_coeff=blur_coeff)
            else:
                matting_edit_bg.generate(mask_path, img_path, save_path, bg_addr=bg_path, scale=scale, x=position_x,
                                         y=position_y)
        except AttributeError:
            return jsonify(data={"message": "Input pictures failure. "}, code=1)
        except cv2.error as err:
            print(err)
            return jsonify(data={"message": "cv2 failure "}, code=1)
        except ValueError:
            print("img, mask size unmatch")
            return jsonify(data={"message": "img, mask size unmatch"}, code=1)
        except OSError:
            return jsonify(data={"message": "save failure. Invalid format or no access to write."}, code=1)

    return jsonify(data={"path": save_path}, code=0)


if __name__ == '__main__':
    # app.run(port=5002, threaded=False)
    sentry_sdk.init("http://3a06f4e9985c453f83c448479309c91b@192.168.50.13:9900/3")

    # Serve the app with gevent
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
