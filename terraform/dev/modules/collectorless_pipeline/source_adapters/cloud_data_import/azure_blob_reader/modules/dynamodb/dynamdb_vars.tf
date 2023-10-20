variable pipeline_uuid {
    type = string
}

variable "log_table" {

    type = object({
        primary_index = object({
            name = optional(string,"")
            name_prefix = optional(string,"azure-blob-source_log-table")
            hash_key = optional(string,"container_name")
            range_key = optional(string, "azure_blob_path")
        })
        
        sort_index = optional(object({
            name = optional(string, "log-table_sort-index")
            range_key = optional(string)
            projection_type = optional(string, "KEYS_ONLY")
            non_key_attributes = optional(list(string))
        })
        )

        optional_params = optional(map(string))
    })

    default = {
        primary_index = {
          name = ""
        }
        sort_index = {
          range_key = "log_timestamp"
        }   
    }
    
}