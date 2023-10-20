variable "pipeline_uuid" {
  type = string
}

variable "bucket_name" {
  type = string
  default = ""
}

variable "bucket_name_prefix" {
  default     = "blob-storage-bucket"
}
