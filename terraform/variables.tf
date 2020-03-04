variable "appname" {
  type    = string
}

variable "environment" {
  type    = string
}

variable "location" {
  type    = string
}

variable "tenant_id" {
  type    = string
}

variable "appinsights_instrumentation_key" {
  type    = string
}

variable "maps_key" {
  type    = string
}

variable "nb_of_routes" {
  type    = number
  default = 100
  description = "Number of random routes to query per run of RandomRoutesGenerator"
}

variable "config_storage_id" {
  type    = string
}

variable "config_cities_url" {
  type    = string
}

variable "client_id" {
  type    = string
  description = "Service principal object id, such as Azure cli, that runs this terraform script"
}
