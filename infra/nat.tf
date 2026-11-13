module "fck_nat" {
  source  = "RaJiska/fck-nat/aws"
  version = "1.6.1"

  name          = local.name
  vpc_id        = aws_vpc.main.id
  subnet_id     = aws_subnet.public.id
  instance_type = "t4g.micro" # smallest free-tier-eligible type
  ha_mode       = false       # single EC2 instance, no ASG

  update_route_tables = true
  route_tables_ids    = { private = aws_route_table.private.id }
}
