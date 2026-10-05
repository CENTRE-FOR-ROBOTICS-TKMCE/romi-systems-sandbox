from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'romi_teleop'

setup(
    name=package_name,
    version='2.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='romi',
    maintainer_email='user@example.com',
    description='Front / back / left / right teleop controller for Romi (GUI D-pad and keyboard)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gui_controller = romi_teleop.gui_controller:main',
            'keyboard_controller = romi_teleop.keyboard_controller:main',
        ],
    },
)
