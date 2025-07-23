#!/usr/bin/env node

/**
 * MCP Platform Wrapper for Filesystem Server
 * 
 * This wrapper extends the official @modelcontextprotocol/server-filesystem
 * with platform-specific configurations, enhanced security, and monitoring.
 */

const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');
const winston = require('winston');

// Configure logging
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    }),
    new winston.transports.File({ 
      filename: '/logs/file-server.log',
      maxsize: 10485760, // 10MB
      maxFiles: 5
    })
  ]
});

class PlatformFileServerWrapper {
  constructor() {
    this.config = this.loadConfiguration();
    this.fsServerProcess = null;
    this.startTime = Date.now();
  }

  loadConfiguration() {
    const config = {
      // Default configuration
      allowedDirs: process.env.MCP_ALLOWED_DIRS?.split(':') || ['/data'],
      readOnly: process.env.MCP_READ_ONLY === 'true',
      maxFileSize: parseInt(process.env.MCP_MAX_FILE_SIZE) || (100 * 1024 * 1024), // 100MB
      enableSymlinks: process.env.MCP_ENABLE_SYMLINKS !== 'false',
      excludePatterns: process.env.MCP_EXCLUDE_PATTERNS?.split(',') || [
        '**/.git/**',
        '**/node_modules/**',
        '**/.env*',
        '**/.*'
      ]
    };

    // Load from config file if it exists
    try {
      const configPath = '/app/config/file-server.json';
      const fileConfig = require(configPath);
      Object.assign(config, fileConfig);
      logger.info('Loaded configuration from file', { configPath });
    } catch (error) {
      logger.debug('No config file found, using environment/defaults');
    }

    return config;
  }

  async validateDirectories() {
    for (const dir of this.config.allowedDirs) {
      try {
        await fs.access(dir);
        const stats = await fs.stat(dir);
        if (!stats.isDirectory()) {
          throw new Error(`${dir} is not a directory`);
        }
        logger.info('Validated directory access', { directory: dir });
      } catch (error) {
        logger.error('Directory validation failed', { 
          directory: dir, 
          error: error.message 
        });
        throw new Error(`Cannot access directory: ${dir}`);
      }
    }
  }

  buildFilesystemServerArgs() {
    const args = [];
    
    // Add allowed directories as roots
    this.config.allowedDirs.forEach(dir => {
      args.push('--root', dir);
    });

    // Add additional configuration
    if (this.config.readOnly) {
      args.push('--read-only');
    }

    if (!this.config.enableSymlinks) {
      args.push('--no-symlinks');
    }

    // Add exclude patterns
    this.config.excludePatterns.forEach(pattern => {
      args.push('--exclude', pattern);
    });

    return args;
  }

  async startFilesystemServer() {
    const args = this.buildFilesystemServerArgs();
    
    logger.info('Starting filesystem server', { 
      args, 
      config: this.config 
    });

    this.fsServerProcess = spawn('npx', [
      '@modelcontextprotocol/server-filesystem',
      ...args
    ], {
      stdio: ['inherit', 'inherit', 'inherit'],
      env: {
        ...process.env,
        NODE_ENV: 'production'
      }
    });

    this.fsServerProcess.on('error', (error) => {
      logger.error('Filesystem server process error', { error: error.message });
      process.exit(1);
    });

    this.fsServerProcess.on('exit', (code, signal) => {
      logger.info('Filesystem server exited', { code, signal });
      if (code !== 0 && code !== null) {
        process.exit(code);
      }
    });

    // Handle graceful shutdown
    process.on('SIGTERM', () => this.shutdown('SIGTERM'));
    process.on('SIGINT', () => this.shutdown('SIGINT'));
  }

  async shutdown(signal) {
    logger.info('Received shutdown signal', { signal });
    
    if (this.fsServerProcess) {
      this.fsServerProcess.kill(signal);
      
      // Wait for process to exit, or force kill after timeout
      const timeout = setTimeout(() => {
        logger.warn('Force killing filesystem server');
        this.fsServerProcess.kill('SIGKILL');
      }, 5000);

      this.fsServerProcess.on('exit', () => {
        clearTimeout(timeout);
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }

  async healthCheck() {
    const uptime = Date.now() - this.startTime;
    const health = {
      status: 'healthy',
      uptime: uptime,
      timestamp: new Date().toISOString(),
      config: {
        allowedDirs: this.config.allowedDirs,
        readOnly: this.config.readOnly,
        enableSymlinks: this.config.enableSymlinks
      },
      process: {
        pid: process.pid,
        memory: process.memoryUsage(),
        cpu: process.cpuUsage()
      }
    };

    // Check if filesystem server process is running
    if (this.fsServerProcess) {
      health.filesystemServer = {
        pid: this.fsServerProcess.pid,
        running: !this.fsServerProcess.killed
      };
    }

    return health;
  }

  async start() {
    try {
      logger.info('Starting MCP Platform File Server Wrapper', { 
        version: require('../package.json').version,
        nodeVersion: process.version
      });

      // Validate configuration and directories
      await this.validateDirectories();

      // Start the filesystem server
      await this.startFilesystemServer();

      logger.info('File server wrapper started successfully');

    } catch (error) {
      logger.error('Failed to start file server wrapper', { 
        error: error.message, 
        stack: error.stack 
      });
      process.exit(1);
    }
  }
}

// Start the wrapper if this file is executed directly
if (require.main === module) {
  const wrapper = new PlatformFileServerWrapper();
  wrapper.start();
}

module.exports = PlatformFileServerWrapper;
