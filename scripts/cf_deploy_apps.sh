#!/bin/bash

#cf push vmwarechargepoint-workers -f manifest_workers.yml --health-check-type none
#cf push vmwarechargepoint-gui -f manifest_gui.yml

cf push -f manifest.yml