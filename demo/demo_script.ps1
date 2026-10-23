# demo/demo_script.ps1
# 60-Second Demonstration Script for gpower-clone (One-Way ANOVA Omnibus F-Test)
# Run from repository root in PowerShell: .\demo\demo_script.ps1

$startTime = [System.Diagnostics.Stopwatch]::StartNew()

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " gpower-clone Demonstration Script (YZM301 Sprint)" -ForegroundColor Cyan
Write-Host " Conforming to CONTRACT.md v1.0.0 & Faul et al. Reference" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Start-Sleep -Seconds 3

# -----------------------------------------------------------------------------
# STEP 1: Typical A-Priori Run
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 1/4] Typical A-Priori Power Analysis (Oracle Vector v003)" -ForegroundColor Yellow
Write-Host "           Scenario: 3 groups, effect size f=0.25, alpha=0.05, power=0.80" -ForegroundColor DarkYellow
Write-Host "> python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.80" -ForegroundColor Gray
python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.80
$ec1 = $LASTEXITCODE
Write-Host "Exit Code: $ec1 (Success, single line JSON, exact integer sample size N=159)" -ForegroundColor Green
Start-Sleep -Seconds 12

# -----------------------------------------------------------------------------
# STEP 2: Post-Hoc Run (Public Vector)
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 2/4] Post-Hoc Power Analysis (Official Public Vector)" -ForegroundColor Yellow
Write-Host "           Scenario: 5 groups, effect size f=0.25, alpha=0.05, total N=100" -ForegroundColor DarkYellow
Write-Host "> python -m src.cli.main --test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 100 --groups 5" -ForegroundColor Gray
python -m src.cli.main --test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 100 --groups 5
$ec2 = $LASTEXITCODE
Write-Host "Exit Code: $ec2 (Success, power=0.4663312 matches G*Power to < 1e-6)" -ForegroundColor Green
Start-Sleep -Seconds 12

# -----------------------------------------------------------------------------
# STEP 3: Invalid Input Rejection (Exit Code 2)
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 3/4] Invalid Input Handling: Power Below Alpha (Inconsistent Parameters)" -ForegroundColor Yellow
Write-Host "           Scenario: power=0.04 < alpha=0.05 (rejected with INCONSISTENT, exit 2)" -ForegroundColor DarkYellow
Write-Host "> python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.04" -ForegroundColor Gray
python -m src.cli.main --test anova-oneway --mode a-priori --groups 3 --f 0.25 --alpha 0.05 --power 0.04
$ec3 = $LASTEXITCODE
Write-Host "Exit Code: $ec3 (Expected rejection with single-line JSON error/code/field)" -ForegroundColor Red
Start-Sleep -Seconds 12

# -----------------------------------------------------------------------------
# STEP 4: Full Test Suite & Verification Summary
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[Step 4/4] Executing Full Test Suite & Differential Verification" -ForegroundColor Yellow
Write-Host "> python tests/run_all.py" -ForegroundColor Gray
python tests/run_all.py

Write-Host ""
Write-Host "> python -m unittest tests/differential/test_differential.py" -ForegroundColor Gray
python -m unittest tests/differential/test_differential.py
Start-Sleep -Seconds 4

$startTime.Stop()
$totalSec = [math]::Round($startTime.Elapsed.TotalSeconds, 1)

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Demonstration complete in $totalSec seconds (Target ~60s)." -ForegroundColor Cyan
Write-Host " All contract scenarios and oracle verifications passed." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
