palala - taming the river of news

[![Circle CI](https://circleci.com/gh/bear/palala.svg?style=svg)](https://circleci.com/gh/bear/palala)
[![Requirements Status](https://requires.io/github/bear/palala/requirements.svg?branch=master)](https://requires.io/github/bear/palala/requirements/?branch=master)
[![codecov.io](https://codecov.io/github/bear/palala/coverage.svg?branch=master)](https://codecov.io/github/bear/palala?branch=master)


## Local Development Environment

Currently I'm assuming an OS X environment as that is what I am using...

```
brew tap homebrew/nginx
brew install nginx-full --with-push-stream-module

cd /path/to/your/palala
# assumes PyEnv has activated the virtual env...
# installs uwsgi via pip
make update-uwsgi
````

Example Nginx config

```
# With a homebrew installed nginx: /usr/local/etcc/nginx/servers/palala.conf
# On a Debian/Ubuntu installed nginx: /etc/nginx/conf.d/palala.conf
# Currently assumes uwsgi config

upstream uwsgicluster {
    server 127.0.0.1:5080;
}
server {
    listen      5000;
    server_name palala.org;
    charset     utf-8;
    client_max_body_size 75M;

    location / {
        try_files $uri @palala_web;
    }
    location @palala_web {
        include            uwsgi_params;
        uwsgi_pass         uwsgicluster;

        proxy_redirect     off;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host $server_name;
    }
}
````
