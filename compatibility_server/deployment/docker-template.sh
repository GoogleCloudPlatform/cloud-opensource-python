gcloud compute --project=gce-compatibility instance-templates create docker-template-test-v3 \
  --machine-type=n1-standard-4 \
  --network=projects/gce-compatibility/global/networks/default \
  --maintenance-policy=MIGRATE \
  --image=ubuntu-1804-lts-drawfork-shielded-v20181106 \
  --image-project=eip-images \
  --boot-disk-size=4000GB \
  --boot-disk-type=pd-standard \
  --boot-disk-device-name=docker-template \
  --metadata-from-file startup-script=docker-startup.sh

