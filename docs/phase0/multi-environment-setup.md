# Multi-Environment Setup with Infrastructure as Code

## Environment Architecture Overview

### Environment Strategy
```
Environment Hierarchy:
Development → Staging → Production
    ↓           ↓           ↓
  Testing    Validation   Live
  Debugging   Performance  Real Users
  Rapid Iterations Security   High Availability
  Full Access Limited Access  Restricted Access
```

### Environment Specifications

#### Development Environment
```
Purpose: Active development and unit testing
Access: Full development team access
Data: Anonymized sample data
Security: Basic security controls
Monitoring: Development-focused monitoring
Performance: Development-optimized configuration

Infrastructure:
- 2x Application Servers (small)
- 1x Database Server (small)
- 1x Cache Server (small)
- Basic Load Balancer
- Development Monitoring
- Shared Storage (100GB)
```

#### Staging Environment
```
Purpose: Integration testing and validation
Access: Development team + QA team
Data: Production-like test data
Security: Production-equivalent security
Monitoring: Production-like monitoring
Performance: Production-equivalent configuration

Infrastructure:
- 2x Application Servers (medium)
- 1x Database Server (medium)
- 1x Cache Server (medium)
- Production-like Load Balancer
- Production Monitoring Stack
- Shared Storage (500GB)
```

#### Production Environment
```
Purpose: Live system for end users
Access: Operations team only
Data: Real production data
Security: Full security controls
Monitoring: Comprehensive monitoring
Performance: Production-optimized configuration

Infrastructure:
- 4x Application Servers (large)
- 2x Database Servers (large, HA)
- 2x Cache Servers (large)
- Enterprise Load Balancer
- Full Monitoring Stack
- High Availability Storage (2TB)
```

#### Sandbox Environment
```
Purpose: Security testing and experimentation
Access: Security team only
Data: Synthetic security test data
Security: Isolated security controls
Monitoring: Security-focused monitoring
Performance: Variable for testing scenarios

Infrastructure:
- 1x Application Server (variable)
- 1x Database Server (variable)
- 1x Cache Server (variable)
- Isolated Network Segment
- Security Monitoring Only
- Ephemeral Storage (200GB)
```

---

## Infrastructure as Code (IaC) Framework

### Technology Stack
```
IaC Tool: Terraform
Configuration Management: Ansible
Container Orchestration: Kubernetes
Cloud Provider: AWS/Azure/GCP (based on university preference)
Version Control: Git
Secrets Management: HashiCorp Vault
```

### Terraform Structure
```
terraform/
├── modules/
│   ├── compute/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── network/
│   ├── storage/
│   ├── database/
│   ├── security/
│   └── monitoring/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   ├── production/
│   └── sandbox/
├── global/
│   ├── iam.tf
│   ├── s3.tf
│   └── provider.tf
└── scripts/
    ├── init.sh
    ├── plan.sh
    ├── apply.sh
    └── destroy.sh
```

### Core Terraform Modules

#### Compute Module
```terraform
# modules/compute/main.tf
resource "aws_instance" "app_servers" {
  count           = var.instance_count
  ami             = var.ami_id
  instance_type   = var.instance_type
  subnet_id       = var.subnet_ids[count.index]
  security_groups = [var.security_group_id]
  
  tags = merge(
    var.common_tags,
    {
      Name = "${var.environment}-app-server-${count.index + 1}"
      Environment = var.environment
    }
  )
  
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    environment = var.environment
    role        = "application"
  }))
}

resource "aws_lb_target_group" "app_tg" {
  name     = "${var.environment}-app-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  
  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
  
  tags = var.common_tags
}
```

#### Network Module
```terraform
# modules/network/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(
    var.common_tags,
    {
      Name = "${var.environment}-vpc"
      Environment = var.environment
    }
  )
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(
    var.common_tags,
    {
      Name = "${var.environment}-private-subnet-${count.index + 1}"
      Type = "Private"
    }
  )
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(
    var.common_tags,
    {
      Name = "${var.environment}-public-subnet-${count.index + 1}"
      Type = "Public"
    }
  )
}
```

