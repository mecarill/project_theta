# /right/image_mono
import os
import rclpy
from rclpy.node import Node
import json
from sensor_msgs.msg import Image
from std_msgs.msg import String
print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
print(os.getcwd())
import sys
sys.path.append("install/theta_pkgs/lib/python3.8/site-packages/theta_pkgs")
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from cv_bridge import CvBridge
import tensorflow as tf
from utils import label_map_util
from utils import visualization_utils as vis_util
from tensorflow.python.platform import gfile
from tensorflow.core.protobuf import saved_model_pb2
from tensorflow.python.util import compat

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)
            
class ModelImg(Node):

	def __init__(self):
		super().__init__('model_img')
		#fileroot = '~/ros2_ws/src/theta_pkgs/theta_pkgs/'
		fileroot=""
		model_path = fileroot+"saved_model/"
		object_file_path = fileroot+'saved_model/object-detection.pbtxt'
		self.subscription = self.create_subscription(
			Image,
			'/color/image',
			self.model_callback,
			10)
		self.subscription  # prevent unused variable warning
		self.publisher_ = self.create_publisher(Image, '/right/image_mono2', 10)
		self.publisher2_ = self.create_publisher(String, '/centroid', 10)
		self.mdl_inf = ModelInference(model_path, object_file_path)

	def model_callback(self, msg):
		
		# Model Function returns dict of items:location(x,y) + image with BB << Focus today
		msg, centroid_msg = self.mdl_inf.show_inference_single_image(model = self.mdl_inf.model,image_path='', category_index = self.mdl_inf.category_index, image_np = msg, supi = self)
		
		# publish Image with BB << Focus today
		msg2 = String()
		#Service call items:items:location(x,y,z) to local "DB" TODO
		msg2.data = json.dumps(centroid_msg, cls=NpEncoder)
		#self.get_logger().info('Got Image')
		self.publisher_.publish(msg)
		self.publisher2_.publish(msg2)

class ModelInference (object):
    
    def __init__(self, model_path, object_file_path):
        self.model = tf.saved_model.load(model_path)
        self.num_classes = 90
        self.label_map = label_map_util.load_labelmap(object_file_path)
        categories = label_map_util.convert_label_map_to_categories(self.label_map, max_num_classes = self.num_classes, use_display_name=True)
        self.category_index = label_map_util.create_category_index(categories)
        self.bridge = CvBridge()
    
    @staticmethod
    def run_inference_for_single_image(model, image):
          image = np.asarray(image)
          # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
          input_tensor = tf.convert_to_tensor(image)
          # The model expects a batch of images, so add an axis with `tf.newaxis`.
          input_tensor = input_tensor[tf.newaxis,...]
        
          # Run inference
          model_fn = model.signatures['serving_default']
          output_dict = model_fn(input_tensor)
        
          # All outputs are batches tensors.
          num_detections = int(output_dict.pop('num_detections'))
          output_dict = {key:value[0, :num_detections].numpy() 
                         for key,value in output_dict.items()}
          output_dict['num_detections'] = num_detections
        
          # detection_classes should be ints.
          output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
           
          return output_dict
      
     
    @staticmethod
    def show_inference_single_image(model, image_path, category_index,supi, image_np=""):
      # the array based representation of the image will be used later in order to prepare the
      # result image with boxes and labels on it.
      bridge = CvBridge()
      image_np=bridge.imgmsg_to_cv2(image_np, desired_encoding='passthrough')
      if len(image_np.shape)==2:
      	  img2 = cv.merge((image_np,image_np,image_np))
      	  image_np = img2
      # Actual detection.
      output_dict = ModelInference.run_inference_for_single_image(model, image_np)
      # Get final detect boxes and detect classes
      detect_boxes = [output_dict['detection_boxes'][x] for x in [i for i,j in enumerate(output_dict['detection_scores']) if j > 0.5]]
      detect_classes = [output_dict['detection_classes'][x] for x in [i for i,j in enumerate(output_dict['detection_scores']) if j > 0.5]]
      
      # Output Dict - detection boxes
      centroid_dict = ModelInference.get_image_centroid(detect_boxes, image_np, detect_classes)
      # Visualization of the results of a detection.
      vis_util.visualize_boxes_and_labels_on_image_array(
          image_np,
          output_dict['detection_boxes'],
          output_dict['detection_classes'],
          output_dict['detection_scores'],
          category_index,
          instance_masks=output_dict.get('detection_masks_reframed', None),
          use_normalized_coordinates=True,
          line_thickness=8)
      # items_dict = {'item':centroid x,y,'item2':centroid x,y'}
      image_np = bridge.cv2_to_imgmsg(image_np, encoding="rgb8")

      return image_np, centroid_dict


    @staticmethod
    def get_image_centroid(bboxes, image_np, classes):
        # Get the centroid of every bbox in relative coordinates
        # Bounding boxes are encoded as [y_min, x_min, y_max, x_max]
        centroid_dict = dict()
        
        for each_class in set(classes):
            bbox_nest = [bboxes[x] for x in [i for i,j in enumerate(classes) if j==each_class]]
            bbox_list = list()
            for bbox in bbox_nest:     
                y_pt = int(((bbox[2]-bbox[0])/2+bbox[0])*image_np.shape[0])
                x_pt = int(((bbox[3]-bbox[1])/2+bbox[1])*image_np.shape[1])
                bbox_list.append([x_pt,y_pt])
            
            centroid_dict[int(each_class)] = bbox_list
            
        return centroid_dict
				   
def main(args=None):
	rclpy.init(args=args)

	model_img = ModelImg()

	rclpy.spin(model_img)

	# Destroy the node explicitly
	# (optional - otherwise it will be done automatically
	# when the garbage collector destroys the node object)
	minimal_subscriber.destroy_node()
	rclpy.shutdown()


if __name__ == '__main__':
	print(os.getcwd())
	main()

