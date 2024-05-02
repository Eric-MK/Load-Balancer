#Use lightweight Python image
FROM python:3.9-slim

#set working directory in the container
WORKDIR /app

#copy the current directory contentd into container /app
COPY . /app

#Install needed packages specified in req.txt
RUN pip install --no-cache-dir flask

#Make port 5000 available
EXPOSE 5000

#Define environment variable for the server ID
ENV SERVER_ID 1

#Command to run the application
CMD ["python","server.py"]