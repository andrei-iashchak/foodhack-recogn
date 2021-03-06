from io import BytesIO
from flask import Flask, send_file, request
from PIL import Image
import requests
import numpy as np
import tensorflow as tf
from json import dumps
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
import os

PATH_TO_CKPT = '/app/my_frozen_inference_graph.pb'

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

PATH_TO_LABELS = '/app/my_label_map.pbtxt'
NUM_CLASSES = 90

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)
print('Loaded')
#
app = Flask(__name__)

def image2array(image):
    (w, h) = image.size
    return np.array(image.getdata()).reshape((h, w, 3)).astype(np.uint8)

def array2image(arr):
    return Image.fromarray(np.uint8(arr))

def detect_objects(sess, image):
    '''Plots the object detection result for a given image.'''
    image_np = image2array(image)
    image_np_expanded = np.expand_dims(image_np, axis=0)

    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    (boxes, scores, classes, num_detections) = sess.run(
          [boxes, scores, classes, num_detections],
          feed_dict={image_tensor: image_np_expanded})

    boxes = np.squeeze(boxes)
    classes = np.squeeze(classes).astype(np.int32)
    scores = np.squeeze(scores)
    return [boxes, scores, classes, num_detections]

@app.route('/')
def detect():
    default_url = 'http://thecatapi.com/api/images/get?format=src&type=jpg'
    url = request.args.get('url', default_url)
    r = requests.get(url)
    image = Image.open(BytesIO(r.content))
    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            detect_objects(sess, image)
    return "Hi"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="443", use_reloader=False)
