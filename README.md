## Deployment 

<b>Below are the configuration files used for production deployment, <> was used to omit some text </b>

#### Gunicorn configuration
Gunicorn spawns multiple threads that execute requests after they are passed from the Nginx
```
#!/bin/bash

NAME="RestFramework"
DIR=~/Django-RF
USER=<>
GROUP=<>
WORKERS=1
BIND=unix:~/Django-RF/run/gunicorn.sock
DJANGO_SETTINGS_MODULE=core.settings
DJANGO_WSGI_MODULE=core.wsgi
LOG_LEVEL=error

cd $DIR
source ~/.virtualenvs/py3_web/bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DIR:$PYTHONPATH

exec sudo ~/.virtualenvs/py3_web/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $WORKERS \
  --bind=$BIND \
  --log-level=$LOG_LEVEL \
  --log-file=-
```

#### Supervisor configuration
Supervisor is a client/server system that allows its users to monitor and control a number of processes on UNIX-like operating systems.

It shares some of the same goals of programs like launchd, daemontools, and runit. Unlike some of these programs, it is not meant to be run as a substitute for init as “process id 1”. Instead it is meant to be used to control processes related to a project or a customer, and is meant to start like any other program at boot time.

I am using supervisor to control gunicorn processes.

```
[program:rpi_rf]
command=~/Django-RF/gunicorn_start
user=<>
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=~/Django-RF/logs/gunicorn.log
```

#### Nginx config
NGINX or nginx or NginX, is a web server that can also be used as a reverse proxy, load balancer, mail proxy and HTTP cache. 

I am using Nginx to return static files.
```

upstream app_server {
    server unix:~/Django-RF/run/gunicorn.sock fail_timeout=0;

}

server {
    listen <>;
    server_name <>;  # here can also be the IP address of the server

    keepalive_timeout 5;
    client_max_body_size 4G;

    access_log ~/Django-RF/logs/nginx-access.log;
    error_log ~/Django-RF/logs/nginx-error.log;

    location /static/ {
        alias ~/Django-RF/staticfiles/;
    }

    # checks for static file, if not found proxy to app
    location / {
        try_files $uri @proxy_to_app;
    }

    location @proxy_to_app {
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header Host $http_host;
      proxy_redirect off;
      proxy_pass http://app_server;
    }
}
```