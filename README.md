# Disk Bloater

The **Disk Bloater** program writes files with arbitrary data to disk at a configurable interval. It
is useful for testing disk consumption and monitoring ephemeral storage behavior.

The program writes an initial file of a specified size and then continuously writes additional files
at a given frequency.

## Configuration

The following parameters control the behavior of the program:

- **Target Directory**: Where the files are written.
- **Initial File Size**: The size of the first file written.
- **File Size**: The size of all subsequent files.
- **Write Interval**: The delay (in seconds) between writing each new file.
- **Total Files**: The total number of files to write.

Before each write, the program prints the filename and size to standard output.

## Setup

Create a Virtual Environment and Activate It

```shell
python -m venv venv
source venv/bin/activate
```

No dependencies to install, just using the standard library.

## Run the Program Locally

```shell
python disk_bloater.py --directory /tmp/bloat \
                       --initial-size 10240 \
                       --file-size 1024 \
                       --interval 5 \
                       -- total-files 5
```

This will:

- Write a **10K** initial file tp /tmp/bloat
- Write 4 **1K** files every **5 seconds** to `/tmp/bloat`.

## Build the Docker Image

```shell
./build.sh
```

## Keeping the node alive

When testing scenarios where pods exceed their ephemeral storage limits, it is important to keep the
node alive even if the pods are evicted. This can be achieved by running a little keep-alive pod on
the target node.

```
echo '
apiVersion: v1
kind: Pod
metadata:
  name: keep-alive
  annotations:
    cluster-autoscaler.kubernetes.io/safe-to-evict: "false"  # Prevents autoscaler from removing the node
spec:
  priorityClassName: system-cluster-critical # Prevents eviction
  nodeSelector:
  kubernetes.io/hostname: "the-node"  # Replace with your target node
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.9' | kubectl apply -f -
```

If the node has taints you'll need to add tolerations to the keep-alive pod.

## Create local Kubernetes cluster with 10GiB Disk (Optional)

If you want to test it locally without running on a real cluster, you can create a local Kubernetes
cluster. Let's use Minikube, which comes with built-in disk control.

First, we need a Docker engine. On Mac with ARM processor I recommend to run Colima as your Docker engine

```
❯ colima start --disk 10
INFO[0000] starting colima
INFO[0000] runtime: docker
INFO[0001] creating and starting ...                     context=vm
INFO[0001] downloading disk image ...                    context=vm
INFO[0024] provisioning ...                              context=docker
INFO[0025] starting ...                                  context=docker
INFO[0026] done
```

Now, we can create a cluster with a control plane node and a worker node.

```shell
❯ minikube start --profile=disk-bloater-test --disk-size=10g --nodes=2
😄  [disk-bloater-test] minikube v1.34.0 on Darwin 15.0.1 (arm64)
✨  Automatically selected the docker driver
📌  Using Docker Desktop driver with root privileges
👍  Starting "disk-bloater-test" primary control-plane node in "disk-bloater-test" cluster
🚜  Pulling base image v0.0.45 ...
🔥  Creating docker container (CPUs=2, Memory=1959MB) ...
🐳  Preparing Kubernetes v1.31.0 on Docker 27.2.0 ...
    ▪ Generating certificates and keys ...
    ▪ Booting up control plane ...
    ▪ Configuring RBAC rules ...
🔗  Configuring CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass

👍  Starting "disk-bloater-test-m02" worker node in "disk-bloater-test" cluster
🚜  Pulling base image v0.0.45 ...
🔥  Creating docker container (CPUs=2, Memory=1959MB) ...
🌐  Found network options:
    ▪ NO_PROXY=192.168.49.2
🐳  Preparing Kubernetes v1.31.0 on Docker 27.2.0 ...
    ▪ env NO_PROXY=192.168.49.2
🔎  Verifying Kubernetes components...
🏄  Done! kubectl is now configured to use "disk-bloater-test" cluster and "default" namespace by default
```

Let's verify all is well and all the pods are running. Note that all the control plane components run on the control
plane node. On the worker node there are only only the kindnet and kube-proxy networking components.

