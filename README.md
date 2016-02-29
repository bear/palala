palala - taming the river of news

[![Circle CI](https://circleci.com/gh/bear/palala.svg?style=svg)](https://circleci.com/gh/bear/palala)
[![Requirements Status](https://requires.io/github/bear/palala/requirements.svg?branch=master)](https://requires.io/github/bear/palala/requirements/?branch=master)
[![codecov.io](https://codecov.io/github/bear/palala/coverage.svg?branch=master)](https://codecov.io/github/bear/palala?branch=master)


## Local Development Environment

Currently I'm assuming an OS X environment as that is what I am using...

```
brew tap homebrew/nginx
brew install nginx-full --with-push-stream-module
brew install uwsgi --with-python

cd /path/to/your/palala
pyenv install 2.7.11
pyenv virtualenv 2.7.11 palala
make update-all
````

Example Nginx config

```
# palala.conf
#
# With a homebrew installed nginx:
#     /usr/local/etcc/nginx/servers/
#     ~/homebrew/etc/nginx/servers/
# On a Debian/Ubuntu installed nginx:
#     /etc/nginx/conf.d/
# Currently assumes uwsgi config
#
# configuration items for http block
#
#   charset     utf-8;
#   client_max_body_size 75M;
#   push_stream_shared_memory_size 100m;
#
upstream uwsgicluster {
    server 127.0.0.1:5080;
}
server {
    listen      8080;
    server_name palala.org;

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

    # endpoint to push events to clients
    location /pub {
        # activate publisher (admin) mode for this location
        push_stream_publisher admin;

        # query string based channel id
        push_stream_channels_path               $arg_id;
    }
    # endpoint SSE clients subscribe to
    location ~ /ev/(.*) {
        # activate event source mode for this location
        push_stream_subscriber eventsource;

        # positional channel path
        push_stream_channels_path                   $1;
        # message template
        push_stream_message_template                "{\"id\":~id~,\"channel\":\"~channel~\",\"text\":\"~text~\"}";

        # ping frequency
        push_stream_ping_message_interval           10s;
    }

}
```

Testing the webmention handler - this assumes that you have a `/etc/hosts` entry to make palala.org to 127.0.0.1

```
./sm.py http://webmention.tools/test1.html
```

Testing the nginx push stream module - this assumes that you have a `/etc/hosts` entry to make palala.org to 127.0.0.1

```
make uwsgi
make server
open http://palala.org:8080/en
curl http://palala.org:8080/pub?id=push -d "Some Text"
```
