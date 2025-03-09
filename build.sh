VERSION=0.1

echo $DOCKERHUB_PASSWORD | docker login -u $DOCKERHUB_USERNAME --password-stdin

# Create new builder if it doesn't exist yet
if ! docker buildx ls | grep -q "the-builder"; then
  docker buildx create --name the-builder --driver docker-container
fi
docker  buildx use --builder the-builder

docker buildx build \
   --platform linux/amd64,linux/arm64 \
   -t g1g1/disk-bloater:${VERSION} \
   -t g1g1/disk-bloater:latest \
   --push .
