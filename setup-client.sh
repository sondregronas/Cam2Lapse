# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get -y install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start docker service
systemctl enable docker
systemctl start docker

# Install resolvconf and setup Google DNS
sudo apt-get -y install resolvconf nscd && sudo resolvconf -u
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolvconf/resolv.conf.d/head

# Pull Cam2Lapse
docker pull ghcr.io/sondregronas/cam2lapse:latest

# Install Wireguard / Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Create file
cat << 'EOF' >> start.sh
# NOTE: CAM set to '' will result in "latest" being used, saves in folder "1" in the receiver
export RTSP_URL="rtsp://<CAMERA-IP>"
export SEND_TO_RECEIVER="y"
export CAM="CAM1"
export URL="https://<RECEIVER-IP>"
export TOKEN="1234567890"

docker run -d \
    -e RTSP_URL=$RTSP_URL \
    -e SEND=$SEND_TO_RECEIVER \
    -e CAM=$CAM \
    -e URL=$URL \
    -e TOKEN=$TOKEN \
    --restart unless-stopped \
    ghcr.io/sondregronas/cam2lapse:latest
EOF

tailscale up --accept-dns=false
