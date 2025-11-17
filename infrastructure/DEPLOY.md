# Infrastructure deployment

To automatically set up the infrastructure you should prepare an environment for that. This guide is
structured for Yandex Cloud, therefore we use their [guide](https://yandex.cloud/ru/docs/tutorials/infrastructure-management/terraform-quickstart).
It covers base things like creating a cloud account, setting payment account, downloading terraform, setting environment
variables. 

In short it will look like this:
Here's a complete step-by-step guide to using Terraform with Yandex Cloud:

### 1. Install Prerequisites

#### Install Terraform
On Ubuntu/Debian:
```bash
# Install prerequisites
sudo apt update
sudo apt install -y curl gnupg software-properties-common

# Add HashiCorp repository
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Install Terraform
sudo apt update
sudo apt install terraform
```

On macOS:
```bash
# Using Homebrew
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Or download from website: https://www.terraform.io/downloads
```

On Windows:
- Download from [terraform.io/downloads](https://www.terraform.io/downloads) and set it according to [instructions](https://learn.hashicorp.com/tutorials/terraform/install-cli?in=terraform/aws-get-started)
- Or download from [yandex archive](https://hashicorp-releases.yandexcloud.net/terraform/)
- Or use Chocolatey: `choco install terraform`

### 2. Install Yandex Cloud CLI
```bash
# Install YC CLI
curl -sSL https://storage.yandex-cloud.net/yandexcloud-yc/install.sh | bash
source ~/.bashrc

# Or follow official instructions: https://cloud.yandex.ru/docs/cli/quickstart
```

Verify installations:
```bash
terraform --version
yc --version
```

### 3. Set Up Yandex Cloud Authentication

Login to Yandex Cloud:
```bash
yc init
```

Create Service Account for Terraform:
```bash
# Create service account
yc iam service-account create --name terraform-sa --description "For Terraform automation"

# Get service account ID
yc iam service-account get terraform-sa

# Assign roles to service account
yc resource-manager folder add-access-binding <your-folder-id> \
  --role editor \
  --subject serviceAccount:<service-account-id>
  
yc resource-manager folder add-access-binding \
  --id <your-folder-id> \
  --role alb.editor \
  --service-account-id <service-account-id>
  
yc resource-manager folder add-access-binding \
  --id <your-folder-id> \
  --role certificate-manager.editor \
  --service-account-id <service-account-id>
  
yc resource-manager folder add-access-binding \
  --id <your-folder-id> \
  --role certificate-manager.certificates.downloader \
  --service-account-id <service-account-id>

# To get <service-account-name> you use `yc iam service-account get <service-account-id>`
# 
yc iam service-account add-access-binding --id <service-account-id> \
  --role container-registry.images.puller \
  --service-account-name <service-account-name>
  

# Check the access
yc iam service-account list-access-bindings <service-account-id>
```
Output for last command:
```
+---------------------------------------------+----------------+----------------------+
|                   ROLE ID                   |  SUBJECT TYPE  |      SUBJECT ID      |
+---------------------------------------------+----------------+----------------------+
| alb.editor                                  | serviceAccount | ajeiui3ihmv6qd6pvncv |
| container-registry.images.puller            | serviceAccount | ajeiui3ihmv6qd6pvncv |
| certificate-manager.editor                  | serviceAccount | ajeiui3ihmv6qd6pvncv |
| certificate-manager.certificates.downloader | serviceAccount | ajeiui3ihmv6qd6pvncv |
+---------------------------------------------+----------------+----------------------+
```
```
# Create authorized key for service account
yc iam key create --service-account-name terraform-sa --output key.json
```

Set Environment Variables:
```bash
# Get your cloud and folder IDs
yc config list

# Set environment variables
export YC_CLOUD_ID=$(yc config get cloud-id)
export YC_FOLDER_ID=$(yc config get folder-id)
export YC_TOKEN=$(yc iam create-token)
```

In Windows PowerShell:
```bash
$Env:YC_TOKEN=$(yc iam create-token --impersonate-service-account-id <service-account_id>)
$Env:YC_CLOUD_ID=$(yc config get cloud-id)
$Env:YC_FOLDER_ID=$(yc config get folder-id)
```

### 3. Terraform Project Structure

Directory has following structure:
```
quran-web-app/
├── infrastructure/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── terraform.tfvars
    └── cloud-config.yaml
```

All this goes until [creating file configurations](https://yandex.cloud/ru/docs/tutorials/infrastructure-management/terraform-quickstart#configure-terraform).
We already have file configurations. So now, let's look into which secrets you need to prepare 

### 4. Prepare secrets

In `variables.tf` you have the following variables:
- yandex_cloud_id
- yandex_folder_id
- service_account_id
- db_username
- db_password
- certificate_domains
- telegram_bot_token
- registry_id

To set them up follow the following:
```bash
# Get cloud ID
yc resource-manager cloud list

# See table of service accounts, check their IDs
yc iam service-account list

# Get information for service account you created recently
yc iam service-account get --id <service_account_id>
```
Output for last command
```bash
id: <service_account_id>
folder_id: <folder_id>
created_at: "2025-10-26T13:22:23Z"
name: terraform-sa
description: For Terraform automation
last_authenticated_at: "2025-10-30T03:10:00Z"
```
Use these IDs to populate first two variables in `terraform.tfvars`:
```
yandex_cloud_id = <cloud_id>
yandex_folder_id = <folder_id>
service_account_id = <service_account_id>
```
For variables for `db_username` and `db_password` you choose yourself. `telegram_bot_token` you get only via 
[BotFather](https://t.me/BotFather) (you can check in the internet how to do it). 

- certificate_domains
- registry_id


```
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "your-email@example.com" -f ~/.ssh/id_rsa_terraform

# Copy public key to use in terraform.tfvars
cat ~/.ssh/id_rsa_terraform.pub
```

### 5. Apply Terraform 

before applying configure provider [guide](https://yandex.cloud/ru/docs/tutorials/infrastructure-management/terraform-quickstart#configure-provider)

1. Navigate to infrastructure directory:
```bash
cd infrastructure
```
2. Initialize Terraform:
```bash
terraform init
```
3. Plan the deployment:
```bash
terraform plan -var="db_password=your-secure-password" -out=plan.out
```
4. Apply the configuration:
```bash
terraform apply plan.out

# Or apply directly:
terraform apply
```

## Useful Terraform Commands
Check current state:
```bash
terraform show
```
List resources:
```bash
terraform state list
```
Modify infrastructure:
```bash
# After changing .tf files
terraform plan
terraform apply
```