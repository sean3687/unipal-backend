# AWS Setup

### Create AWS EC2 Instance
1. Create AWS EC2 Instance by going to AWS -> EC2 Dashboard -> Launch Instance
2. For application and OS images, select: Ubunto Server 22.04 (free tier)
3. For instance type, select: t2.micro (free tier)
4. Create and save the key pair file, which will be used to SSH into the VM
5. Network settings: create a new security group, allow HTTP/HTTPS traffic from the internet

### Connect to EC2
1. SSH onto the EC2 instance OR use EC2 Instance Connect (EC2 Instance Connect Recommended)
2. Username should be ubunto, unless otherwise changed
3. If using SSH, the default command from the AWS SSH command page is expected to work, assuming the key pair file (.pem) is in the current directory

### Clone the Repository
1. Create a personal access token and store it. This is needed since the repository is private. 
2. Ensure that the personal access token has full repository access
3. Run the command: ```git clone https://<pat>@github.com/<your account or organization>/<repo>.git```. This command should looks omething like: ```git clone https://ghp_numbersandletters@githuib.com/unipalAi/unipal-backend.git```

### Set up .env 
1. Navigate to the project directory
2. create a .env file by using the following command: ```nano .env```
3. Copy and paste all .env variables into the file using the nano editor
4. Save and exit by using ctrl+O and ctrl+X
5. Double check that the .env file exists by using the command: ```ls -a```

### Download Dependencies
1. Update packages to latest: ```sudo apt-get update```
2. Install python: ```sudo apt install python3```
3. Install pip: ```sudo apt install python3-pip```
4. Install python-venv: ```sudo apt-get install python3-venv```

### Python venv/libraries
1. Navigate into the project directory
2. Create a virtual environment: ```python3 -m venv venv```
3. Run the following command: ```source venv/bin/activate```
4. Download libraries: ```pip install -r requirements.txt```

### Set up Server
1. Install nginx: ```sudo apt install nginx```
2. Edit the server configuration file: ```sudo nano /etc/nginx/sites-available/default```
3. Add the following under location:

        proxy_pass http://127.0.0.1:5000
        include proxy_params;

4. Run the following command to apply the updates: ```sudo systemctl restart nginx```
5. Navigate to the project directory, then app directory
6. Run the flask application: ```python app.py```

### Connect the front-end to the cloud API
1. Note and save the IPv4 of the EC2 instance
2. Replace the front-end calls to the IP of the EC2 instance
3. Any calls to the EC2 instance IP will be an API call to the Flask application

### Restarting the Server
1. Navigate to the project directory: ```cd unipal-backend```
2. Activate the python virtual environment: ```source venv/bin/activate```
3. Navigate to the flask app.py directory: ```cd app```
4. Run the flask app.py: ```python app.py```

### Miscellanious Notes
1. By default, the EC2 instance should be able to connect to the internet and ping the database. This can be tested using ```nslookup -type=SRV unipal.bnx1cu8.mongodb.net```
2. Currently, the instances occasionnally/eventually crashes and become unable to be connected to. The reason for this is unknown, but is likely caused by running out of memory. 

### References: 

Deploying a flask application: 
https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html#python-flask-deploy
https://www.geeksforgeeks.org/how-to-deploy-flask-app-on-aws-ec2-instance/
https://www.youtube.com/watch?v=ct1GbTvgVNM
https://github.com/yeshwanthlm/YouTube/blob/main/flask-on-aws-ec2.md

Remote cloning a repository: 
https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository
https://stackoverflow.com/questions/2505096/clone-a-private-repository-github
