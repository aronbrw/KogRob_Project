from setuptools import find_packages, setup

package_name = 'bme_ros2_tutorials_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='szabados',
    maintainer_email='szabados@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'hello_world = bme_ros2_tutorials_py.hello_world:main',
            'publisher = bme_ros2_tutorials_py.publisher:main',
            'subscriber = bme_ros2_tutorials_py.subscriber:main'
        ],
    },
)