```
❯ kubectl get po -A -o wide
NAMESPACE     NAME                                        READY   STATUS    RESTARTS        AGE     IP             NODE                    NOMINATED NODE   READINESS GATES
kube-system   coredns-6f6b679f8f-7gz2t                    1/1     Running   2 (3m23s ago)   3m50s   10.244.0.2     disk-bloater-test       <none>           <none>
kube-system   etcd-disk-bloater-test                      1/1     Running   0               3m56s   192.168.49.2   disk-bloater-test       <none>           <none>
kube-system   kindnet-2dxb7                               1/1     Running   0               3m50s   192.168.49.2   disk-bloater-test       <none>           <none>
kube-system   kindnet-hp9tz                               1/1     Running   0               3m43s   192.168.49.3   disk-bloater-test-m02   <none>           <none>
kube-system   kube-apiserver-disk-bloater-test            1/1     Running   0               3m56s   192.168.49.2   disk-bloater-test       <none>           <none>
kube-system   kube-controller-manager-disk-bloater-test   1/1     Running   0               3m56s   192.168.49.2   disk-bloater-test       <none>           <none>
kube-system   kube-proxy-hxwx6                            1/1     Running   0               3m50s   192.168.49.2   disk-bloater-test       <none>           <none>
kube-system   kube-proxy-pk4wh                            1/1     Running   0               3m43s   192.168.49.3   disk-bloater-test-m02   <none>           <none>
kube-system   kube-scheduler-disk-bloater-test            1/1     Running   0               3m56s   192.168.49.2   disk-bloater-test       <none>           <none>
kube-system   storage-provisioner                         1/1     Running   1 (3m20s ago)   3m54s   192.168.49.2   disk-bloater-test       <none>           <none>
```

Let's taint the control plane node to make sure nothing is scheduled on it, because we are going to perform some destructive operations.

```
❯ kubectl taint nodes disk-bloater-test node-role.kubernetes.io/control-plane=:NoSchedule
node/disk-bloater-test tainted
``` 

## Deploy to Kubernetes

You may want to deploy more than one pod to test the behavior of the node under different
conditions.

For example, to deploy two pods called disk-bloater-1 and disk-bloater-2 that will write 3 files
each (600 MiB initial file + two additional 100 MiB files):

```
for i in 1 2; do
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: disk-bloater-$i
  labels:
    app: disk-bloater
spec:
  restartPolicy: Never
  containers:
    - name: disk-bloater
      image: g1g1/disk-bloater:latest
      args:
        - "--directory"
        - "/mnt/disk-bloat/$i"
        - "--initial-size"
        - "419430400"  # 400 MiB initial file
        - "--file-size"
        - "104857600"   # 100 MiB per additional file
        - "--interval"
        - "60"           # Write every minute
        - "--total-files"
        - "3"
      resources:
        limits:
          cpu: 500m
          ephemeral-storage: 8Gi
          memory: 512Mi
        requests:
          cpu: 250m
          ephemeral-storage: 3Gi
          memory: 10Mi
      volumeMounts:
        - name: bloat-volume
          mountPath: /mnt/disk-bloat
  volumes:
    - name: bloat-volume
      emptyDir: {}
EOF
done
```

## Investigating the node

### Starting a debug pod on the target node

Let's get the name of a disk-bloater pod and its node

```
POD_NAME=$(kubectl get pods -l app=disk-bloater --no-headers -o name | head -n 1)
NODE_NAME=$(kubectl get $POD_NAME -o jsonpath='{.spec.nodeName}')
```

Now we can run a privileged debug pod on the node with the same node selector as
the disk-bloater pod. It also mounts the host file system at /host in the container.

```shell
kubectl run debug-shell --rm -it --image=g1g1/py-kube \
  --overrides='{
    "apiVersion": "v1",
    "spec": {
      "hostPID": true,
      "hostNetwork": true,
      "nodeSelector": {
        "kubernetes.io/hostname": "'"$NODE_NAME"'"
      },
      "volumes": [{
        "name": "host-root",
        "hostPath": {
          "path": "/",
          "type": "Directory"
        }
      }],
      "containers": [{
        "name": "debug",
        "image": "g1g1/py-kube",
        "stdin": true,
        "tty": true,
        "securityContext": {
          "privileged": true
        },
        "volumeMounts": [{
          "mountPath": "/host",
          "name": "host-root"
        }],
        "command": ["bash"]
      }]
    }
  }'
```

You should drop into a shell like so:

```
If you don't see a command prompt, try pressing enter.
root@minikube:/app#
```

This method will work to get a shell on the node of any Kubernetes cluster as long as you have
permissions to run privileged pods. Minikube offers a simpler way to get a shell on the node via
`minikube ssh`, but it doesn't give you root access, and you can't examine the host filesystem.

```shell
❯ minikube ssh
docker@minikube:~$ ls /host
ls: cannot access '/host': No such file or directory
```

### Check disk usage

We have a total of 8.7 GiB of disk space available on the node and 4.2G is in use.

```
root@minikube:/app# df -h /host
Filesystem      Size  Used Avail Use% Mounted on
overlay         8.7G  3.2G  5.5G  37% /host
```

Let's see where the disk space is being used. We can see that the /host directory takes up about 4.5
GiB

```
root@minikube:/host/var/lib/kubelet/pods# du -ah --max-depth=1  /host 2>/dev/null | sort -rh | head -5
4.5G	/host
3.4G	/host/var
1.1G	/host/usr
77M	/host/opt
9.3M	/host/run
```

