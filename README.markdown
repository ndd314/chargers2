[![Build Status](https://travis-ci.org/ndd314/chargers2.svg?branch=master)](https://travis-ci.org/ndd314/chargers2)

# Chargers2

A project to check on the availability of EV charge stations at the VMware Palo Alto Campus

Currently running on http://vmwarechargepoint.herokuapp.com/

# Testing

1. Install virtualenv `pip install virtualenv`
2. Create virtualenv folder `virtualenv venv`
3. Activate virtualenv `source venv/bin/activate`
4. Get dependencies `pip install -r ./requirements_test.txt`
5. Run tests `PYTHONPATH=. py.test workers`

Step 1-4 can be run by executing `./scripts/setup_virtualenv.sh`
Step 5 can also be run by executing `./scripts/run_test.sh`

# Deploy to Heroku

1. Install the heroku toolbelt
2. Create the heroku app. Here is an example of the commands sequence:
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

# Adding other services
heroku addons:create sendgrid:starter
heroku addons:create easysms:test
heroku addons:create newrelic:wayne
heroku config:set NEW_RELIC_APP_NAME='vmwarechargepoint'
heroku addons:create logmatic:test
heroku addons:create keen:developer
heroku addons:create airbrake:free_heroku
```

You'll need to replace `vmwarechargepoint` with your own app name.

# Travis-CI Autodeploy to Heroku

.travis.yml contains a section for autodeploy to heroku to work:

```yaml
deploy:
  app:
    master: vmwarechargepoint
  provider: heroku
  api_key:
    secure: fEoIdO9F+AkD+MkhcnAuWOIF59dIbyVq4FXuHErwlv9z3rF3Wk3n5bDS5wBtSyUnQpoHgWThRQ+Ln1lmkN881hHUNJ4C7f0pnL8CCJV2Jh0MGR9DDccOoWRJKaW6nZVFlZq7Ze3L9Pc+Z/ksdLflYdt490sAOyIWs3/oNPQ/0/+Ys34KxMYiWIGFnw7pIwp6xRaLXdUrMNBL+EGhyaJdSTricbPimocpeSvkaBcBLNF98k6FCoofbN5te4tD5fY+Xsm2qOuhP1Hx3tqPBuC5n84my3VRxkut8s6Tdzt9q8jjFjh/oRDsKUIjgIYP4z89T089N/bJJ8wgsaojIa89rIy9mGshw2asZv/HW1epFuIIxVW9SMFv2yI0QV8pDhMcqFzxQDA47rZUFyeEmOULinOGVBxe0x3l4vlYjCC/hcp03AyC1RjiqIJWZ4xYk5Ir5Pm9fZHEk9GGzR+YrD1iY2WH9XgRuB2wAtthrqODDNAH4pDAVNHVe0PN7uUBOrzuhoc6iT6ZmZnPhmMCGET48KiwLKwNLJu5o8l4w0ZffzoEJzR2nlttr+zSy4ldUx2pS7xwrh9fzKBSsJMMTprPv+s8ZlvKF/Lf6UCVSE5m/GppbnNUFcXipwZx/+TmaBaBq2jAOUfZHDhSXdiVwTtpwz6pwiSxv4c80kan1sa+HOE=
  strategy: git
```

The `api_key` field contains an encrypted Heroku API token by the Travis CI account's private key.

Run this command to create the yaml config section: `travis encrypt $(heroku auth:token) --add deploy.api_key`

See https://docs.travis-ci.com/user/deployment/heroku/ for more information.