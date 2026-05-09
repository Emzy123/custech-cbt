"""
Security hardening and penetration testing API endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from ..schemas.security import (
    SASTScanRequest, SASTScanResponse, DASTScanRequest, DASTScanResponse,
    PenetrationTestRequest, PenetrationTestResponse, ServerHardeningRequest,
    ServerHardeningResponse, WAFConfigurationRequest, WAFConfigurationResponse,
    SecretsAuditResponse, VulnerabilityReport, VulnerabilityRemediation
)
from ..services.security_hardening_service import SecurityHardeningService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/security", tags=["security-hardening"])


@router.post("/sast/scan", response_model=SASTScanResponse)
@require_permission("security.scan")
async def run_sast_scan(
    scan_request: SASTScanRequest,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> SASTScanResponse:
    """Run Static Application Security Testing (SAST) scan."""
    try:
        security_service = SecurityHardeningService(db)
        
        # Run scan in background for comprehensive scans
        if scan_request.scan_type == "comprehensive":
            background_tasks.add_task(
                security_service.run_sast_scan,
                scan_request.scan_type
            )
            return SASTScanResponse(
                scan_id="pending",
                scan_type="SAST",
                status="pending",
                message="Comprehensive SAST scan started in background"
            )
        else:
            result = await security_service.run_sast_scan(scan_request.scan_type)
            return SASTScanResponse(**result)
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run SAST scan"
        )


@router.post("/dast/scan", response_model=DASTScanResponse)
@require_permission("security.scan")
async def run_dast_scan(
    scan_request: DASTScanRequest,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> DASTScanResponse:
    """Run Dynamic Application Security Testing (DAST) scan."""
    try:
        security_service = SecurityHardeningService(db)
        
        # Run scan in background for comprehensive scans
        if scan_request.scan_type == "comprehensive":
            background_tasks.add_task(
                security_service.run_dast_scan,
                scan_request.target_url,
                scan_request.scan_type
            )
            return DASTScanResponse(
                scan_id="pending",
                scan_type="DAST",
                target_url=scan_request.target_url,
                status="pending",
                message="Comprehensive DAST scan started in background"
            )
        else:
            result = await security_service.run_dast_scan(
                scan_request.target_url, scan_request.scan_type
            )
            return DASTScanResponse(**result)
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run DAST scan"
        )


@router.post("/penetration-test", response_model=PenetrationTestResponse)
@require_permission("security.penetration_test")
async def run_penetration_test(
    test_request: PenetrationTestRequest,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> PenetrationTestResponse:
    """Run comprehensive penetration test."""
    try:
        security_service = SecurityHardeningService(db)
        
        # Always run penetration tests in background due to complexity
        background_tasks.add_task(
            security_service.run_penetration_test,
            test_request.test_scope
        )
        
        return PenetrationTestResponse(
            test_id="pending",
            scan_type="PENETRATION_TEST",
            status="pending",
            message="Penetration test started in background"
        )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run penetration test"
        )


@router.post("/server/harden", response_model=ServerHardeningResponse)
@require_permission("security.harden")
async def harden_server_security(
    hardening_request: ServerHardeningRequest,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ServerHardeningResponse:
    """Apply server security hardening."""
    try:
        security_service = SecurityHardeningService(db)
        
        # Run hardening in background
        background_tasks.add_task(
            security_service.harden_server_security,
            hardening_request.server_config
        )
        
        return ServerHardeningResponse(
            hardening_id="pending",
            scan_type="SERVER_HARDENING",
            status="pending",
            message="Server hardening started in background"
        )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to harden server security"
        )


@router.post("/waf/configure", response_model=WAFConfigurationResponse)
@require_permission("security.configure")
async def configure_waf(
    waf_request: WAFConfigurationRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> WAFConfigurationResponse:
    """Configure Web Application Firewall."""
    try:
        security_service = SecurityHardeningService(db)
        result = await security_service.configure_waf(waf_request.waf_config)
        return WAFConfigurationResponse(**result)
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure WAF"
        )


@router.post("/secrets/audit", response_model=SecretsAuditResponse)
@require_permission("security.audit")
async def audit_secrets_management(
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> SecretsAuditResponse:
    """Audit secrets management."""
    try:
        security_service = SecurityHardeningService(db)
        
        # Run audit in background
        background_tasks.add_task(security_service.audit_secrets_management)
        
        return SecretsAuditResponse(
            audit_id="pending",
            scan_type="SECRETS_AUDIT",
            status="pending",
            message="Secrets audit started in background"
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to audit secrets management"
        )


@router.get("/vulnerabilities/report", response_model=VulnerabilityReport)
@require_permission("security.read")
async def get_vulnerability_report(
    scan_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> VulnerabilityReport:
    """Get comprehensive vulnerability report."""
    try:
        security_service = SecurityHardeningService(db)
        report = await security_service.get_vulnerability_report(
            scan_id, severity, status
        )
        return VulnerabilityReport(**report)
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate vulnerability report"
        )


@router.get("/scans")
@require_permission("security.read")
async def get_security_scans(
    scan_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get list of security scans."""
    try:
        # Build query
        query = select(SecurityScan)
        
        if scan_type:
            query = query.where(SecurityScan.scan_type == scan_type)
        
        if status:
            query = query.where(SecurityScan.status == status)
        
        # Execute query
        result = await self.db.execute(query.order_by(SecurityScan.started_at.desc()).limit(limit))
        scans = result.scalars().all()
        
        return {
            "scans": [
                {
                    "id": scan.id,
                    "scan_type": scan.scan_type,
                    "status": scan.status,
                    "started_at": scan.started_at,
                    "completed_at": scan.completed_at,
                    "vulnerabilities_found": scan.vulnerabilities_found,
                    "error_message": scan.error_message
                }
                for scan in scans
            ],
            "total_scans": len(scans)
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security scans"
        )


