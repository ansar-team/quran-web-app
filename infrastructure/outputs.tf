output "load_balancer_ip" {
  description = "Application Load Balancer IP address"
  value = yandex_alb_load_balancer.app_lb.listener[0].endpoint[0].address[0].external_ipv4_address[0].address
}

output "compute_instance_group_name" {
  description = "VMs target group name"
  value = yandex_compute_instance_group.app_group.name
}

output "database_host" {
  description = "Database host FQDN"
  value = yandex_mdb_postgresql_cluster.app_db.host[0].fqdn
}
