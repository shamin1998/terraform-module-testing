#define variables
# locals {
#   layer_zip_path = "${var.layer_name}_${var.layer_zip_path}"
# }

# output testing_out {
#   value = var.layer_requirements_path
# }

# # create zip file from requirements.txt. Triggers only when the file is updated
# resource "null_resource" "install_and_zip_requirements" {
#   triggers = {
#     requirements = filesha1(var.layer_requirements_path)
#   }
#   # the command to install python and dependencies to the machine and zips
#   provisioner "local-exec" {
#     command = <<EOT
#       rm -rf python
#       mkdir python
#       pip3 install --platform manylinux2014_x86_64 --target python/ --implementation cp --python-version 3.10 --only-binary=:all: --upgrade -r ${var.layer_requirements_path}
#       zip -r ${local.layer_zip_path} python/
#     EOT
#   }
# }

# # define bucket for storing lambda layers
# resource "aws_s3_bucket" "lambda_layer_bucket" {
#   bucket = "${replace(var.layer_name, "_", "-")}-storage-bucket"
# }

# # upload zip file to s3
# resource "aws_s3_object" "lambda_layer_zip" {
#   bucket     = aws_s3_bucket.lambda_layer_bucket.id
#   key        = "lambda_layers/${var.layer_name}/${local.layer_zip_path}"
#   source     = local.layer_zip_path
#   depends_on = [null_resource.install_and_zip_requirements] # triggered only if the zip file is created
#   # etag = filemd5(local.layer_zip_path)
# }

# create lambda layer from s3 object
resource "aws_lambda_layer_version" "lambda_layer" {
  s3_bucket           = var.layer_bucket  #aws_s3_bucket.lambda_layer_bucket.id
  s3_key              = var.layer_zip_path #aws_s3_object.lambda_layer_zip.key
  layer_name          = var.layer_name
  compatible_runtimes = var.compatible_runtimes
#   skip_destroy        = true
  # depends_on          = [aws_s3_object.lambda_layer_zip] # triggered only if the zip file is uploaded to the bucket
  # source_code_hash = filebase64sha256(local.layer_zip_path)
}