@router.get("/scan/{scan_id}")
@require_permission("security.read")
async def get_scan_details(
    scan_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed scan information."""
    try:
        # Get scan
        scan_result = await self.db.execute(
            select(SecurityScan).where(SecurityScan.id == scan_id)
        )
        scan = scan_result.scalar_one_or_none()
        
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found"
            )
        
        # Get vulnerabilities for this scan
        vuln_result = await self.db.execute(
            select(Vulnerability).where(Vulnerability.scan_id == scan_id)
        )
        vulnerabilities = vuln_result.scalars().all()
        
        return {
            "scan": {
                "id": scan.id,
                "scan_type": scan.scan_type,
                "status": scan.status,
                "started_at": scan.started_at,
                "completed_at": scan.completed_at,
                "vulnerabilities_found": scan.vulnerabilities_found,
                "configuration": scan.configuration,
                "results": scan.results,
                "error_message": scan.error_message
            },
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "severity": vuln.severity,
                    "category": vuln.category,
                    "title": vuln.title,
                    "description": vuln.description,
                    "file_path": vuln.file_path,
                    "url": vuln.url,
                    "cwe_id": vuln.cwe_id,
                    "cvss_score": vuln.cvss_score,
                    "remediation": vuln.remediation,
                    "status": vuln.status
                }
                for vuln in vulnerabilities
            ]
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan details"
        )


@router.post("/vulnerability/{vulnerability_id}/remediate")
@require_permission("security.remediate")
async def remediate_vulnerability(
    vulnerability_id: str,
    remediation: VulnerabilityRemediation,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Mark vulnerability as remediated."""
    try:
        # Get vulnerability
        vuln_result = await self.db.execute(
            select(Vulnerability).where(Vulnerability.id == vulnerability_id)
        )
        vulnerability = vuln_result.scalar_one_or_none()
        
        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vulnerability not found"
            )
        
        # Update vulnerability
        vulnerability.status = "remediated"
        vulnerability.remediation_notes = remediation.notes
        vulnerability.remediated_by = current_user.id
        vulnerability.remediated_at = datetime.utcnow()
        
        await self.db.commit()
        
        return {
            "success": True,
            "vulnerability_id": vulnerability_id,
            "status": "remediated",
            "remediated_at": vulnerability.remediated_at
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remediate vulnerability"
        )


@router.post("/vulnerability/{vulnerability_id}/acknowledge")
@require_permission("security.acknowledge")
async def acknowledge_vulnerability(
    vulnerability_id: str,
    notes: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Acknowledge vulnerability (accept risk)."""
    try:
        # Get vulnerability
        vuln_result = await self.db.execute(
            select(Vulnerability).where(Vulnerability.id == vulnerability_id)
        )
        vulnerability = vuln_result.scalar_one_or_none()
        
        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vulnerability not found"
            )
        
        # Update vulnerability
        vulnerability.status = "acknowledged"
        vulnerability.acknowledged_by = current_user.id
        vulnerability.acknowledged_at = datetime.utcnow()
        vulnerability.acknowledgment_notes = notes
        
        await self.db.commit()
        
        return {
            "success": True,
            "vulnerability_id": vulnerability_id,
            "status": "acknowledged",
            "acknowledged_at": vulnerability.acknowledged_at
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge vulnerability"
        )


@router.get("/dashboard")
@require_permission("security.read")
async def get_security_dashboard(
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get security dashboard overview."""
    try:
        # Get recent scans
        recent_scans_result = await self.db.execute(
            select(SecurityScan)
            .order_by(SecurityScan.started_at.desc())
            .limit(10)
        )
        recent_scans = recent_scans_result.scalars().all()
        
        # Get vulnerability statistics
        total_vulns_result = await self.db.execute(
            select(func.count(Vulnerability.id))
        )
        total_vulns = total_vulns_result.scalar() or 0
        
        critical_vulns_result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .where(Vulnerability.severity == "critical")
        )
        critical_vulns = critical_vulns_result.scalar() or 0
        
        high_vulns_result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .where(Vulnerability.severity == "high")
        )
        high_vulns = high_vulns_result.scalar() or 0
        
        open_vulns_result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .where(Vulnerability.status == "open")
        )
        open_vulns = open_vulns_result.scalar() or 0
        
        # Calculate security score
        max_score = total_vulns * 10
        weighted_score = (critical_vulns * 10 + high_vulns * 7)
        security_score = max(0, 100 - (weighted_score / max_score * 100)) if max_score > 0 else 100
        
        return {
            "overview": {
                "total_vulnerabilities": total_vulns,
                "critical_vulnerabilities": critical_vulns,
                "high_vulnerabilities": high_vulns,
                "open_vulnerabilities": open_vulns,
                "security_score": round(security_score, 2)
            },
            "recent_scans": [
                {
                    "id": scan.id,
                    "scan_type": scan.scan_type,
                    "status": scan.status,
                    "started_at": scan.started_at,
                    "vulnerabilities_found": scan.vulnerabilities_found
                }
                for scan in recent_scans
            ],
            "risk_level": "high" if critical_vulns > 0 else "medium" if high_vulns > 0 else "low",
            "last_updated": datetime.utcnow()
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security dashboard"
        )


