from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

def generate_launch_description():
    approx_sync = LaunchConfiguration('approx_sync', default='True')
    mapping = LaunchConfiguration('localise', default='False')
    return LaunchDescription([
        DeclareLaunchArgument(
            'approx_sync',
            default_value='True',
            description='Use approx_sync for images if true'),
        DeclareLaunchArgument(
            'mapping',
            default_value='False',
            description='Mapping instead of localisation if true'),
        Node(
            package='depthai_examples',
            executable='rgb_stereo_node',
            name='stereo_node'
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments = ["0.035", "0", "-1.5", "-1.57079632679", "0", "-1.57079632679", "base_link", "oak-d_left_camera_optical_frame"],
            name='tf2'
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments = ["-0.035", "0", "-1.5", "-1.57079632679", "0", "-1.57079632679", "base_link", "oak-d_right_camera_optical_frame"],
            name='tf2'
        ),
        Node(
            package='image_proc',
            executable='image_proc',
            name='image_proc',
            remappings=[
                ('image_raw', 'left/image'),
                ('camera_info', 'left/camera_info'),
                ('image_mono', 'left/image_mono'),
                ('image_rect', 'left/image_rect'),
            ]
        ),
        Node(
            package='image_proc',
            executable='image_proc',
            name='image_proc',
            remappings=[
                ('image_raw', 'right/image'),
                ('camera_info', 'right/camera_info'),
                ('image_mono', 'right/image_mono'),
                ('image_rect', 'right/image_rect'),
            ]
        ),
        Node(
            package='rtabmap_ros',
            executable='rtabmap',
            name='rtabmap_ros',
            parameters=[
            	{"approx_sync": True},
            	{"subscribe_stereo": True}
            ]
        ),
        Node(
            package='rtabmap_ros',
            executable='rtabmapviz',
            name='rtabmapviz'
        ),
        Node(
            package='theta_pkgs',
            executable='model_inference',
            name='model_inference'
        ),
        
        # This node needs to be run seperately
        #Node(
        #    package='rtabmap_ros',
        #    executable='stereo_odometry',
         #   name='stereo_odometry',
         #   parameters=[
         #   	{"approx_sync": True}
          #  ]),

    ])
