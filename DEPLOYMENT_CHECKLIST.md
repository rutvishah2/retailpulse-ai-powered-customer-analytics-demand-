# RetailPulse - Production Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Quality & Testing
- [ ] All linting checks pass (`flake8 src/`)
- [ ] Unit tests pass (`pytest tests/ -v`)
- [ ] Code coverage ≥ 80%
- [ ] No security vulnerabilities detected
- [ ] All docstrings are complete
- [ ] Type hints are present in all functions

### ✅ Model Performance
- [ ] Demand Forecast MAPE ≤ 12%
- [ ] Churn Prediction AUC-ROC ≥ 0.88
- [ ] Churn Precision@20% ≥ 0.75
- [ ] Customer Segmentation Silhouette Score ≥ 0.35
- [ ] Model inference latency ≤ 100ms
- [ ] Model accuracy stable over last 7 days

### ✅ Data Quality
- [ ] Data validation passes Great Expectations
- [ ] No unexpected missing values
- [ ] Data distribution within expected ranges
- [ ] No data quality alerts from Evidently AI
- [ ] Training data size adequate (≥10K samples)

### ✅ Configuration
- [ ] config.yaml reviewed and finalized
- [ ] .env file properly configured
- [ ] All secrets secured (not in code)
- [ ] Database credentials rotated
- [ ] API keys and tokens generated
- [ ] Logging levels configured correctly

### ✅ Infrastructure
- [ ] Docker image builds successfully
- [ ] Docker image size ≤ 500MB
- [ ] Kubernetes manifests validated
- [ ] Resource limits appropriate
- [ ] Storage volumes configured
- [ ] Network policies defined

### ✅ Database Setup
- [ ] PostgreSQL database created
- [ ] Database schema initialized
- [ ] Backup strategy implemented
- [ ] Replication configured (if multi-node)
- [ ] Performance indexes created
- [ ] Database connection pooling enabled

### ✅ Monitoring & Observability
- [ ] Prometheus scrape configs ready
- [ ] Grafana dashboards created
- [ ] AlertManager rules configured
- [ ] CloudWatch/ELK logging enabled
- [ ] Distributed tracing configured
- [ ] SLA/SLO targets defined

### ✅ Security
- [ ] SSL/TLS certificates installed
- [ ] HTTPS enforced on all endpoints
- [ ] Authentication enabled (OAuth2/JWT)
- [ ] Authorization (RBAC) configured
- [ ] Encryption at rest enabled
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] CORS policy defined

### ✅ Documentation
- [ ] README.md complete and tested
- [ ] API documentation generated
- [ ] Architecture diagram included
- [ ] Deployment runbook written
- [ ] Troubleshooting guide prepared
- [ ] Team trained on new system

### ✅ CI/CD Pipeline
- [ ] GitHub Actions workflows tested
- [ ] Build process automated
- [ ] Tests run automatically
- [ ] Docker build triggered on push
- [ ] Automatic deployment to staging
- [ ] Manual approval for production
- [ ] Rollback procedure documented

---

## Deployment Steps

### Phase 1: Staging Deployment

```bash
# 1. Build Docker image
docker build -t retailpulse:v2.0 .

# 2. Run tests in container
docker run --rm retailpulse:v2.0 pytest tests/

# 3. Deploy to staging K8s cluster
kubectl apply -f k8s/deployment.yaml --namespace=staging

# 4. Run smoke tests
curl http://staging-retailpulse:8501/_stcore/health

# 5. Run integration tests
pytest tests/integration/ --base-url=http://staging-retailpulse:8501
```

### Phase 2: Production Deployment

```bash
# 1. Tag and push image
docker tag retailpulse:v2.0 gcr.io/retailpulse/retailpulse:v2.0
docker push gcr.io/retailpulse/retailpulse:v2.0

# 2. Deploy to production K8s
kubectl apply -f k8s/deployment.yaml --namespace=production

# 3. Monitor rollout
kubectl rollout status deployment/retailpulse-deployment -n production

# 4. Verify all pods running
kubectl get pods -n production

# 5. Run smoke tests against production
curl http://retailpulse-prod:8501/_stcore/health
```

### Phase 3: Post-Deployment Verification

```bash
# 1. Check all services healthy
kubectl get services -n production
kubectl describe pods -n production

# 2. Verify data pipeline
python -c "from train import RetailPulsePipeline; p = RetailPulsePipeline(); print('✅ Pipeline OK')"

# 3. Validate dashboard
curl http://retailpulse-prod:8501/

# 4. Check model endpoints
curl http://retailpulse-prod:8000/health

# 5. Monitor metrics
# Visit: http://grafana:3000/

# 6. Test alerts
# Verify alert manager is receiving metrics
```

---

## Rollback Procedure

### If Issues Detected

```bash
# 1. Immediate rollback to previous version
kubectl rollout undo deployment/retailpulse-deployment -n production

# 2. Verify previous version running
kubectl get pods -n production
kubectl logs -f deployment/retailpulse-deployment -n production

# 3. Investigate issues
# - Check pod logs
# - Review metrics in Grafana
# - Check data quality
# - Review error rates

# 4. Document incident
# - Create post-mortem
# - Identify root cause
# - Plan fixes for next deployment

# 5. Fix and redeploy
# - Fix code issues
# - Update image
# - Run full test suite
# - Deploy to staging first
```

---

## Post-Deployment Monitoring (First 24 Hours)

### Metrics to Watch

| Metric | Threshold | Action |
|--------|-----------|--------|
| Pod Restart Rate | > 2/hour | Investigate pod crashes |
| Error Rate | > 1% | Review error logs |
| Latency (p95) | > 500ms | Check resource usage |
| Memory Usage | > 80% | Scale up replicas |
| CPU Usage | > 70% | Check for bottlenecks |
| Model Accuracy | Drop > 5% | Retrain model |

### Monitoring Commands

```bash
# Pod status
kubectl get pods -w -n production

# Resource usage
kubectl top pods -n production
kubectl top nodes

# Logs
kubectl logs -f deployment/retailpulse-deployment -n production

# Events
kubectl get events -n production --sort-by='.lastTimestamp'

# Describe deployment
kubectl describe deployment retailpulse-deployment -n production
```

---

## Communication Plan

### Before Deployment
- [ ] Notify stakeholders 48 hours in advance
- [ ] Schedule maintenance window
- [ ] Prepare rollback procedure
- [ ] Brief on-call team

### During Deployment
- [ ] Post update in team channel
- [ ] Monitor key metrics every 5 minutes
- [ ] Be ready to rollback
- [ ] Document any issues

### After Deployment
- [ ] Confirm all systems operational
- [ ] Run business validation tests
- [ ] Send completion notification
- [ ] Schedule post-mortem if issues
- [ ] Update deployment log

---

## Sign-Off

- **Deployment Date**: _______________
- **Deployed By**: _______________
- **Approved By**: _______________
- **Status**: [ ] Success [ ] Rollback [ ] Partial

**Notes**:
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## Contacts & Escalation

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Tech Lead | | | |
| DevOps Lead | | | |
| Product Manager | | | |
| On-Call | | | |

---

**Version**: 2.0 | **Last Updated**: March 2026 | **Owner**: Zidio Development