@router.get("/compliance/check")
@require_permission("security.read")
async def check_compliance(
    standard: str = "owasp",
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Check compliance against security standards."""
    try:
        # Get open vulnerabilities
        open_vulns_result = await self.db.execute(
            select(Vulnerability).where(Vulnerability.status == "open")
        )
        open_vulns = open_vulns_result.scalars().all()
        
        # OWASP Top 10 mapping
        owasp_mapping = {
            "injection": "A01:2021-Broken Access Control",
            "authentication": "A02:2021-Cryptographic Failures",
            "sensitive_data": "A03:2021-Injection",
            "xml_external": "A04:2021-Insecure Design",
            "broken_access": "A05:2021-Security Misconfiguration",
            "security_misconfig": "A06:2021-Vulnerable and Outdated Components",
            "xss": "A07:2021-Identification and Authentication Failures",
            "insecure_deserialization": "A08:2021-Software and Data Integrity Failures",
            "components": "A09:2021-Security Logging and Monitoring Failures",
            "logging": "A10:2021-Server-Side Request Forgery"
        }
        
        compliance_results = {}
        for category, owasp_category in owasp_mapping.items():
            category_vulns = [v for v in open_vulns if v.category == category]
            compliance_results[owasp_category] = {
                "vulnerabilities": len(category_vulns),
                "compliant": len(category_vulns) == 0,
                "risk_level": "high" if any(v.severity in ["critical", "high"] for v in category_vulns) else "medium" if category_vulns else "low"
            }
        
        # Calculate overall compliance score
        compliant_categories = sum(1 for result in compliance_results.values() if result["compliant"])
        total_categories = len(compliance_results)
        compliance_score = (compliant_categories / total_categories * 100) if total_categories > 0 else 0
        
        return {
            "standard": standard.upper(),
            "compliance_score": round(compliance_score, 2),
            "compliant_categories": compliant_categories,
            "total_categories": total_categories,
            "results": compliance_results,
            "recommendations": [
                "Address all critical and high vulnerabilities",
                "Implement regular security scanning",
                "Establish vulnerability management process",
                "Conduct security training for developers"
            ],
            "checked_at": datetime.utcnow()
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check compliance"
        )


@router.post("/remediation/sprint")
@require_permission("security.manage")
async def create_remediation_sprint(
    sprint_data: Dict[str, Any],
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create vulnerability remediation sprint."""
    try:
        # Get vulnerabilities to include in sprint
        vulnerability_ids = sprint_data.get("vulnerability_ids", [])
        
        if not vulnerability_ids:
            raise ValueError("No vulnerabilities specified for sprint")
        
        # Get vulnerabilities
        vulns_result = await self.db.execute(
            select(Vulnerability).where(Vulnerability.id.in_(vulnerability_ids))
        )
        vulnerabilities = vulns_result.scalars().all()
        
        # Create sprint record (simplified - in production would have proper Sprint model)
        sprint_id = str(uuid.uuid4())
        sprint_data = {
            "id": sprint_id,
            "name": sprint_data.get("name", "Security Remediation Sprint"),
            "description": sprint_data.get("description", ""),
            "vulnerability_ids": vulnerability_ids,
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "target_completion": sprint_data.get("target_completion"),
            "status": "active"
        }
        
        # Store sprint in cache
        cache_key = f"remediation_sprint:{sprint_id}"
        await self.cache.set(cache_key, sprint_data, ttl=86400 * 30)  # 30 days
        
        return {
            "sprint_id": sprint_id,
            "name": sprint_data["name"],
            "vulnerabilities_included": len(vulnerabilities),
            "created_at": sprint_data["created_at"],
            "status": "active"
        }
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create remediation sprint"
        )
