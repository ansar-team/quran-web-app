# Terraform configuration for Yandex Cloud
# Purpose: autoscaled instance group running FastAPI behind ALB (HTTP+HTTPS) + Managed PostgreSQL

terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.13"
    }
  }
}

provider "yandex" {
  zone = var.zone
}

# --------------------
# Network
# --------------------
resource "yandex_vpc_network" "app_network" {
  name = "telegram-app-network"
}

resource "yandex_vpc_subnet" "app_subnet" {
  name           = "telegram-app-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.app_network.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

# --------------------
# Security Group
# --------------------
resource "yandex_vpc_security_group" "app_sg" {
  name        = "telegram-app-sg"
  network_id  = yandex_vpc_network.app_network.id

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTPS"
    port           = 443
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
    # v4_cidr_blocks = [var.allow_ssh_from] # more strict!
  }

  ingress {
    protocol       = "TCP"
    description    = "App port (internal)"
    port           = 8000
    v4_cidr_blocks = ["192.168.10.0/24"]
  }

  egress {
    protocol       = "ANY"
    description    = "Outbound"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# --------------------
# Managed PostgreSQL
# --------------------
resource "yandex_mdb_postgresql_cluster" "app_db" {
  name        = "telegram-app-db"
  environment = "PRODUCTION"
  network_id  = yandex_vpc_network.app_network.id

  config {
    version = 15
    resources {
      resource_preset_id = "s2.micro"
      disk_type_id       = "network-ssd"
      disk_size          = 20
    }

    access {
      web_sql = true
    }

    postgresql_config = {
      max_connections                   = 100
      enable_parallel_hash              = true
      autovacuum_vacuum_scale_factor    = 0.34
      default_transaction_isolation  = 2
    }
  }

  host {
    zone      = var.zone
    subnet_id = yandex_vpc_subnet.app_subnet.id
  }

  maintenance_window {
    type = "ANYTIME"
  }

  lifecycle {
    ignore_changes = [
      config,
      maintenance_window,
    ]
  }
}

resource "yandex_mdb_postgresql_user" "app_user" {
  cluster_id = yandex_mdb_postgresql_cluster.app_db.id
  name       = var.db_username
  password   = var.db_password
}

resource "yandex_mdb_postgresql_database" "app_database" {
  cluster_id = yandex_mdb_postgresql_cluster.app_db.id
  name       = "telegram_app"
  owner      = yandex_mdb_postgresql_user.app_user.name
  lc_collate = "en_US.UTF-8"
  lc_type    = "en_US.UTF-8"

  depends_on = [yandex_mdb_postgresql_user.app_user]
}

# If you want to automate certificate creation
# --------------------
# Certificate (Yandex Certificate Manager)
# --------------------
# resource "yandex_cm_certificate" "app_cert" {
#   name    = "telegram-app-cert"
#   # count = length(var.certificate_domains) > 0 ? 1 : 0
#   domains = var.certificate_domains
#
#   managed {
#     challenge_type = "DNS_CNAME"
#     challenge_count = 1
#   }
# }
#
# resource "yandex_dns_recordset" "app_cert" {
#   count   = yandex_cm_certificate.app_cert.managed[0].challenge_count
#   zone_id = var.zone
#   name    = yandex_cm_certificate.app_cert.challenges[count.index].dns_name
#   type    = yandex_cm_certificate.app_cert.challenges[count.index].dns_type
#   data    = [yandex_cm_certificate.app_cert.challenges[count.index].dns_value]
#   ttl     = 60
# }
#
# data "yandex_cm_certificate" "app_cert" {
#   depends_on      = [yandex_dns_recordset.app_cert]
#   certificate_id  = yandex_cm_certificate.app_cert.id
#   wait_validation = true
# }

# --------------------
# Instance Group (autoscaled)
# --------------------
resource "yandex_compute_instance_group" "app_group" {
  name               = "telegram-app-group"
  service_account_id = var.service_account_id
  folder_id          = var.yandex_folder_id

  instance_template {
    platform_id = "standard-v3"

    resources {
      cores  = 2
      memory = 4
    }

    boot_disk {
      initialize_params {
        image_id = var.image_id
        size = 20
        type = "network-ssd"
      }
    }

    network_interface {
      subnet_ids = [yandex_vpc_subnet.app_subnet.id]
      nat       = true
      security_group_ids = [yandex_vpc_security_group.app_sg.id]
    }

    # For Linux users
    # metadata = {
    #   ssh-keys = "ubuntu:${file("~/.ssh/id_rsa.pub")}"
    #   user-data = file("${path.module}/cloud-config.yaml")
    # }

    # For Windows users
    metadata = {
      ssh-keys  = "amir:${file("C:/Users/amira/.ssh/id_ed25519.pub")}"
      # user-data = templatefile("${path.module}/cloud-config.yaml", {
      # user-data = templatefile("C:/Users/amira/PycharmProjects/quran-web-app/infrastructure/cloud-config.yaml", {
      #   docker_image       = "cr.yandex/${var.registry_id}/telegram-app:latest"
      #   database_url       = "postgresql://${var.db_username}:${var.db_password}@${yandex_mdb_postgresql_cluster.app_db.host[0].fqdn}:5432/telegram_app"
      #   telegram_bot_token = var.telegram_bot_token
      # })
        user-data = <<-EOF
          #cloud-config
          write_files:
              path: /etc/telegram.env
              permissions: '0600'
              content: |
                DATABASE_URL=postgresql://${var.db_username}:${var.db_password}@${yandex_mdb_postgresql_cluster.app_db.host[0].fqdn}:5432/telegram_app
                TELEGRAM_BOT_TOKEN=${var.telegram_bot_token}
          runcmd:
          - docker pull cr.yandex/${var.registry_id}/telegram-app:latest
          - docker run -d \
            --restart=always \
            --name fastapi-app \
            --env-file /etc/telegram.env \
            -p 8000:8000 \
            cr.yandex/${var.registry_id}/telegram-app:latest
        EOF
      # user-data = file("${path.module}/cloud-config.yaml")
      # user-data = templatefile("C:/Users/amira/PycharmProjects/quran-web-app/infrastructure/cloud-config.yaml")
      # enable-oslogin = "true"
      # enable-yandex-cloud-monitoring = "true"
      # enable-yandex-cloud-logging = "true"
    }
  }

  scale_policy {
    auto_scale {
      initial_size = 1
      min_zone_size = 1
      max_size      = 5
      measurement_duration = 60
      cpu_utilization_target = 60.0
    }
  }

  allocation_policy {
    zones = [var.zone]
  }

  deploy_policy {
    max_creating = 2
    max_deleting = 1
    max_expansion = 1
    max_unavailable = 2
  }

  load_balancer {
    target_group_name = "telegram-app-tg"
  }

  depends_on = [yandex_mdb_postgresql_database.app_database]
}

# --------------------
# Application Load Balancer (ALB) with HTTP + HTTPS listeners
# --------------------
resource "null_resource" "wait_for_instance_group" {
  depends_on = [yandex_compute_instance_group.app_group]

  # For linux, This resource is used to wait compute instances initialization
  # provisioner "local-exec" {
  #   command = "echo 'Waiting 5 minutes for instance group target group propagation...' && sleep 300"
  # }
  provisioner "local-exec" {
    command = "powershell -Command \"Write-Host 'Waiting 5 minutes for instance group target group propagation...'; Start-Sleep -Seconds 300\""
  }
}

resource "yandex_alb_target_group" "app_target_group" {
  name = "app-alb-target-group"

  dynamic "target" {
    for_each = yandex_compute_instance_group.app_group.instances
    content {
      subnet_id  = target.value.network_interface[0].subnet_id
      ip_address = target.value.network_interface[0].ip_address
    }
  }
}

resource "yandex_alb_backend_group" "app_backend" {
  name = "app-backend"

  http_backend {
    name             = "backend-1"
    port             = 80
    target_group_ids = [yandex_alb_target_group.app_target_group.id]
  }
}

resource "yandex_alb_http_router" "app_router" {
  name = "app-router"
}

resource "yandex_alb_load_balancer" "app_lb" {
  name = "app-https-lb"
  network_id = yandex_vpc_network.app_network.id

  allocation_policy {
    location {
      zone_id   = "ru-central1-a"
      subnet_id = yandex_vpc_subnet.app_subnet.id
    }
  }

  listener {
    name = "http-listener"
    endpoint {
      address {
        external_ipv4_address {
        }
      }
      ports = [80]
    }
    http {
      redirects {
        http_to_https = true
      }
    }
  }

  listener {
    name = "https-listener"
    endpoint {
      address {
        external_ipv4_address {}
      }
      ports = [443]
    }

    tls {
      default_handler {
        http_handler {
          http_router_id = yandex_alb_http_router.app_router.id
        }
        # If you plan to create certificate automatically
        # certificate_ids = length(yandex_cm_certificate.app_cert) > 0 ? [yandex_cm_certificate.app_cert[0].id] : []
        certificate_ids = [var.existing_cert_id]
      }
    }
  }

  depends_on = [yandex_alb_backend_group.app_backend]
}

resource "yandex_alb_virtual_host" "app_host" {
  name = "app-vhost"
  http_router_id = yandex_alb_http_router.app_router.id
  authority = ["enimatrix.ru", ".enimatrix.ru"]

  route {
    name = "app-vhost-route"
    http_route {
      http_route_action {
        backend_group_id = yandex_alb_backend_group.app_backend.id
      }
    }
  }
}