#### Database Module
```terraform
# modules/database/main.tf
resource "aws_db_instance" "main" {
  identifier = "${var.environment}-db"
  
  engine         = "postgres"
  engine_version = "14.6"
  instance_class = var.instance_class
  
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_encrypted     = true
  storage_type          = "gp2"
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [var.security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window
  
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.final_snapshot_identifier
  
  tags = merge(
    var.common_tags,
    {
      Name = "${var.environment}-database"
      Environment = var.environment
    }
  )
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids
  
  tags = var.common_tags
}
```

### Environment-Specific Configurations

#### Development Environment
```terraform
# environments/dev/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket = "cbt-terraform-state"
    key    = "dev/terraform.tfstate"
    region = "us-west-2"
    encrypt = true
  }
}

module "network" {
  source = "../../modules/network"
  
  environment = "dev"
  vpc_cidr    = "10.0.0.0/16"
  
  private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24"]
  availability_zones   = ["us-west-2a", "us-west-2b"]
  
  common_tags = {
    Project     = "CBT"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "compute" {
  source = "../../modules/compute"
  
  environment     = "dev"
  instance_count  = 2
  instance_type   = "t3.micro"
  ami_id          = "ami-0c02fb55956c7d316"
  subnet_ids      = module.network.private_subnet_ids
  security_group_id = module.security.app_security_group_id
  
  common_tags = {
    Project     = "CBT"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "database" {
  source = "../../modules/database"
  
  environment              = "dev"
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  max_allocated_storage    = 100
  db_name                 = "cbt_dev"
  db_username             = "cbt_admin"
  db_password             = var.db_password
  security_group_id       = module.security.db_security_group_id
  private_subnet_ids      = module.network.private_subnet_ids
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  skip_final_snapshot    = true
  
  common_tags = {
    Project     = "CBT"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}
```

#### Production Environment
```terraform
# environments/production/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket = "cbt-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-west-2"
    encrypt = true
    dynamodb_table = "terraform-locks"
  }
}

module "network" {
  source = "../../modules/network"
  
  environment = "production"
  vpc_cidr    = "10.1.0.0/16"
  
  private_subnet_cidrs = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  public_subnet_cidrs  = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]
  availability_zones   = ["us-west-2a", "us-west-2b", "us-west-2c"]
  
  common_tags = {
    Project     = "CBT"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

module "compute" {
  source = "../../modules/compute"
  
  environment     = "production"
  instance_count  = 4
  instance_type   = "t3.large"
  ami_id          = "ami-0c02fb55956c7d316"
  subnet_ids      = module.network.private_subnet_ids
  security_group_id = module.security.app_security_group_id
  
  common_tags = {
    Project     = "CBT"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

module "database" {
  source = "../../modules/database"
  
  environment              = "production"
  instance_class          = "db.r5.large"
  allocated_storage       = 500
  max_allocated_storage    = 2000
  db_name                 = "cbt_prod"
  db_username             = "cbt_admin"
  db_password             = var.db_password
  security_group_id       = module.security.db_security_group_id
  private_subnet_ids      = module.network.private_subnet_ids
  backup_retention_period = 30
  backup_window          = "02:00-03:00"
  maintenance_window     = "sun:03:00-sun:05:00"
  skip_final_snapshot    = false
  final_snapshot_identifier = "cbt-prod-final-snapshot"
  
  common_tags = {
    Project     = "CBT"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}
```

---

## Configuration Management with Ansible

### Ansible Structure
```
ansible/
├── inventory/
│   ├── dev.ini
│   ├── staging.ini
│   ├── production.ini
│   └── sandbox.ini
├── playbooks/
│   ├── common/
│   │   ├── base-setup.yml
│   │   ├── security-hardening.yml
│   │   └── monitoring.yml
│   ├── application/
│   │   ├── deploy.yml
│   │   ├── configure.yml
│   │   └── update.yml
│   └── database/
│       ├── setup.yml
│       ├── backup.yml
│       └── maintenance.yml
├── roles/
│   ├── common/
│   ├── application/
│   ├── database/
│   ├── security/
│   └── monitoring/
├── group_vars/
│   ├── all.yml
│   ├── dev.yml
│   ├── staging.yml
│   ├── production.yml
│   └── sandbox.yml
└── host_vars/
```

