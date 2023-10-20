variable pipeline_uuid {
    type = string
}

variable layer_name {
    default    = "AzurePythonSDKLayer"
}

variable layer_zip_path {
    default    = "layer.zip"
}

variable layer_requirements_path {
    default    = "./modules/layers/layer-requirements.txt"
}

