#!/bin/bash --login
echo "pulling and Checkout Core tag"
echo "--------------------------------------------"
git fetch --tags jenkins@10.44.0.51:/var/lib/jenkins/workspace/2024-Q3-EMR-pipeline-newIMG-1/HIS-Core-release -f
git checkout v1.15.2 -f
#git describe > HEAD
echo "____________________________________________"