### Example Playbook
```yaml
# playbooks/application/deploy.yml
---
- name: Deploy CBT Application
  hosts: application_servers
  become: yes
  vars:
    app_version: "{{ app_version | default('latest') }}"
    environment: "{{ ansible_environment }}"
  
  tasks:
    - name: Create application directory
      file:
        path: /opt/cbt
        state: directory
        mode: '0755'
        owner: cbt
        group: cbt
    
    - name: Deploy application code
      git:
        repo: "https://github.com/custech/cbt-app.git"
        dest: /opt/cbt/app
        version: "{{ app_version }}"
        force: yes
      notify: restart application
    
    - name: Install application dependencies
      pip:
        requirements: /opt/cbt/app/requirements.txt
        virtualenv: /opt/cbt/venv
        state: present
    
    - name: Configure application
      template:
        src: config.py.j2
        dest: /opt/cbt/app/config.py
        mode: '0640'
        owner: cbt
        group: cbt
      notify: restart application
    
    - name: Ensure application service is running
      systemd:
        name: cbt-app
        state: started
        enabled: yes
  
  handlers:
    - name: restart application
      systemd:
        name: cbt-app
        state: restarted
```

---

## Kubernetes Configuration

### Namespace Configuration
```yaml
# k8s/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cbt-dev
  labels:
    environment: development
    project: cbt
---
apiVersion: v1
kind: Namespace
metadata:
  name: cbt-staging
  labels:
    environment: staging
    project: cbt
---
apiVersion: v1
kind: Namespace
metadata:
  name: cbt-production
  labels:
    environment: production
    project: cbt
---
apiVersion: v1
kind: Namespace
metadata:
  name: cbt-sandbox
  labels:
    environment: sandbox
    project: cbt
```

### Application Deployment
```yaml
# k8s/application/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cbt-app
  namespace: {{ .Values.environment }}
spec:
  replicas: {{ .Values.replicas }}
  selector:
    matchLabels:
      app: cbt-app
  template:
    metadata:
      labels:
        app: cbt-app
        environment: {{ .Values.environment }}
    spec:
      containers:
      - name: cbt-app
        image: "cbt/app:{{ .Values.version }}"
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cbt-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: cbt-config
              key: redis-url
        resources:
          requests:
            memory: "{{ .Values.resources.requests.memory }}"
            cpu: "{{ .Values.resources.requests.cpu }}"
          limits:
            memory: "{{ .Values.resources.limits.memory }}"
            cpu: "{{ .Values.resources.limits.cpu }}"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Helm Values by Environment
```yaml
# helm/values-dev.yaml
environment: development
replicas: 2
version: latest

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 4
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  host: dev.cbt.custech.edu.ng
  tls: true
```

```yaml
# helm/values-production.yaml
environment: production
replicas: 4
version: "1.0.0"

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

autoscaling:
  enabled: true
  minReplicas: 4
  maxReplicas: 10
  targetCPUUtilizationPercentage: 60

ingress:
  enabled: true
  host: cbt.custech.edu.ng
  tls: true
```

---

## Environment Management Procedures

### Environment Creation Workflow
```
1. Planning Phase
   - Define environment requirements
   - Create infrastructure specifications
   - Estimate costs and resources
   - Get approval from stakeholders

2. Setup Phase
   - Create Terraform configuration
   - Set up Ansible playbooks
   - Configure Kubernetes manifests
   - Initialize version control

3. Provisioning Phase
   - Run Terraform plan and apply
   - Execute Ansible configuration
   - Deploy Kubernetes resources
   - Validate infrastructure

4. Testing Phase
   - Run connectivity tests
   - Validate security controls
   - Test application deployment
   - Performance baseline testing

5. Handover Phase
   - Document environment
   - Train operations team
   - Set up monitoring
   - Establish support procedures
