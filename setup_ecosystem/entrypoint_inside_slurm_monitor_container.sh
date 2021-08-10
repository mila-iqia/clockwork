#!/bin/sh

# 

# verify that the ssh keys are mounted are correct place
# verify that the config file is present

# One environment variable is going to specify which cluster
# we're going to be using.
# There's an open question about whether all that should be
# in the configuration file, or how we want to override certain
# values as arguments instead.
# Let's start with something that works, and then figure the rest later.

# Some environment variables are going to be needed in order to talk
# to the instances of
#    - prometheus
#    - elasticsearch
#    - mongodb



# if testing mode
#    do one thing
# else
#    scrape for realsies