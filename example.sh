openstack --insecure server create --flavor m1.large --image ca70466d-5043-4cb6-a779-8a2b1cf303a4 --user-data /tmp/user-data-$i --~/.ssh/achbal-id_rsa student-key "ubuntu-$i-14.04.3-LTS"
