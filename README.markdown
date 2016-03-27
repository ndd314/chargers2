[![Build Status](https://travis-ci.org/ndd314/chargers2.svg?branch=master)](https://travis-ci.org/ndd314/chargers2)

# Chargers2

A project to check on the availability of EV charge stations at the VMware Palo Alto Campus

Currently running on http://vmwarechargepoint.herokuapp.com/

# Deploy to Heroku

1. Install the heroku toolbelt
2. Create the heroku app. Here is an example of the command sequence:
```shell
heroku login
heroku create
heroku apps:rename vmwarechargepoint
# heroku requires credit card information for the heroku-redis free tier 
heroku plugins:install heroku-redis
heroku addons:create heroku-redis:hobby-dev -a vmwarechargepoint
# chargepoint.com username/password that can see VMware charge stations
heroku config:set CP_USERNAME=xxx CP_PASSWORD=xxx GOOGLE_ANALYTICS_SITE_ID=xxx
git push heroku
heroku ps:scale worker=1
```