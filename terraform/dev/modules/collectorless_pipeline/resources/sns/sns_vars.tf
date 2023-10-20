# variable "pipeline_uuid" {
#     type = string
# }

variable "sns_topic_name" {
    type = string
    default = ""
}

variable "sns_topic_name_prefix" {
    default = "transformation_trigger_sns_topic"
}
