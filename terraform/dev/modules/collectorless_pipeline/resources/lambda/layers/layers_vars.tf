variable layer_name {
    default    = "default-layer"
}

variable layer_zip_path {
    default    = "layer.zip"
}

variable layer_requirements_path {
    type = string
}

variable compatible_runtimes {
    default = ["python3.10"]
}

variable layer_bucket {
    default = "dte-utils-bucket"
}