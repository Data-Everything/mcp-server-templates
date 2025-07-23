#!/usr/bin/env node

/**
 * Health Check for MCP Platform File Server
 * 
 * This script performs health checks for the containerized file server
 * and can be used by Docker HEALTHCHECK or monitoring systems.
 */

const fs = require('fs').promises;
const path = require('path');

async function performHealthCheck() {
  const healthData = {
    timestamp: new Date().toISOString(),
    status: 'healthy',
    checks: [],
    errors: []
  };

  try {
    // Check 1: Process is responsive
    healthData.checks.push({
      name: 'process_responsive',
      status: 'pass',
      description: 'Health check script executed successfully'
    });

    // Check 2: Required directories exist and are accessible
    const requiredDirs = ['/data', '/logs'];
    for (const dir of requiredDirs) {
      try {
        await fs.access(dir);
        const stats = await fs.stat(dir);
        if (stats.isDirectory()) {
          healthData.checks.push({
            name: `directory_${dir.replace('/', '')}`,
            status: 'pass',
            description: `Directory ${dir} is accessible`
          });
        } else {
          throw new Error(`${dir} is not a directory`);
        }
      } catch (error) {
        healthData.checks.push({
          name: `directory_${dir.replace('/', '')}`,
          status: 'fail',
          description: `Directory ${dir} check failed: ${error.message}`
        });
        healthData.errors.push(`Directory access error: ${error.message}`);
        healthData.status = 'unhealthy';
      }
    }

    // Check 3: Memory usage is reasonable
    const memUsage = process.memoryUsage();
    const memUsageMB = memUsage.rss / 1024 / 1024;
    const memLimit = 512; // MB
    
    if (memUsageMB < memLimit) {
      healthData.checks.push({
        name: 'memory_usage',
        status: 'pass',
        description: `Memory usage ${memUsageMB.toFixed(2)}MB is within limits`
      });
    } else {
      healthData.checks.push({
        name: 'memory_usage',
        status: 'warn',
        description: `Memory usage ${memUsageMB.toFixed(2)}MB exceeds recommended limit`
      });
    }

    // Check 4: Log directory is writable
    try {
      const testFile = '/logs/.health-check';
      await fs.writeFile(testFile, Date.now().toString());
      await fs.unlink(testFile);
      
      healthData.checks.push({
        name: 'log_directory_writable',
        status: 'pass',
        description: 'Log directory is writable'
      });
    } catch (error) {
      healthData.checks.push({
        name: 'log_directory_writable',
        status: 'fail',
        description: `Log directory write test failed: ${error.message}`
      });
      healthData.errors.push(`Log directory write error: ${error.message}`);
      healthData.status = 'unhealthy';
    }

    // Check 5: Configuration is valid
    try {
      const allowedDirs = process.env.MCP_ALLOWED_DIRS?.split(':') || ['/data'];
      let configValid = true;
      
      for (const dir of allowedDirs) {
        try {
          await fs.access(dir);
        } catch {
          configValid = false;
          break;
        }
      }

      if (configValid) {
        healthData.checks.push({
          name: 'configuration_valid',
          status: 'pass',
          description: 'All configured directories are accessible'
        });
      } else {
        healthData.checks.push({
          name: 'configuration_valid',
          status: 'fail',
          description: 'Some configured directories are not accessible'
        });
        healthData.status = 'unhealthy';
      }
    } catch (error) {
      healthData.checks.push({
        name: 'configuration_valid',
        status: 'fail',
        description: `Configuration validation failed: ${error.message}`
      });
      healthData.errors.push(`Configuration error: ${error.message}`);
      healthData.status = 'unhealthy';
    }

  } catch (error) {
    healthData.status = 'unhealthy';
    healthData.errors.push(`Health check failed: ${error.message}`);
  }

  // Output results
  if (process.env.HEALTH_CHECK_VERBOSE === 'true') {
    console.log(JSON.stringify(healthData, null, 2));
  } else {
    console.log(`Status: ${healthData.status}`);
    if (healthData.errors.length > 0) {
      console.log(`Errors: ${healthData.errors.join(', ')}`);
    }
  }

  // Exit with appropriate code
  process.exit(healthData.status === 'healthy' ? 0 : 1);
}

// Run health check if this file is executed directly
if (require.main === module) {
  performHealthCheck().catch(error => {
    console.error('Health check script error:', error.message);
    process.exit(1);
  });
}

module.exports = { performHealthCheck };
