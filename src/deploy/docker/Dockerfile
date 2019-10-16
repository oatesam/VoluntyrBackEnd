# Python 3.6.9 Base image
FROM python:3.6.9

WORKDIR /app

# Add and install requirements
add requirements.txt requriements.txt

# Add project files
add src src/

WORKDIR src/voluntyrBackend/

RUN pip3 install -r /app/requriements.txt

# EXPOSE 8000

ENV VOL_SECRET_KEY="8c3b1f260864e6f18a410925a33b7f4ac2752b456e5f238245a69682f8d37314fb6f02fb1f84ba92b093be3376db2c1a4703710b7ae097c0a3c32d94de37debf4b50399024f40c882edb0b740282239510860edd118944d1bea5d5574aa92a58474dd68e9c10b5847a467e298acf70850a150181133f3e55481dde94e9a54cf5"

ENV VOL_DEBUG=False

RUN useradd -ms /bin/bash myuser
USER myuser

WORKDIR /app/src/deploy


# If running container locally
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# run gunicorn - for heroku
# CMD gunicorn voluntyrBackend.wsgi:application --bind 0.0.0.0:$PORT

CMD ["/bin/bash", "/app/src/deploy/start.sh"]