/// <reference types="vitest" />
import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config'; // Import your main Vite config

export default mergeConfig(
  viteConfig, // Merge with your existing Vite config
  defineConfig({
    test: {
      globals: true, // Use global APIs like describe, it, expect
      environment: 'jsdom', // Use jsdom to simulate browser environment
      setupFiles: './src/setupTests.ts', // Optional: Path to setup file (if needed)
      // You might want to exclude node_modules, dist, etc.
      exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],
      coverage: {
        provider: 'v8', // or 'istanbul'
        reporter: ['text', 'json', 'html'], // Coverage reporters
        // Add directories/files to include in coverage report
        include: ['src/**/*.{ts,tsx}'],
        // Add directories/files to exclude from coverage report
        exclude: [
          'src/main.tsx', // Often exclude entry point
          'src/vite-env.d.ts',
          'src/setupTests.ts', // Exclude test setup file
          'src/**/*.d.ts', // Exclude type definition files
        ],
      },
    },
  })
);