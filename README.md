# USRP-to-redis

### installation
The following software needs to be installed: Python 3.10, UHD Driver, Docker

UHD driver can be installed using the guide present at [PySDR UHD Install Guide](https://pysdr.org/content/usrp.html#software-drivers-install)

To setup the project, first create a virtual environment using venv. Once the environment is created and activated, all other dependencies can be installed using ```pip install -r requirements.txt```

Before running any of the applications in this repo, first start docker using ```docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest```

### To run the application

Select the application you would like to run. For the system, you must have a USRP to_redis process running for each radio and a single schedule_to_redis process for both.

### Trouble shooting

If you get any errors, they are most likely the applications being unable to access Redis. In this case, make sure that redis stack server is running using docker ps.
All other errors will have descriptive error messages.