```

### Environment Promotion Process
```
Development → Staging:
1. Code review and testing complete
2. Unit tests passing (100%)
3. Integration tests passing
4. Security scan passing
5. Performance tests meeting criteria
6. Manual QA approval
7. Deploy to staging

Staging → Production:
1. All staging tests passing
2. Load testing successful
4. Security audit complete
5. Performance benchmarks met
6. Change advisory board approval
7. Production deployment window scheduled
8. Deploy to production
```

### Environment Maintenance
```
Regular Maintenance Tasks:
- Weekly: Security patching
- Monthly: Dependency updates
- Quarterly: Performance tuning
- Semi-annually: Capacity planning
- Annually: Architecture review

Backup and Recovery:
- Daily automated backups
- Weekly backup verification
- Monthly disaster recovery testing
- Quarterly backup restoration testing
```

---

## Security and Compliance

### Environment Security Controls
```
Development Environment:
- Basic network security groups
- Development-only access
- Test data only
- Basic logging and monitoring

Staging Environment:
- Production-equivalent security
- Limited access team
- Anonymized test data
- Full monitoring stack

Production Environment:
- Full security controls
- Operations-only access
- Real production data
- Comprehensive monitoring

Sandbox Environment:
- Isolated security zone
- Security team access only
- Synthetic security test data
- Security-focused monitoring
```

### Compliance Monitoring
```
Automated Compliance Checks:
- Security group rule validation
- Encryption compliance verification
- Access control configuration
- Logging and monitoring setup
- Backup and recovery procedures

Manual Compliance Reviews:
- Quarterly security assessments
- Annual compliance audits
- Change management reviews
- Incident response testing
```

---

## Monitoring and Observability

### Monitoring Stack by Environment
```
Development:
- Basic application metrics
- System resource monitoring
- Error tracking
- Development-focused dashboards

Staging:
- Production-like monitoring
- Performance metrics
- Security monitoring
- Test result tracking

Production:
- Comprehensive monitoring
- Business metrics
- Security monitoring
- User experience tracking

Sandbox:
- Security monitoring only
- Attack simulation metrics
- Vulnerability scanning results
- Security testing metrics
```

### Alert Configuration
```
Development Environment:
- Critical system failures
- Service unavailable
- Build failures
- Test failures

Staging Environment:
- Performance degradation
- Security anomalies
- Integration failures
- Data validation errors

Production Environment:
- All critical alerts
- Performance issues
- Security incidents
- User experience problems
```

---

## Cost Management

### Resource Optimization
```
Development Environment:
- On-demand instances
- Small resource allocations
- Shared resources where possible
- Cost optimization focus

Staging Environment:
- Reserved instances for baseline
- Medium resource allocations
- Some resource sharing
- Balance of cost and performance

Production Environment:
- Reserved instances
- Large resource allocations
- Dedicated resources
- Performance and reliability focus
```

### Cost Monitoring
```
Monthly Cost Reviews:
- Environment cost comparison
- Resource utilization analysis
- Optimization opportunities
- Budget variance analysis

Cost Optimization Strategies:
- Right-sizing instances
- Scheduling non-critical resources
- Using spot instances for testing
- Implementing auto-scaling
```

---

## Disaster Recovery

### Backup Strategy
```
Development Environment:
- Daily backups
- 7-day retention
- Local storage only
- Fast recovery time

Staging Environment:
- Daily backups
- 30-day retention
- Cross-region replication
- Medium recovery time

Production Environment:
- Hourly backups
- 90-day retention
- Multi-region replication
- Fast recovery time with RPO/RTO targets
```

### Recovery Procedures
```
Recovery Time Objectives (RTO):
- Development: 4 hours
- Staging: 2 hours
- Production: 1 hour

Recovery Point Objectives (RPO):
- Development: 24 hours
- Staging: 4 hours
- Production: 1 hour

Testing Schedule:
- Development: Monthly
- Staging: Quarterly
- Production: Semi-annually
```

This comprehensive multi-environment setup provides a robust foundation for the CBT system development, testing, and deployment lifecycle, ensuring consistency, security, and reliability across all environments while supporting the specific needs of each environment type.
