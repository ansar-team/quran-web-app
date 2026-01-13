variable "yandex_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "zone" {
  description = "Zone"
  type        = string
  default     = "ru-central1-a"
}

variable "yandex_folder_id" {
  description = "Yandex Folder ID"
  type        = string
}

variable "service_account_id" {
  description = "Yandex service account ID"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "app_user"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "certificate_domains" {
  type    = list(string)
  default = []
}

variable "telegram_bot_token" {
  type      = string
  sensitive = true
}

variable "registry_id" {
  description = "Registry from which you pull image"
  type        = string
}

variable "existing_cert_id" {
  description = "ID of an existing valid certificate for enimatrix.ru"
  type        = string
}

variable "image_id" {
  description = "OS image"
  type        = string
}
