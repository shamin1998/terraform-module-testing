# Create pipeline Terraform resources

module pipeline {
    source = "./terraform/dev/modules/collectorless_pipeline" #"./modules/collectorless_pipeline"

    pipeline_uuid = var.pipeline_uuid

    aws_region = var.aws_region

    shared_params = var.shared_params

    state_table = var.state_table
    source_def = var.source_def
    transformer_def = var.transformer_def
    destination_def = var.destination_def

}