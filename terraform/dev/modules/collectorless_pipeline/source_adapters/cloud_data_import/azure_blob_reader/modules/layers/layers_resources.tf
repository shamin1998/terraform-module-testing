#define variables

# create zip file from requirements.txt. Triggers only when the file is updated
resource "null_resource" "lambda_layer" {
  triggers = {
    requirements = filesha1(var.layer_requirements_path)
  }
  # the command to install python and dependencies to the machine and zips
  provisioner "local-exec" {
    command = <<EOT
      rm -rf python
      mkdir python
      pip install --platform manylinux2014_x86_64 --target python/ --implementation cp --python-version 3.10 --only-binary=:all: --upgrade -r ${var.layer_requirements_path}
      zip -r ${var.layer_zip_path} python/
    EOT
  }
}

# define existing bucket for storing lambda layers
resource "aws_s3_bucket" "lambda_layer_bucket" {
  bucket = "azure-layer-storage-bucket-puuid-${var.pipeline_uuid}"
}

# upload zip file to s3
resource "aws_s3_object" "lambda_layer_zip" {
  bucket     = aws_s3_bucket.lambda_layer_bucket.id
  key        = "lambda_layers/${var.layer_name}/${var.layer_zip_path}"
  source     = var.layer_zip_path
  depends_on = [null_resource.lambda_layer] # triggered only if the zip file is created
  # etag = filemd5(var.layer_requirements_path)
}

# create lambda layer from s3 object
resource "aws_lambda_layer_version" "azureSDKlayer" {
  s3_bucket           = aws_s3_bucket.lambda_layer_bucket.id
  s3_key              = aws_s3_object.lambda_layer_zip.key
  layer_name          = var.layer_name
  compatible_runtimes = ["python3.10"]
#   skip_destroy        = true
  depends_on          = [aws_s3_object.lambda_layer_zip] # triggered only if the zip file is uploaded to the bucket
#   source_code_hash = "${filebase64sha256(var.layer_requirements_path)}"
}