import base64
import os

# Flask
import cv2
from flask import Flask, request, render_template, jsonify
import requests
from gevent.pywsgi import WSGIServer
import numpy as np
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
    img_path = request.form["img_path"]
    mask_path = request.form["mask_path"]
    save_path = request.form["save_path"]
    if request.form["mode"] == "fusion":
        try:
            matting_edit_bg.generate(mask_path, img_path, save_path)
        except AttributeError:
            return jsonify(data= {"message": "Input pictures failure. "}, code=1)
        except cv2.error as err:
            print(err)
            return jsonify(data= {"message": "cv2 failure. "}, code=1)
        except:
            return jsonify(data= {"message": "runtime failure. "}, code=1)
    if request.form["mode"] == "change":
        bg_path = request.form["bg_path"]
        scale = float(request.form["scale"])
        position_x = int(request.form["position_x"])
        position_y = int(request.form["position_y"])
        # print(request.form)
        # print(scale, position_x, position_y)
        try:
            # matting_edit_bg.generate(mask_path, img_path, save_path)
            matting_edit_bg.generate(mask_path, img_path, save_path, bg_path, scale=scale, x=position_x, y=position_y)
        except AttributeError:
            return jsonify(data= {"message": "Input pictures failure. "}, code=1)
        except cv2.error as err:
            print(err)
            return jsonify(data= {"message": "cv2 failure. "}, code=1)
        except:
            return jsonify(data= {"message": "runtime failure. "}, code=1)

    return jsonify(data= {"path": save_path}, code=0)


if __name__ == '__main__':
    # app.run(port=5002, threaded=False)

    # Serve the app with gevent
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
