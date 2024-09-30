#!/bin/bash --login
set -x # Enable debugging
echo "pulling and Checkout API tag-------------------------------------------"
GIT_SSH_COMMAND="ssh -o KexAlgorithms=ecdh-sha2-nistp521" git fetch --tags jenkins@10.44.0.51:/var/lib/jenkins/workspace/2024-Q3-EMR-pipeline-newIMG-1/BHT-EMR-API -f
git checkout v5.0.4 -f
git describe > HEAD
echo "____________________________________________"
export PATH=$PATH:/home/emr-user/.rbenv/bin
export PATH=$PATH:/home/emr-user/.rbenv/shims
echo "ruby setup"
source ~/.bashrc
rbenv local 3.2.0
echo "____________________________________________"
echo "Installing Local Gems"
echo "____________________________________________"
bundle install --local
echo "--------------------------------------------"
echo "running bin_update art"
echo "____________________________________________"
./bin/update_art_metadata.sh production
echo "____________________________________________"