All the interesting stuff is in the /host/var/lib directory. Let's see what's in there. The `docker`
directory takes a big chunk of 1.9 GiB, and then we have the `kubelet` directory taking up 1.2 GiB.
This is where our pods and their ephemeral storage live.

```
root@minikube:/host/var/lib/kubelet/pods# du -ah --max-depth=1 /host/var/lib 2>/dev/null | sort -rh | head -5
3.4G	/host/var/lib
1.9G	/host/var/lib/docker
1.2G	/host/var/lib/kubelet
302M	/host/var/lib/minikube
8.2M	/host/var/lib/dpkg
```

Within the /host/var/lib/kubelet/pods directory, we can see that our empty-dir volumes taking about
600 MiB each

```
root@minikube:/host/var/lib/kubelet/pods# du -ah --max-depth=5 /host/var/lib/kubelet/pods 2>/dev/null | sort -rh | grep bloat-volume/ | grep -v ready
601M	/host/var/lib/kubelet/pods/6f974e65-d039-45e7-81f6-b066547a0553/volumes/kubernetes.io~empty-dir/bloat-volume/1
601M	/host/var/lib/kubelet/pods/5212e219-7ecf-4cde-9c94-6d0c82c17c74/volumes/kubernetes.io~empty-dir/bloat-volume/2
```

### Saturate the disk

Let's see what happens when we saturate the disk. We can do this by deploying another disk-bloater
pod. Note that it only requests 1 GiB of ephemeral storage to fit on the node, but it will use much
more disk space. The initial file is 400 MiB, and every 3 seconds it will write another 100 MiB
file for a total of 40 files for a total of 4.3 GiB. But, it will exceed its limit of 3.2 GiB much earlier.

```
echo '
apiVersion: v1
kind: Pod
metadata:
  name: disk-bloater-3
  labels:
    app: disk-bloater
spec:
  restartPolicy: Never
  containers:
    - name: disk-bloater
      image: g1g1/disk-bloater:latest
      args:
        - "--directory"
        - "/mnt/disk-bloat/3"
        - "--initial-size"
        - "419430400"  # 400 MiB initial file
        - "--file-size"
        - "104857600"   # 100 MiB per additional file
        - "--interval"
        - "3"           # Write another file every 3 seconds
        - "--total-files"
        - "40"
      resources:
        limits:
          cpu: 500m
          ephemeral-storage: 3.2Gi
          memory: 512Mi
        requests:
          cpu: 250m
          ephemeral-storage: 1Gi
          memory: 10Mi
      volumeMounts:
        - name: bloat-volume
          mountPath: /mnt/disk-bloat
  volumes:
    - name: bloat-volume
      emptyDir: {}' | kubectl apply -f -
```

The pod will allocate more and more disk, until it exceeds its limits and then it gets evicted.

```
root@minikube:/host/var/lib/kubelet/pods# df -h /host | head -5
Filesystem      Size  Used Avail Use% Mounted on
overlay         8.7G  8.6G   80M 100% /host
root@minikube:/host/var/lib/kubelet/pods# df -h /host | head -5
Filesystem      Size  Used Avail Use% Mounted on
overlay         8.7G  8.6G   80M 100% /host
root@minikube:/host/var/lib/kubelet/pods# df -h /host | head -5
Filesystem      Size  Used Avail Use% Mounted on
overlay         8.7G  8.6G   80M 100% /host
root@minikube:/host/var/lib/kubelet/pods# df -h /host | head -5
Filesystem      Size  Used Avail Use% Mounted on
overlay         8.7G  8.6G   80M 100% /host
```

Here are the pod's events
```
❯ kubectl describe po disk-bloater-3 | rg Events: -A 10
Events:
  Type     Reason     Age    From               Message
  ----     ------     ----   ----               -------
  Normal   Scheduled  5m14s  default-scheduler  Successfully assigned default/disk-bloater-3 to disk-bloater-test-m02
  Normal   Pulling    5m13s  kubelet            Pulling image "g1g1/disk-bloater:latest"
  Normal   Pulled     5m12s  kubelet            Successfully pulled image "g1g1/disk-bloater:latest" in 1.359s (1.359s including waiting). Image size: 146402249 bytes.
  Normal   Created    5m12s  kubelet            Created container disk-bloater
  Normal   Started    5m12s  kubelet            Started container disk-bloater
  Warning  Evicted    3m23s  kubelet            Pod ephemeral local storage usage exceeds the total limit of containers 3435973836800m.
  Normal   Killing    3m23s  kubelet            Stopping container disk-bloater
```

On Minikube when the pod is evicted its ephemeral storage is immediately released